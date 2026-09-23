"""Private project files, stored in SQLite and always downloaded as attachments."""

import hashlib
from datetime import timezone
import re
import unicodedata
from urllib.parse import quote, unquote
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from . import main as core
from .models import Member, ProjectAttachment, now
from .projects import get_project

router = APIRouter(prefix="/api/projects")
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PROJECT_BYTES = 100 * 1024 * 1024
MAX_PROJECT_FILES = 30


def limits():
    return {
        "file_bytes": MAX_FILE_BYTES,
        "project_bytes": MAX_PROJECT_BYTES,
        "project_files": MAX_PROJECT_FILES,
    }


def attachment_data(db, a):
    return {
        "id": a.id,
        "filename": a.filename,
        "size_bytes": a.size_bytes,
        "created_at": a.created_at.astimezone(timezone.utc).isoformat(),
        "uploaded_by": core.member_name(db, a.uploaded_by_id),
        "download_url": f"/api/projects/{a.project_id}/attachments/{a.id}/download",
    }


def attachment_list(db, member, pid):
    return [
        attachment_data(db, a)
        for a in db.scalars(
            select(ProjectAttachment)
            .where(
                ProjectAttachment.company_id == member.company_id,
                ProjectAttachment.project_id == pid,
            )
            .order_by(ProjectAttachment.created_at.desc(), ProjectAttachment.id.desc())
        )
    ]


def safe_filename(encoded):
    if len(encoded) > 2400 or re.search(r"%(?![0-9a-fA-F]{2})", encoded):
        raise HTTPException(422, "ファイル名を確認してください。")
    try:
        name = unicodedata.normalize("NFC", unquote(encoded, errors="strict"))
    except UnicodeError:
        raise HTTPException(422, "ファイル名を確認してください。")
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(c for c in name if unicodedata.category(c) not in ("Cc", "Cf"))
    name = re.sub(r'[<>:"|?*]', "_", name).strip().rstrip(". ")
    if not name or len(name) > 200:
        raise HTTPException(422, "ファイル名は1〜200文字にしてください。")
    return name


@router.get("/{pid}/attachments")
def list_files(pid: int, db: Session = core.Db, member: Member = core.Auth):
    get_project(db, member, pid)
    return {"items": attachment_list(db, member, pid), "limits": limits()}


def save_attachment(db, member, pid, upload_id, filename, content):
    # Serialize quota checks, retries and deletions per project. Read the HTTP body
    # before acquiring this lock so a slow upload cannot lock the project.
    project = get_project(db, member, pid, True)
    digest = hashlib.sha256(content).hexdigest()
    previous = db.scalar(
        select(ProjectAttachment).where(
            ProjectAttachment.company_id == member.company_id,
            ProjectAttachment.project_id == pid,
            ProjectAttachment.upload_id == str(upload_id),
        )
    )
    if previous:
        if previous.sha256 != digest or previous.filename != filename:
            raise HTTPException(
                409, "同じアップロード番号で異なるファイルは保存できません。"
            )
        return attachment_data(db, previous)
    count, total = db.execute(
        select(
            func.count(ProjectAttachment.id),
            func.coalesce(func.sum(ProjectAttachment.size_bytes), 0),
        ).where(
            ProjectAttachment.company_id == member.company_id,
            ProjectAttachment.project_id == pid,
        )
    ).one()
    if count >= MAX_PROJECT_FILES:
        raise HTTPException(
            409, f"1案件に添付できるファイルは{MAX_PROJECT_FILES}件までです。"
        )
    if total + len(content) > MAX_PROJECT_BYTES:
        raise HTTPException(
            409, "案件の添付容量が上限を超えます。不要なファイルを整理してください。"
        )
    a = ProjectAttachment(
        company_id=member.company_id,
        project_id=pid,
        upload_id=str(upload_id),
        filename=filename,
        size_bytes=len(content),
        sha256=digest,
        content=content,
        uploaded_by_id=member.id,
    )
    db.add(a)
    project.updated_at = now()
    db.flush()
    core.audit(
        db,
        member,
        "案件にファイルを添付",
        detail=f"案件 #{pid} / 添付 #{a.id}: {filename} ({len(content)} bytes)",
    )
    return attachment_data(db, a)


@router.put("/{pid}/attachments/{upload_id}")
async def upload_file(
    pid: int,
    upload_id: UUID,
    request: Request,
    x_file_name: str = Header(max_length=2400),
    db: Session = core.Db,
    member: Member = core.Auth,
):
    project = await run_in_threadpool(get_project, db, member, pid)
    if not core.can_edit(member, project):
        raise HTTPException(403, "案件の担当者または対象範囲の管理者のみ添付できます。")
    filename = safe_filename(x_file_name)
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            size = int(declared)
        except ValueError:
            raise HTTPException(400, "ファイルサイズが不正です。")
        if size < 0:
            raise HTTPException(400, "ファイルサイズが不正です。")
        if size > MAX_FILE_BYTES:
            raise HTTPException(413, "1ファイルは10MBまで添付できます。")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_FILE_BYTES:
            raise HTTPException(413, "1ファイルは10MBまで添付できます。")
        content.extend(chunk)
    if not content:
        raise HTTPException(422, "空のファイルは添付できません。")
    return await run_in_threadpool(
        save_attachment, db, member, pid, upload_id, filename, bytes(content)
    )


def get_attachment(db, member, pid, aid, write=False):
    project = get_project(db, member, pid, write)
    a = core.scoped(db, ProjectAttachment, aid, member)
    if a.project_id != pid:
        raise HTTPException(404, "添付ファイルが見つかりません。")
    return project, a


@router.get("/{pid}/attachments/{aid}/download")
def download_file(
    pid: int, aid: int, db: Session = core.Db, member: Member = core.Auth
):
    _, a = get_attachment(db, member, pid, aid)
    return Response(
        a.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(a.filename, safe='')}",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.delete("/{pid}/attachments/{aid}")
def delete_file(pid: int, aid: int, db: Session = core.Db, member: Member = core.Auth):
    project, a = get_attachment(db, member, pid, aid, True)
    core.audit(
        db,
        member,
        "案件の添付ファイルを削除",
        detail=f"案件 #{pid} / 添付 #{a.id}: {a.filename}",
    )
    db.delete(a)
    project.updated_at = now()
    return {"ok": True}
