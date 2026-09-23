from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import base64

from PIL import Image, ImageDraw
from pypdf import PdfReader
import pytest


def quote(c, seal_id=None, items=None):
    body = {
        "title": "受注・請求の検証",
        "customer_id": c.get("/api/customers").json()[0]["id"],
        "valid_until": str(date.today() + timedelta(days=30)),
        "seal_id": seal_id,
        "items": items
        or [{"name": "制作費", "quantity": "1", "unit_price": "12345", "tax_rate": 10}],
    }
    r = c.post("/api/quotes", json=body)
    assert r.status_code == 201, r.text
    return r.json(), body


def action(c, q, verb):
    return c.post(
        f"/api/revisions/{q['revision_id']}/{verb}",
        json={"lock_version": q["lock_version"]},
    )


def order(c, q):
    r = c.post(
        "/api/orders",
        json={"revision_id": q["revision_id"], "ordered_on": str(date.today())},
    )
    assert r.status_code == 201, r.text
    return r.json()


def invoice(c, o):
    body = {
        "issue_on": str(date.today() - timedelta(days=2)),
        "transaction_on": str(date.today() - timedelta(days=2)),
        "due_on": str(date.today() - timedelta(days=1)),
        "bank_details": "テスト銀行 本店 普通 1234567\nテスト名義",
        "registration_number": "T1234567890123",
    }
    r = c.post(f"/api/orders/{o['id']}/invoices", json=body)
    assert r.status_code == 201, r.text
    return r.json(), body


def inv_action(c, i, verb, comment=""):
    return c.post(
        f"/api/invoices/{i['id']}/{verb}",
        json={"lock_version": i["lock_version"], "comment": comment},
    )


def stamp(c, color="red"):
    im = Image.new("RGBA", (120, 120), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((5, 5, 114, 114), outline=color, width=4)
    d.text((30, 50), "TEST", fill=color)
    out = BytesIO()
    im.save(out, format="PNG")
    r = c.post(
        "/api/seals", json={"image_base64": base64.b64encode(out.getvalue()).decode()}
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_seal_tenant_permissions_validation_and_snapshot(clients):
    c, outsider = clients("solo"), clients("staff")
    sid = stamp(c)
    assert outsider.get(f"/api/seals/{sid}").status_code == 404
    assert outsider.post("/api/seals", json={"image_base64": "bad"}).status_code == 403
    assert c.post("/api/seals", json={"image_base64": "bad"}).status_code == 422
    q, body = quote(c, sid)
    assert (
        outsider.post(
            "/api/quotes",
            json={
                **body,
                "customer_id": outsider.get("/api/customers").json()[0]["id"],
            },
        ).status_code
        == 404
    )
    issued = action(c, q, "issue").json()
    pdf = c.get(f"/api/revisions/{q['revision_id']}/pdf").content
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages[0].images) >= 1
    new_id = stamp(c, "blue")
    assert new_id != sid
    assert c.delete("/api/seals/current").status_code == 200
    assert c.get(f"/api/revisions/{q['revision_id']}/pdf").content == pdf
    assert c.get(f"/api/seals/{sid}").status_code == 200
    assert c.post("/api/quotes", json=body).status_code == 409
    duplicate = action(c, issued, "duplicate").json()
    assert duplicate["payload"]["seal_id"] is None
    out = Path("output/pdf")
    out.mkdir(parents=True, exist_ok=True)
    (out / "qa-quote-seal.pdf").write_bytes(pdf)


def test_seal_cannot_bypass_approval_and_pending_snapshot(clients):
    admin, staff, manager, director = (
        clients(u) for u in ["admin", "staff", "manager", "director"]
    )
    sid = stamp(admin)
    q, body = quote(staff, sid)
    q = action(staff, q, "submit").json()
    assert action(staff, q, "issue").status_code == 409
    sid2 = stamp(admin, "blue")
    assert (
        staff.put(
            f"/api/revisions/{q['revision_id']}",
            json={**body, "seal_id": sid2, "lock_version": q["lock_version"]},
        ).status_code
        == 409
    )
    q = action(manager, q, "approve").json()
    q = action(director, q, "approve").json()
    assert q["payload"]["seal_id"] == sid
    q = action(staff, q, "issue").json()
    assert q["status"] == "issued"
    assert q["approvals"][0]["steps"][0]["approver_name"]


def test_order_requires_issued_revision_and_freezes_agreed_version(clients):
    c = clients("solo")
    q, body = quote(c)
    ob = {"revision_id": q["revision_id"], "ordered_on": str(date.today())}
    assert c.post("/api/orders", json=ob).status_code == 409
    assert (
        c.put(
            f"/api/quotes/{q['id']}/sales",
            json={
                "sales_status": "sent",
                "sent_on": str(date.today()),
                "lock_version": q["sales_version"],
            },
        ).status_code
        == 409
    )
    q = action(c, q, "issue").json()
    assert (
        c.put(
            f"/api/quotes/{q['id']}/sales",
            json={
                "sales_status": "sent",
                "sent_on": str(date.today()),
                "lock_version": q["sales_version"],
            },
        ).status_code
        == 200
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: c.post("/api/orders", json=ob), range(2)))
    assert all(r.status_code == 201 for r in results)
    o = results[0].json()
    assert results[1].json()["id"] == o["id"]
    revised = action(c, q, "revise").json()
    body["items"][0]["unit_price"] = "99999"
    c.put(
        f"/api/revisions/{revised['revision_id']}",
        json={**body, "lock_version": revised["lock_version"]},
    )
    stored = c.get(f"/api/orders/{o['id']}").json()
    assert stored["total"] == q["total"] and stored["revision_id"] == q["revision_id"]
    assert c.get(f"/api/revisions/{q['revision_id']}").json()["sales_status"] == "won"


def test_invoice_full_payment_correction_void_reissue_and_pdf(clients):
    c = clients("solo")
    sid = stamp(c)
    q, _ = quote(
        c,
        sid,
        [
            {"name": "制作費", "quantity": "1", "unit_price": "10000", "tax_rate": 10},
            {
                "name": "食品サンプル",
                "quantity": "2",
                "unit_price": "100",
                "tax_rate": 8,
            },
        ],
    )
    q = action(c, q, "issue").json()
    o = order(c, q)
    inv, body = invoice(c, o)
    assert invoice(c, o)[0]["id"] == inv["id"]
    inv = inv_action(c, inv, "issue").json()
    assert inv["overdue"] and inv["status"] == "issued"
    pdf = c.get(f"/api/invoices/{inv['id']}/pdf").content
    text = "".join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
    for fragment in [
        "御請求書",
        "T1234567890123",
        "取引年月日",
        "10%対象",
        "8%対象",
        "軽減税率",
        "テスト銀行",
    ]:
        assert fragment in text
    assert (
        c.put(
            f"/api/invoices/{inv['id']}",
            json={**body, "lock_version": inv["lock_version"]},
        ).status_code
        == 409
    )
    data = {
        "lock_version": inv["lock_version"],
        "paid_on": str(date.today()),
        "note": "銀行明細で確認",
    }
    r = c.post(f"/api/invoices/{inv['id']}/payment", json=data)
    assert r.status_code == 200, r.text
    paid = r.json()
    assert paid["status"] == "paid" and not paid["overdue"]
    assert c.post(f"/api/invoices/{inv['id']}/payment", json=data).status_code == 409
    assert inv_action(c, paid, "void", "取消").status_code == 409
    unpaid = inv_action(c, paid, "unpay", "別の振込と取り違え").json()
    assert unpaid["status"] == "issued" and unpaid["paid_on"] is None
    void = inv_action(c, unpaid, "void", "請求日の修正").json()
    assert void["status"] == "void"
    assert c.get(f"/api/invoices/{inv['id']}/pdf").content == pdf
    new, _ = invoice(c, o)
    new = inv_action(c, new, "issue").json()
    assert new["id"] != inv["id"] and new["number"] != inv["number"]
    logs = c.get(f"/api/revisions/{q['revision_id']}").json()["history"]
    assert any("取り違え" in log["detail"] for log in logs)
    Path("output/pdf/qa-invoice-seal.pdf").write_bytes(pdf)


def test_business_company_scope_and_org_permissions(clients):
    c, other = clients("solo"), clients("staff")
    q, _ = quote(c)
    q = action(c, q, "issue").json()
    o = order(c, q)
    inv, _ = invoice(c, o)
    for path in [
        f"/api/orders/{o['id']}",
        f"/api/invoices/{inv['id']}",
        f"/api/invoices/{inv['id']}/pdf",
    ]:
        assert other.get(path).status_code == 404
    assert inv_action(other, inv, "issue").status_code == 404
    assert not any(i["id"] == inv["id"] for i in other.get("/api/invoices").json())
    assert not any(x["id"] == o["id"] for x in other.get("/api/orders").json())
    # A member in another section cannot see a director-owned order.
    director = clients("director")
    from backend.app.db import SessionLocal
    from backend.app.models import Revision

    q, _ = quote(director)
    with SessionLocal.begin() as db:
        rev = db.get(Revision, q["revision_id"])
        rev.status = "issued"  # Fixture only: permissions independent of the approval test above.
    o = order(director, q)
    assert clients("sales").get(f"/api/orders/{o['id']}").status_code == 404
    assert other.get(f"/api/orders/{o['id']}").status_code == 200
    assert (
        other.put(
            f"/api/orders/{o['id']}",
            json={
                "ordered_on": str(date.today()),
                "status": "completed",
                "lock_version": o["lock_version"],
            },
        ).status_code
        == 403
    )


def test_invoice_concurrency_rollback_and_order_cancellation(clients, monkeypatch):
    c = clients("solo")
    q, _ = quote(c)
    q = action(c, q, "issue").json()
    o = order(c, q)
    inv, body = invoice(c, o)
    from backend.app import main

    original = main.generate_pdf

    def fail(*args, **kwargs):
        raise RuntimeError("PDF unavailable")

    monkeypatch.setattr(main, "generate_pdf", fail)
    with pytest.raises(RuntimeError):
        inv_action(c, inv, "issue")
    inv = c.get(f"/api/invoices/{inv['id']}").json()
    assert inv["status"] == "draft" and inv["number"] is None
    monkeypatch.setattr(main, "generate_pdf", original)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: inv_action(c, inv, "issue"), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert results[0].json()["number"] == results[1].json()["number"]
    issued = results[0].json()
    update = {
        "ordered_on": str(date.today()),
        "status": "cancelled",
        "note": "先方都合",
        "lock_version": o["lock_version"],
    }
    assert c.put(f"/api/orders/{o['id']}", json=update).status_code == 409
    assert inv_action(c, issued, "void", "先方都合").status_code == 200
    cancelled = c.put(f"/api/orders/{o['id']}", json=update)
    assert cancelled.status_code == 200
    assert c.post(f"/api/orders/{o['id']}/invoices", json=body).status_code == 409
    assert (
        c.put(
            f"/api/orders/{o['id']}", json={**update, "status": "received"}
        ).status_code
        == 409
    )


def test_invoice_dates_and_database_source_revision_constraints(clients):
    from sqlalchemy.exc import IntegrityError
    from backend.app.db import SessionLocal
    from backend.app.models import Order

    c = clients("solo")
    q, _ = quote(c)
    q = action(c, q, "issue").json()
    o = order(c, q)
    inv, body = invoice(c, o)
    assert (
        c.put(
            f"/api/invoices/{inv['id']}",
            json={**body, "due_on": "2000-01-01", "lock_version": inv["lock_version"]},
        ).status_code
        == 422
    )
    assert (
        c.put(
            f"/api/invoices/{inv['id']}",
            json={
                **body,
                "registration_number": "T123",
                "lock_version": inv["lock_version"],
            },
        ).status_code
        == 422
    )
    inv = inv_action(c, inv, "issue").json()
    assert (
        c.post(
            f"/api/invoices/{inv['id']}/payment",
            json={
                "lock_version": inv["lock_version"],
                "paid_on": str(date.today() + timedelta(days=1)),
            },
        ).status_code
        == 422
    )
    q2, _ = quote(c)
    with SessionLocal() as db:
        original = db.get(Order, o["id"])
        db.add(
            Order(
                company_id=original.company_id,
                quote_id=q2["id"],
                revision_id=q["revision_id"],
                ordered_on=date.today(),
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
