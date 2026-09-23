from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from uuid import uuid4

from fastapi.testclient import TestClient


def project(client):
    response = client.post(
        "/api/projects",
        json={
            "title": "添付ファイルのテスト案件",
            "customer_id": client.get("/api/customers").json()[0]["id"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def upload(client, pid, content=b"hello", filename="資料.txt", token=None, **kwargs):
    return client.put(
        f"/api/projects/{pid}/attachments/{token or uuid4()}",
        content=content,
        headers={
            "X-File-Name": quote(filename),
            "Content-Type": "application/octet-stream",
            **kwargs.pop("headers", {}),
        },
        **kwargs,
    )


def test_multiple_files_roundtrip_and_safe_download(clients):
    c = clients("solo")
    pid = project(c)
    contents = [
        "日本語の相談メモ".encode(),
        b"\x00\xff\x01test",
        b"<script>alert(1)</script>",
    ]
    saved = []
    for body, name in zip(contents, ["相談メモ.txt", "構成.zip", "sample.html"]):
        result = upload(c, pid, body, name)
        assert result.status_code == 200, result.text
        row = result.json()
        assert row["size_bytes"] == len(body) and row["filename"] == name
        assert row["uploaded_by"] and row["created_at"]
        assert "content" not in row and "sha256" not in row
        saved.append(row)
        download = c.get(row["download_url"])
        assert download.content == body
        assert download.headers["content-type"] == "application/octet-stream"
        assert download.headers["content-disposition"].startswith("attachment;")
        assert quote(name) in download.headers["content-disposition"]
        assert download.headers["x-content-type-options"] == "nosniff"
        assert download.headers["content-security-policy"] == "sandbox"
        assert download.headers["cache-control"] == "no-store"
    files = c.get(f"/api/projects/{pid}/attachments").json()
    assert [a["id"] for a in files["items"]] == [a["id"] for a in reversed(saved)]
    assert files["limits"]["file_bytes"] == 10 * 1024 * 1024
    assert c.get(f"/api/projects/{pid}").json()["attachments"] == files["items"]


def test_files_follow_project_tenant_org_and_edit_permissions(clients):
    staff, admin = clients("staff"), clients("admin")
    pid = project(staff)
    saved = upload(staff, pid).json()
    base = f"/api/projects/{pid}/attachments"
    for user in ("solo", "sales"):
        c = clients(user)
        assert c.get(base).status_code == 404
        assert c.get(saved["download_url"]).status_code == 404
        assert upload(c, pid).status_code == 404
        assert c.delete(f"{base}/{saved['id']}").status_code == 404
    for user in ("manager", "director", "admin"):
        assert clients(user).get(saved["download_url"]).status_code == 200
    username = "attachment_peer_" + uuid4().hex[:8]
    result = admin.post(
        "/api/members",
        json={
            "username": username,
            "display_name": "同じ課の閲覧担当",
            "password": "demo1234",
            "section_id": staff.get("/api/bootstrap").json()["me"]["section_id"],
        },
    )
    assert result.status_code == 201
    peer = clients(username)
    assert peer.get(base).status_code == 200
    assert peer.get(saved["download_url"]).status_code == 200
    assert upload(peer, pid).status_code == 403
    assert peer.delete(f"{base}/{saved['id']}").status_code == 403
    other_pid = project(staff)
    assert (
        staff.get(
            f"/api/projects/{other_pid}/attachments/{saved['id']}/download"
        ).status_code
        == 404
    )
    assert (
        staff.delete(f"/api/projects/{other_pid}/attachments/{saved['id']}").status_code
        == 404
    )
    assert upload(clients("manager"), pid).status_code == 200


def test_retry_is_idempotent_but_same_filename_is_not_overwritten(clients):
    c = clients("solo")
    pid = project(c)
    token = uuid4()
    first = upload(c, pid, token=token).json()
    assert upload(c, pid, token=token).json() == first
    assert upload(c, pid, b"different", token=token).status_code == 409
    assert upload(c, pid, filename="another.txt", token=token).status_code == 409
    second = upload(c, pid, b"second version").json()
    assert first["filename"] == second["filename"] and first["id"] != second["id"]
    assert c.get(first["download_url"]).content == b"hello"
    assert c.get(second["download_url"]).content == b"second version"
    # Attaching a file must not invalidate an open project-edit form.
    assert c.get(f"/api/projects/{pid}").json()["lock_version"] == 1


def test_byte_limits_and_empty_stream_rollback(clients, monkeypatch):
    from backend.app import attachments

    monkeypatch.setattr(attachments, "MAX_FILE_BYTES", 8)
    monkeypatch.setattr(attachments, "MAX_PROJECT_BYTES", 10)
    c = clients("solo")
    pid = project(c)
    assert upload(c, pid, b"").status_code == 422
    assert upload(c, pid, b"a" * 9).status_code == 413
    # No Content-Length: enforce actual received bytes as well as declared size.
    assert upload(c, pid, iter([b"1234", b"5678", b"9"])).status_code == 413
    assert upload(c, pid, b"12345678").status_code == 200
    assert upload(c, pid, b"123").status_code == 409
    assert upload(c, pid, b"12").status_code == 200
    items = c.get(f"/api/projects/{pid}/attachments").json()["items"]
    assert len(items) == 2 and sum(a["size_bytes"] for a in items) == 10


def test_concurrent_quota_and_retry(clients, monkeypatch):
    from backend.app import attachments

    monkeypatch.setattr(attachments, "MAX_PROJECT_FILES", 2)
    c = clients("solo")
    pid = project(c)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: upload(c, pid), range(3)))
    assert sorted(r.status_code for r in results) == [200, 200, 409]
    assert len(c.get(f"/api/projects/{pid}/attachments").json()["items"]) == 2
    pid = project(c)
    token = uuid4()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: upload(c, pid, token=token), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert results[0].json()["id"] == results[1].json()["id"]
    assert len(c.get(f"/api/projects/{pid}/attachments").json()["items"]) == 1


def test_delete_frees_capacity_and_is_audited(clients, monkeypatch):
    from backend.app import attachments

    monkeypatch.setattr(attachments, "MAX_PROJECT_FILES", 1)
    c = clients("solo")
    pid = project(c)
    a = upload(c, pid).json()
    assert upload(c, pid).status_code == 409
    path = f"/api/projects/{pid}/attachments/{a['id']}"
    assert c.delete(path).status_code == 200
    assert c.get(a["download_url"]).status_code == 404
    assert c.delete(path).status_code == 404
    assert upload(c, pid).status_code == 200
    from backend.app.db import SessionLocal
    from backend.app.models import Audit
    from sqlalchemy import select

    with SessionLocal() as db:
        actions = list(
            db.scalars(
                select(Audit.action).where(Audit.detail.like(f"案件 #{pid} / 添付 #%"))
            )
        )
        assert actions.count("案件にファイルを添付") == 2
        assert actions.count("案件の添付ファイルを削除") == 1


def test_filename_normalization_auth_and_csrf(clients):
    from backend.app.main import app

    c = clients("solo")
    pid = project(c)
    a = upload(c, pid, filename='../../仕様\r\n書".txt').json()
    assert a["filename"] == "仕様書_.txt"
    assert upload(c, pid, filename="..").status_code == 422
    assert upload(c, pid, filename="x" * 201).status_code == 422
    assert upload(c, pid, headers={"X-File-Name": "%FF"}).status_code == 422
    assert upload(c, pid, headers={"X-File-Name": "%broken"}).status_code == 422
    assert upload(c, pid, headers={"Origin": "https://example.org"}).status_code == 403
    with TestClient(app) as anonymous:
        assert anonymous.get(a["download_url"]).status_code == 401
        assert anonymous.get(f"/api/projects/{pid}/attachments").status_code == 401
        assert upload(anonymous, pid).status_code == 401


def test_attachment_foreign_keys_reject_cross_company(clients):
    from backend.app.db import SessionLocal
    from backend.app.models import ProjectAttachment
    from sqlalchemy.exc import IntegrityError
    import pytest

    staff = clients("staff")
    pid = project(staff)
    solo = clients("solo").get("/api/bootstrap").json()
    with SessionLocal() as db:
        db.add(
            ProjectAttachment(
                company_id=solo["company"]["id"],
                project_id=pid,
                upload_id=str(uuid4()),
                filename="x",
                size_bytes=1,
                sha256="0" * 64,
                content=b"x",
                uploaded_by_id=solo["me"]["id"],
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
