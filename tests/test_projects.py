from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import json
import re
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError


def project(c, title="予約システム開発"):
    body = {
        "title": title,
        "customer_id": c.get("/api/customers").json()[0]["id"],
        "purpose": "予約受付を効率化する",
    }
    response = c.post("/api/projects", json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def requirement(c, p, scope="included"):
    body = {
        "title": "予約を登録できる",
        "description": "空き枠から予約する",
        "acceptance": "満席の枠は選択できない",
        "scope": scope,
    }
    response = c.post(f"/api/projects/{p['id']}/requests", json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def estimate(c, p, r):
    body = {
        "title": "予約機能開発",
        "customer_id": p["customer_id"],
        "project_id": p["id"],
        "request_refs": [{"request_id": r["id"], "version": r["lock_version"]}],
        "valid_until": str(date.today() + timedelta(days=30)),
        "items": [
            {
                "name": "予約機能",
                "quantity": "1",
                "unit_price": "100000",
                "tax_rate": 10,
            }
        ],
    }
    response = c.post("/api/quotes", json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def test_project_tenant_org_and_owner_permissions(clients):
    staff, admin = clients("staff"), clients("admin")
    p, pb = project(staff)
    r, rb = requirement(staff, p)
    path = f"/api/projects/{p['id']}"
    for username in ("sales", "solo"):
        other = clients(username)
        assert other.get(path).status_code == 404
        assert other.get(f"{path}/requests/{r['id']}/history").status_code == 404
        assert other.put(path, json={**pb, "lock_version": 1}).status_code == 404
        assert not any(x["id"] == p["id"] for x in other.get("/api/projects").json())
    for username in ("manager", "director", "admin"):
        assert clients(username).get(path).status_code == 200
    boot = staff.get("/api/bootstrap").json()
    username = "peer_" + uuid4().hex[:10]
    result = admin.post(
        "/api/members",
        json={
            "username": username,
            "display_name": "同じ課の担当者",
            "password": "demo1234",
            "section_id": boot["me"]["section_id"],
        },
    )
    assert result.status_code == 201, result.text
    peer = clients(username)
    assert peer.get(path).status_code == 200
    assert (
        peer.put(
            f"{path}/requests/{r['id']}", json={**rb, "lock_version": r["lock_version"]}
        ).status_code
        == 403
    )
    q, qb = estimate(admin, p, r)
    assert q["owner_name"] == boot["me"]["name"]
    assert q["section_id"] == boot["me"]["section_id"]
    assert staff.get(f"/api/revisions/{q['revision_id']}").json()["editable"]
    assert peer.post("/api/quotes", json=qb).status_code == 403
    assert clients("sales").get(f"/api/revisions/{q['revision_id']}").status_code == 404


def test_agreement_change_history_and_optimistic_lock(clients):
    c = clients("solo")
    p, _ = project(c)
    r, body = requirement(c, p)
    url = f"/api/projects/{p['id']}/requests/{r['id']}"
    assert (
        c.put(url, json={**body, "status": "done", "lock_version": 1}).status_code
        == 422
    )
    assert c.post(url + "/agree", json={"lock_version": 1}).status_code == 422
    response = c.post(
        url + "/agree", json={"lock_version": 1, "comment": "田中様とメールで確認"}
    )
    assert response.status_code == 200, response.text
    agreed = response.json()
    assert agreed["status"] == "agreed" and agreed["agreement"]["content_version"] == 1
    assert (
        c.put(
            url, json={**body, "title": "予約を変更できる", "lock_version": 2}
        ).status_code
        == 422
    )
    response = c.put(url, json={**body, "status": "in_progress", "lock_version": 2})
    assert response.status_code == 200, response.text
    assert response.json()["agreement"] == agreed["agreement"]
    response = c.put(
        url,
        json={
            **body,
            "description": "変更にも対応",
            "status": "in_progress",
            "change_note": "顧客からの追加要望",
            "lock_version": 3,
        },
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["agreement"] is None and updated["status"] == "consulting"
    assert c.put(url, json={**body, "lock_version": 3}).status_code == 409
    history = c.get(url + "/history").json()
    assert [h["version"] for h in history] == [4, 3, 2, 1]
    assert history[2]["payload"]["agreement"] == agreed["agreement"]
    assert history[-1]["payload"]["description"] == body["description"]


def test_requirement_snapshot_revision_duplicate_and_pdf_immutable(clients):
    c = clients("solo")
    p, _ = project(c)
    r, rb = requirement(c, p)
    q, qb = estimate(c, p, r)
    rid = q["revision_id"]
    first_snapshot = q["payload"]["request_snapshots"]
    assert (
        c.put(
            f"/api/projects/{p['id']}/requests/{r['id']}",
            json={**rb, "description": "全く別の新しい要望", "lock_version": 1},
        ).status_code
        == 200
    )
    saved = c.put(
        f"/api/revisions/{rid}",
        json={**qb, "title": "金額以外を更新", "lock_version": q["lock_version"]},
    ).json()
    assert saved["payload"]["request_snapshots"] == first_snapshot
    issued = c.post(
        f"/api/revisions/{rid}/issue", json={"lock_version": saved["lock_version"]}
    ).json()
    assert issued["status"] == "issued"
    pdf = c.get(f"/api/revisions/{rid}/pdf").content
    revised = c.post(
        f"/api/revisions/{rid}/revise", json={"lock_version": issued["lock_version"]}
    ).json()
    assert revised["payload"]["request_snapshots"] == first_snapshot
    response = c.put(
        f"/api/revisions/{revised['revision_id']}",
        json={
            **qb,
            "request_refs": [{"request_id": r["id"], "version": 2}],
            "lock_version": revised["lock_version"],
        },
    )
    assert response.status_code == 200, response.text
    current = response.json()
    assert (
        current["payload"]["request_snapshots"][0]["description"]
        == "全く別の新しい要望"
    )
    assert (
        c.get(f"/api/revisions/{rid}").json()["payload"]["request_snapshots"]
        == first_snapshot
    )
    assert c.get(f"/api/revisions/{rid}/pdf").content == pdf
    duplicate = c.post(
        f"/api/revisions/{current['revision_id']}/duplicate",
        json={"lock_version": current["lock_version"]},
    ).json()
    assert (
        duplicate["project_id"] is None
        and duplicate["payload"]["request_snapshots"] == []
    )


def test_cross_project_refs_customer_changes_and_invalid_inputs(clients):
    c = clients("solo")
    p, pb = project(c)
    other, _ = project(c)
    r, _ = requirement(c, p)
    other_r, _ = requirement(c, other)
    excluded, _ = requirement(c, p, "excluded")
    q, qb = estimate(c, p, r)
    for refs in (
        [{"request_id": other_r["id"], "version": 1}],
        [{"request_id": excluded["id"], "version": 1}],
        [{"request_id": r["id"], "version": 999}],
        qb["request_refs"] * 2,
    ):
        assert (
            c.post("/api/quotes", json={**qb, "request_refs": refs}).status_code == 422
        )
    foreign_p, _ = project(clients("staff"))
    foreign_r, _ = requirement(clients("staff"), foreign_p)
    assert (
        c.post(
            "/api/quotes",
            json={
                **qb,
                "request_refs": [{"request_id": foreign_r["id"], "version": 1}],
            },
        ).status_code
        == 404
    )
    assert (
        c.post("/api/quotes", json={**qb, "project_id": foreign_p["id"]}).status_code
        == 404
    )
    assert c.post("/api/quotes", json={**qb, "project_id": None}).status_code == 422
    assert (
        c.put(
            f"/api/revisions/{q['revision_id']}",
            json={**qb, "project_id": other["id"], "lock_version": q["lock_version"]},
        ).status_code
        == 409
    )
    customer = c.post("/api/customers", json={"name": "別のお客様"}).json()
    assert (
        c.post("/api/quotes", json={**qb, "customer_id": customer["id"]}).status_code
        == 422
    )
    current = c.get(f"/api/projects/{p['id']}").json()
    assert (
        c.put(
            f"/api/projects/{p['id']}",
            json={
                **pb,
                "customer_id": customer["id"],
                "lock_version": current["lock_version"],
            },
        ).status_code
        == 409
    )
    assert (
        c.post(
            "/api/projects", json={**pb, "external_url": "javascript:alert(1)"}
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/projects",
            json={**pb, "external_url": "https://user:pass@example.com"},
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/projects", json={**pb, "customer_id": foreign_p["customer_id"]}
        ).status_code
        == 404
    )


def test_concurrent_requirement_updates_and_company_foreign_keys(clients):
    c = clients("solo")
    p, pb = project(c)
    r, rb = requirement(c, p)
    url = f"/api/projects/{p['id']}/requests/{r['id']}"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda title: (
                    c.put(
                        url, json={**rb, "title": title, "lock_version": 1}
                    ).status_code
                ),
                ["変更A", "変更B"],
            )
        )
    assert sorted(results) == [200, 409]
    assert len(c.get(url + "/history").json()) == 2
    current = c.get(f"/api/projects/{p['id']}").json()
    assert (
        c.put(f"/api/projects/{p['id']}", json={**pb, "lock_version": 1}).status_code
        == 409
    )
    assert (
        c.put(
            f"/api/projects/{p['id']}",
            json={**pb, "lock_version": current["lock_version"]},
        ).status_code
        == 200
    )
    from backend.app.db import SessionLocal
    from backend.app.models import Quote

    foreign, _ = project(clients("staff"))
    q, _ = estimate(c, p, r)
    with pytest.raises(IntegrityError), SessionLocal.begin() as db:
        db.get(Quote, q["id"]).project_id = foreign["id"]
        db.flush()


def test_project_aggregate_multiple_estimates_orders_and_invoices(clients):
    from test_commerce import order, invoice, inv_action

    c = clients("solo")
    p, _ = project(c)
    r, _ = requirement(c, p)
    for _ in range(2):
        q, _ = estimate(c, p, r)
        q = c.post(
            f"/api/revisions/{q['revision_id']}/issue",
            json={"lock_version": q["lock_version"]},
        ).json()
        o = order(c, q)
        i, _ = invoice(c, o)
        i = inv_action(c, i, "issue").json()
    data = c.get(f"/api/projects/{p['id']}").json()
    assert len(data["quotes"]) == len(data["orders"]) == len(data["invoices"]) == 2
    assert data["ordered_total"] == data["unpaid_total"] == "220000"
    assert (
        c.post(
            f"/api/invoices/{i['id']}/payment",
            json={"lock_version": i["lock_version"], "paid_on": str(date.today())},
        ).status_code
        == 200
    )
    assert c.get(f"/api/projects/{p['id']}").json()["unpaid_total"] == "110000"


def test_assigned_approver_does_not_gain_project_access(clients):
    from test_workflows import settings

    admin, owner, approver = clients("admin"), clients("sales"), clients("staff")
    old = settings(admin)
    config = {
        **old,
        "approval_mode": "sequential",
        "route": [
            {
                "name": "担当レビュー",
                "approver_id": approver.get("/api/bootstrap").json()["me"]["id"],
            }
        ],
    }
    assert admin.put("/api/settings", json=config).status_code == 200
    try:
        p, _ = project(owner)
        r, _ = requirement(owner, p)
        q, _ = estimate(owner, p, r)
        response = owner.post(
            f"/api/revisions/{q['revision_id']}/submit",
            json={"lock_version": q["lock_version"]},
        )
        assert response.status_code == 200, response.text
        assert approver.get(f"/api/revisions/{q['revision_id']}").status_code == 200
        assert approver.get(f"/api/projects/{p['id']}").status_code == 404
        assert (
            approver.get(
                f"/api/projects/{p['id']}/requests/{r['id']}/history"
            ).status_code
            == 404
        )
    finally:
        old["route_version"] = settings(admin)["route_version"]
        assert admin.put("/api/settings", json=old).status_code == 200


def test_manual_index_and_relative_article_links():
    root = Path(__file__).resolve().parents[1] / "docs/manual/ja"
    entries = json.loads((root / "index.json").read_text(encoding="utf-8"))["items"]
    assert len(entries) == 10 and len({x["id"] for x in entries}) == 10
    paths = {x["path"] for x in entries}
    for entry in entries:
        content = (root / entry["path"]).read_text(encoding="utf-8")
        assert content.startswith("# " + entry["title"])
        for link in re.findall(r"\]\(([^)]+\.md)\)", content):
            assert link in paths


def test_manual_download_uses_auth_and_allowlist(clients):
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as anonymous:
        assert anonymous.get("/api/manual/requests/download").status_code == 401
    c = clients("solo")
    response = c.get("/api/manual/requests/download")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="03-requests.md"'
    )
    assert "text/markdown" in response.headers["content-type"]
    source = Path(__file__).resolve().parents[1] / "docs/manual/ja/03-requests.md"
    assert response.content == source.read_bytes()
    assert c.get("/api/manual/unknown/download").status_code == 404
    assert c.get("/api/manual/.env/download").status_code == 404
