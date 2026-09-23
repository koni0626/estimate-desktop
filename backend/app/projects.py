"""Projects, versioned requirements, and immutable estimate scope snapshots."""

import copy
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import main as core
from .models import (
    Customer,
    Member,
    Order,
    Project,
    Quote,
    Requirement,
    RequirementHistory,
    now,
)
from .schemas import Action, ProjectInput, RequirementInput

router = APIRouter(prefix="/api")
Db, Auth = core.Db, core.Auth
FIELDS = (
    "title",
    "description",
    "acceptance",
    "questions",
    "priority",
    "scope",
    "status",
)
CONTENT_FIELDS = ("title", "description", "acceptance", "scope")


def get_project(db, member, pid, write=False):
    project = core.scoped(db, Project, pid, member)
    if not core.normal_scope(member, project):
        raise HTTPException(404, "案件が見つかりません。")
    if write:
        if not core.can_edit(member, project):
            raise HTTPException(
                403, "案件の担当者または対象範囲の管理者のみ変更できます。"
            )
        db.execute(
            select(Project.id).where(Project.id == project.id)
        ).first()
        db.refresh(project)
    return project


def requirement_data(r):
    return {
        "id": r.id,
        "project_id": r.project_id,
        **{key: getattr(r, key) for key in FIELDS},
        "agreement": r.agreement,
        "lock_version": r.lock_version,
        "updated_at": r.updated_at.isoformat(),
    }


def remember(db, member, r, note):
    db.add(
        RequirementHistory(
            company_id=member.company_id,
            requirement_id=r.id,
            version=r.lock_version,
            actor_id=member.id,
            payload=copy.deepcopy(requirement_data(r)),
            note=note[:1000],
        )
    )
    core.audit(
        db,
        member,
        "案件の要望を記録",
        detail=f"案件 #{r.project_id} / 要望 #{r.id} v{r.lock_version}: {note}",
    )
    db.flush()


def project_data(db, member, p):
    requirements = db.scalars(
        select(Requirement).where(
            Requirement.project_id == p.id, Requirement.company_id == member.company_id
        )
    ).all()
    return {
        "id": p.id,
        "title": p.title,
        "customer_id": p.customer_id,
        "customer_name": db.get(Customer, p.customer_id).name,
        "customer_contact": p.customer_contact,
        "customer_corporate_number": p.customer_corporate_number,
        "purpose": p.purpose,
        "status": p.status,
        "due_on": p.due_on,
        "external_url": p.external_url,
        "owner_name": core.member_name(db, p.owner_id),
        "lock_version": p.lock_version,
        "updated_at": p.updated_at,
        "editable": core.can_edit(member, p),
        "request_count": len(requirements),
        "unresolved_count": sum(
            r.scope == "undecided" or bool(r.questions) for r in requirements
        ),
    }


@router.get("/projects")
def projects(db: Session = Db, member: Member = Auth):
    return [
        project_data(db, member, p)
        for p in db.scalars(
            select(Project)
            .where(Project.company_id == member.company_id)
            .order_by(Project.updated_at.desc(), Project.id.desc())
        )
        if core.normal_scope(member, p)
    ]


@router.post("/projects", status_code=201)
def create_project(body: ProjectInput, db: Session = Db, member: Member = Auth):
    core.scoped(db, Customer, body.customer_id, member)
    p = Project(
        company_id=member.company_id,
        owner_id=member.id,
        department_id=member.department_id,
        section_id=member.section_id,
        **body.model_dump(exclude={"lock_version"}),
    )
    db.add(p)
    db.flush()
    core.audit(db, member, "案件を作成", detail=f"案件 #{p.id}: {p.title}")
    return project_data(db, member, p)


@router.put("/projects/{pid}")
def update_project(
    pid: int, body: ProjectInput, db: Session = Db, member: Member = Auth
):
    p = get_project(db, member, pid, True)
    core.check_version(p, body.lock_version)
    core.scoped(db, Customer, body.customer_id, member)
    if body.customer_id != p.customer_id and db.scalar(
        select(Quote.id).where(Quote.project_id == p.id).limit(1)
    ):
        raise HTTPException(
            409, "見積がある案件の取引先は変更できません。別の案件を作成してください。"
        )
    for key, value in body.model_dump(exclude={"lock_version"}).items():
        setattr(p, key, value)
    core.touch(p)
    core.audit(db, member, "案件を更新", detail=f"案件 #{p.id}: {p.title}")
    db.flush()
    return project_data(db, member, p)


@router.get("/projects/{pid}")
def project_detail(pid: int, db: Session = Db, member: Member = Auth):
    p = get_project(db, member, pid)
    qs = db.scalars(
        select(Quote)
        .where(Quote.project_id == p.id, Quote.company_id == member.company_id)
        .order_by(Quote.id.desc())
    ).all()
    from .commerce import order_data
    from .attachments import attachment_list, limits

    orders = [
        order_data(db, member, o, q)
        for q in qs
        if core.normal_scope(member, q)
        for o in db.scalars(
            select(Order).where(
                Order.quote_id == q.id, Order.company_id == member.company_id
            )
        )
    ]
    return {
        **project_data(db, member, p),
        "attachments": attachment_list(db, member, pid),
        "attachment_limits": limits(),
        "requests": [
            requirement_data(r)
            for r in db.scalars(
                select(Requirement)
                .where(
                    Requirement.project_id == p.id,
                    Requirement.company_id == member.company_id,
                )
                .order_by(Requirement.id)
            )
        ],
        "quotes": [
            core.summary(db, q, core.latest(db, q.id))
            for q in qs
            if core.normal_scope(member, q)
        ],
        "orders": orders,
        "invoices": [i for o in orders for i in o["invoices"]],
        "ordered_total": str(
            sum(int(o["total"]) for o in orders if o["status"] != "cancelled")
        ),
        "unpaid_total": str(
            sum(
                int(i["total"])
                for o in orders
                for i in o["invoices"]
                if i["status"] == "issued"
            )
        ),
    }


@router.post("/projects/{pid}/requests", status_code=201)
def create_requirement(
    pid: int, body: RequirementInput, db: Session = Db, member: Member = Auth
):
    p = get_project(db, member, pid, True)
    if body.status not in ("consulting", "estimated"):
        raise HTTPException(422, "要望登録後に合意を記録してください。")
    r = Requirement(
        company_id=member.company_id,
        project_id=p.id,
        **body.model_dump(exclude={"lock_version", "change_note"}),
    )
    db.add(r)
    db.flush()
    remember(db, member, r, body.change_note or "要望を登録")
    core.touch(p)
    return requirement_data(r)


def get_requirement(db, member, pid, rid, write=False):
    p = get_project(db, member, pid, write)
    r = core.scoped(db, Requirement, rid, member)
    if r.project_id != p.id:
        raise HTTPException(404, "要望が見つかりません。")
    return p, r


@router.put("/projects/{pid}/requests/{rid}")
def update_requirement(
    pid: int, rid: int, body: RequirementInput, db: Session = Db, member: Member = Auth
):
    p, r = get_requirement(db, member, pid, rid, True)
    core.check_version(r, body.lock_version)
    changed = any(getattr(r, key) != getattr(body, key) for key in CONTENT_FIELDS)
    if changed and r.agreement and not body.change_note:
        raise HTTPException(422, "合意した内容を変更する理由を入力してください。")
    if not r.agreement and body.status not in ("consulting", "estimated"):
        raise HTTPException(422, "先に顧客との合意を記録してください。")
    for key in FIELDS:
        setattr(r, key, getattr(body, key))
    if changed and r.agreement:
        r.agreement = None
        r.status = "consulting"
    core.touch(r)
    core.touch(p)
    remember(db, member, r, body.change_note or "要望を更新")
    return requirement_data(r)


@router.post("/projects/{pid}/requests/{rid}/agree")
def agree_requirement(
    pid: int, rid: int, body: Action, db: Session = Db, member: Member = Auth
):
    p, r = get_requirement(db, member, pid, rid, True)
    core.check_version(r, body.lock_version)
    if (
        not body.comment
        or not r.acceptance
        or r.scope not in ("included", "additional")
    ):
        raise HTTPException(
            422, "対象範囲・完了条件を設定し、合意相手や確認方法を入力してください。"
        )
    r.agreement = {
        "content_version": r.lock_version,
        "recorded_at": now().isoformat(),
        "recorded_by": core.member_name(db, member.id),
        "note": body.comment,
    }
    r.status = "agreed"
    core.touch(r)
    core.touch(p)
    remember(db, member, r, "合意を記録: " + body.comment)
    return requirement_data(r)


@router.get("/projects/{pid}/requests/{rid}/history")
def requirement_history(pid: int, rid: int, db: Session = Db, member: Member = Auth):
    get_requirement(db, member, pid, rid)
    return [
        {
            "version": h.version,
            "payload": h.payload,
            "note": h.note,
            "actor_name": core.member_name(db, h.actor_id),
            "created_at": h.created_at,
        }
        for h in db.scalars(
            select(RequirementHistory)
            .where(
                RequirementHistory.company_id == member.company_id,
                RequirementHistory.requirement_id == rid,
            )
            .order_by(RequirementHistory.version.desc())
        )
    ]


def quote_scope(db, member, body):
    if body.project_id is None:
        if body.request_refs:
            raise HTTPException(422, "要望の紐付けには案件を指定してください。")
        return None, []
    p = get_project(db, member, body.project_id, True)
    if body.customer_id != p.customer_id:
        raise HTTPException(422, "案件と見積の取引先を一致させてください。")
    if len({r.request_id for r in body.request_refs}) != len(body.request_refs):
        raise HTTPException(422, "同じ要望を重複して選択できません。")
    snapshots = []
    for ref in body.request_refs:
        r = core.scoped(db, Requirement, ref.request_id, member)
        h = db.scalar(
            select(RequirementHistory).where(
                RequirementHistory.company_id == member.company_id,
                RequirementHistory.requirement_id == r.id,
                RequirementHistory.version == ref.version,
            )
        )
        if r.project_id != p.id or h is None:
            raise HTTPException(422, "案件内の要望と保存済みの版を指定してください。")
        if h.payload["scope"] not in ("included", "additional"):
            raise HTTPException(
                422,
                "見積には「今回の対象」または「追加見積」の要望を選択してください。",
            )
        snapshots.append(copy.deepcopy(h.payload))
    return p, snapshots
