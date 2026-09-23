from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import pytest
from pypdf import PdfReader
from sqlalchemy.exc import IntegrityError


def new_quote(client, title="検証用見積", items=None):
    customer = client.get("/api/customers").json()[0]
    body = {
        "title": title,
        "customer_id": customer["id"],
        "valid_until": (date.today() + timedelta(days=30)).isoformat(),
        "items": items
        or [
            {
                "name": "デザイン制作",
                "quantity": "1",
                "unit": "式",
                "unit_price": "10000",
                "tax_rate": 10,
            }
        ],
    }
    response = client.post("/api/quotes", json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def act(client, q, action, comment=""):
    return client.post(
        f"/api/revisions/{q['revision_id']}/{action}",
        json={"lock_version": q["lock_version"], "comment": comment},
    )


def settings(client):
    data = client.get("/api/bootstrap").json()["company"]
    data.pop("id")
    return data


def test_authentication_and_csrf(clients):
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as c:
        assert c.get("/api/quotes").status_code == 401
        assert (
            c.post(
                "/api/auth/login", json={"username": "solo", "password": "wrong"}
            ).status_code
            == 401
        )
        r = c.post("/api/auth/login", json={"username": "solo", "password": "demo1234"})
        assert "HttpOnly" in r.headers["set-cookie"]
        assert (
            c.post(
                "/api/quotes", headers={"Origin": "https://untrusted.example"}, json={}
            ).status_code
            == 403
        )
        assert c.post("/api/auth/logout").status_code == 200
        assert c.get("/api/bootstrap").status_code == 401


def test_tenant_isolation_and_cross_tenant_references(clients):
    solo, staff = clients("solo"), clients("staff")
    q, body = new_quote(solo)
    rid = q["revision_id"]
    assert staff.get(f"/api/revisions/{rid}").status_code == 404
    assert staff.get(f"/api/revisions/{rid}/pdf").status_code == 404
    assert (
        staff.put(
            f"/api/revisions/{rid}", json={**body, "lock_version": q["lock_version"]}
        ).status_code
        == 404
    )
    assert act(staff, q, "issue").status_code == 404
    assert staff.post("/api/quotes", json=body).status_code == 404
    assert (
        staff.put(
            f"/api/customers/{body['customer_id']}", json={"name": "不正変更"}
        ).status_code
        == 404
    )
    assert staff.put("/api/settings", json=settings(solo)).status_code == 403
    assert q["id"] not in [x["id"] for x in staff.get("/api/quotes").json()]


def test_department_and_section_scope(clients):
    sales, staff, director = clients("sales"), clients("staff"), clients("director")
    q, _ = new_quote(sales, "営業課だけの見積")
    assert staff.get(f"/api/revisions/{q['revision_id']}").status_code == 404
    assert director.get(f"/api/revisions/{q['revision_id']}").status_code == 200
    assert q["id"] in [x["id"] for x in director.get("/api/quotes").json()]


def test_decimal_pdf_immutability_and_revision(clients):
    c = clients("solo")
    items = [
        {
            "name": "小数の明細",
            "quantity": "1.5",
            "unit": "時間",
            "unit_price": "100.50",
            "tax_rate": 10,
        },
        {
            "name": "軽減税率の明細",
            "quantity": "2",
            "unit": "個",
            "unit_price": "125",
            "tax_rate": 8,
        },
    ]
    q, body = new_quote(c, items=items)
    assert q["payload"]["subtotal"] == "401"
    assert q["payload"]["tax"] == "35"
    q = act(c, q, "issue").json()
    assert q["status"] == "issued"
    original = c.get(f"/api/revisions/{q['revision_id']}/pdf").content
    reader = PdfReader(BytesIO(original))
    assert "小数の明細" in "".join(p.extract_text() for p in reader.pages)
    assert (
        c.put(
            f"/api/revisions/{q['revision_id']}",
            json={**body, "lock_version": q["lock_version"]},
        ).status_code
        == 409
    )
    s = settings(c)
    old_name = s["name"]
    s["name"] = "変更後の会社情報"
    assert c.put("/api/settings", json=s).status_code == 200
    assert c.get(f"/api/revisions/{q['revision_id']}/pdf").content == original
    s = settings(c)
    s["name"] = old_name
    c.put("/api/settings", json=s)
    revised = act(c, q, "revise").json()
    assert revised["version"] == 2 and revised["status"] == "draft"
    assert revised["number"] == q["number"]
    assert c.get(f"/api/revisions/{q['revision_id']}/pdf").content == original


def test_multistep_approval_order_and_issue(clients):
    staff, manager, director = clients("staff"), clients("manager"), clients("director")
    q, _ = new_quote(staff)
    q = act(staff, q, "submit").json()
    assert act(staff, q, "issue").status_code == 409
    assert act(director, q, "approve").status_code == 403
    assert act(staff, q, "approve").status_code == 403
    q = act(manager, q, "approve").json()
    assert (
        q["status"] == "pending"
        and q["approvals"][0]["steps"][1]["status"] == "pending"
    )
    assert act(staff, q, "issue").status_code == 409
    q = act(director, q, "approve").json()
    assert q["status"] == "approved"
    issued = act(staff, q, "issue")
    assert issued.status_code == 200 and issued.json()["status"] == "issued"


def test_return_resubmission_snapshot_and_optimistic_lock(clients):
    staff, manager, director = clients("staff"), clients("manager"), clients("director")
    q, body = new_quote(staff)
    old = q.copy()
    q = act(staff, q, "submit").json()
    assert (
        staff.put(
            f"/api/revisions/{q['revision_id']}",
            json={**body, "lock_version": q["lock_version"]},
        ).status_code
        == 409
    )
    assert act(staff, old, "submit").status_code == 409
    q = act(manager, q, "approve").json()
    assert act(director, q, "return").status_code == 422
    q = act(director, q, "return", "金額を再確認してください").json()
    updated = staff.put(
        f"/api/revisions/{q['revision_id']}",
        json={**body, "title": "修正後の見積", "lock_version": q["lock_version"]},
    )
    assert updated.status_code == 200
    q = act(staff, updated.json(), "submit").json()
    assert len(q["approvals"]) == 2
    assert q["approvals"][0]["steps"][0]["status"] == "pending"
    assert q["approvals"][0]["steps"][1]["status"] == "waiting"
    assert q["approvals"][1]["steps"][1]["comment"] == "金額を再確認してください"


def test_route_changes_do_not_mutate_pending_and_three_steps(clients):
    admin, staff = clients("admin"), clients("staff")
    original = settings(admin)
    try:
        q, _ = new_quote(staff)
        q = act(staff, q, "submit").json()
        s = settings(admin)
        mid = admin.get("/api/bootstrap").json()["me"]["id"]
        s["route"].append({"name": "代表確認", "approver_id": mid, "backup_id": None})
        assert admin.put("/api/settings", json=s).status_code == 200
        assert (
            len(
                staff.get(f"/api/revisions/{q['revision_id']}").json()["approvals"][0][
                    "steps"
                ]
            )
            == 2
        )
        new, _ = new_quote(staff)
        new = act(staff, new, "submit").json()
        assert len(new["approvals"][0]["steps"]) == 3
        for who in ("manager", "director", "admin"):
            r = act(clients(who), new, "approve")
            assert r.status_code == 200, r.text
            new = r.json()
        assert new["status"] == "approved"
        assert act(staff, new, "issue").status_code == 200
    finally:
        original["route_version"] = settings(admin)["route_version"]
        admin.put("/api/settings", json=original)


def test_self_approval_backup_and_mode_switch(clients):
    manager, admin, solo = clients("manager"), clients("admin"), clients("solo")
    q, _ = new_quote(manager)
    q = act(manager, q, "submit").json()
    assert (
        q["approvals"][0]["steps"][0]["approver_id"]
        == admin.get("/api/bootstrap").json()["me"]["id"]
    )
    original = settings(solo)
    try:
        old, _ = new_quote(solo)
        s = settings(solo)
        s["approval_mode"] = "sequential"
        s["route"] = [
            {
                "name": "確認",
                "approver_id": solo.get("/api/bootstrap").json()["me"]["id"],
                "backup_id": None,
            }
        ]
        assert solo.put("/api/settings", json=s).status_code == 200
        assert act(solo, old, "issue").status_code == 409
        assert act(solo, old, "submit").status_code == 422
    finally:
        original["route_version"] = settings(solo)["route_version"]
        solo.put("/api/settings", json=original)


def test_concurrent_issue_is_idempotent(clients):
    from fastapi.testclient import TestClient
    from backend.app.main import app

    solo = clients("solo")
    q, _ = new_quote(solo)
    token = solo.cookies.get("estimate2_session")

    def send():
        with TestClient(app) as c:
            c.cookies.set("estimate2_session", token)
            response = act(c, q, "issue")
            assert response.status_code == 200, response.text
            return response.json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: send(), range(2)))
    assert results[0]["number"] == results[1]["number"]
    assert results[0]["revision_id"] == results[1]["revision_id"]
    assert results[0]["status"] == results[1]["status"] == "issued"


def test_pdf_failure_does_not_issue_or_consume_number(clients, monkeypatch):
    from backend.app import main

    solo = clients("solo")
    q, _ = new_quote(solo)

    def fail(*args, **kwargs):
        raise RuntimeError("PDF generation failed for test")

    monkeypatch.setattr(main, "generate_pdf", fail)
    with pytest.raises(RuntimeError):
        act(solo, q, "issue")
    restored = solo.get(f"/api/revisions/{q['revision_id']}").json()
    assert restored["status"] == "draft" and restored["number"] is None


def test_database_cross_company_foreign_key_and_disabled_session(clients):
    from backend.app.db import SessionLocal
    from backend.app.models import Member, Quote

    solo = clients("solo")
    team = clients("staff")
    solo_data = solo.get("/api/bootstrap").json()
    team_data = team.get("/api/bootstrap").json()
    with SessionLocal() as db:
        bad = Quote(
            company_id=solo_data["company"]["id"],
            creator_id=team_data["me"]["id"],
            owner_id=solo_data["me"]["id"],
        )
        db.add(bad)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
    with SessionLocal.begin() as db:
        member = db.get(Member, team_data["me"]["id"])
        member.active = False
    try:
        assert team.get("/api/bootstrap").status_code == 401
    finally:
        with SessionLocal.begin() as db:
            db.get(Member, team_data["me"]["id"]).active = True


def test_multipage_japanese_pdf_and_embedded_font(clients):
    import fitz

    c = clients("solo")
    items = [
        {
            "name": f"{i + 1:02d} 日本語の長い品名を含むデザイン制作・原稿確認・レイアウト調整作業",
            "quantity": "1.5",
            "unit": "時間",
            "unit_price": "1234.50",
            "tax_rate": 10,
        }
        for i in range(65)
    ]
    q, _ = new_quote(c, "日本語・複数ページ検証", items)
    response = c.get(f"/api/revisions/{q['revision_id']}/pdf")
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) >= 3
    text = "".join(p.extract_text() for p in reader.pages)
    assert "65 日本語" in text and "下書き" in text and "お支払条件" in text
    embedded = False
    for f in reader.pages[0]["/Resources"]["/Font"].values():
        font = f.get_object()
        descriptor = font.get("/FontDescriptor")
        if descriptor and "/FontFile2" in descriptor.get_object():
            embedded = True
    assert embedded
    out = Path("output/pdf")
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample-multipage.pdf").write_bytes(response.content)
    doc = fitz.open(stream=response.content, filetype="pdf")
    for i in [0, len(doc) - 1]:
        doc[i].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(
            str(out / f"qa-page-{i + 1}.png")
        )
