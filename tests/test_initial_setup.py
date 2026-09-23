"""The owner can claim an empty local installation exactly once."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker

from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app.models import Company, Member, User
from backend.app.security import hash_password


@pytest.fixture
def empty_installation(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'empty.sqlite3'}",
        connect_args={"timeout": 30, "check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def sqlite_settings(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")

    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)

    def isolated_db(request: Request):
        with sessions() as db:
            try:
                if request.method not in ("GET", "HEAD", "OPTIONS"):
                    db.execute(text("BEGIN IMMEDIATE"))
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = isolated_db
    yield sessions
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def owner_data(username="owner"):
    return {
        "company_name": "私のデザイン事務所",
        "display_name": "山田 花子",
        "username": username,
        "password": "a-long-private-password",
    }


def test_first_admin_can_setup_and_login(empty_installation):
    with TestClient(app) as client:
        assert client.get("/api/setup/status").json() == {
            "required": True,
            "demo_available": False,
        }
        assert client.post("/api/setup", json={**owner_data(), "password": "short"}).status_code == 422
        created = client.post("/api/setup", json=owner_data())
        assert created.status_code == 201
        assert created.json() == {"ok": True}
        assert client.get("/api/setup/status").json()["required"] is False
        boot = client.get("/api/bootstrap")
        assert boot.status_code == 200
        assert boot.json()["me"]["role"] == "admin"
        assert boot.json()["company"]["name"] == "私のデザイン事務所"
        assert client.post("/api/setup", json=owner_data("other")).status_code == 409

        client.post("/api/auth/logout")
        assert client.post("/api/auth/login", json={
            "username": "owner", "password": "a-long-private-password"
        }).status_code == 200

    with empty_installation() as db:
        assert len(db.scalars(select(Company)).all()) == 1
        assert len(db.scalars(select(User)).all()) == 1
        assert len(db.scalars(select(Member)).all()) == 1


def test_parallel_setup_allows_only_one_admin(empty_installation):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda name: TestClient(app).post("/api/setup", json=owner_data(name)).status_code,
            ["first", "second"],
        ))
    assert sorted(results) == [201, 409]
    with empty_installation() as db:
        assert len(db.scalars(select(Company)).all()) == 1
        assert len(db.scalars(select(User)).all()) == 1


def test_cross_site_cannot_claim_empty_installation(empty_installation):
    with TestClient(app) as client:
        response = client.post(
            "/api/setup", json=owner_data(), headers={"Origin": "https://example.test"}
        )
        assert response.status_code == 403
        assert client.get("/api/setup/status").json()["required"] is True


def test_desktop_first_run_needs_no_username_or_password(empty_installation, monkeypatch):
    monkeypatch.setenv("ESTIMATE2_DESKTOP_TOKEN", "unpredictable-test-launch-token")
    monkeypatch.setenv("ESTIMATE2_DESKTOP_ORIGIN", "http://127.0.0.1:54321")
    with TestClient(app) as client:
        assert client.get("/api/desktop/launch?token=wrong").status_code == 404
        assert client.post("/api/desktop/setup", json={
            "company_name": "個人事務所", "display_name": "山田 花子"
        }).status_code == 403
        assert client.get("/api/desktop/launch?token=unpredictable-test-launch-token").status_code == 200
        assert client.get("/api/setup/status").json() == {
            "required": True, "demo_available": False, "desktop_mode": True
        }
        created = client.post("/api/desktop/setup", json={
            "company_name": "個人事務所", "display_name": "山田 花子"
        }, headers={"Origin": "http://127.0.0.1:54321"})
        assert created.status_code == 201
        assert client.get("/api/bootstrap").json()["me"]["name"] == "山田 花子"
        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/desktop/resume", json={}).status_code == 200
        assert client.get("/api/bootstrap").status_code == 200
        assert client.post("/api/desktop/setup", json={
            "company_name": "二つ目", "display_name": "別の人"
        }).status_code == 409

    with empty_installation() as db:
        assert len(db.scalars(select(User)).all()) == 1
        assert len(db.scalars(select(Member)).all()) == 1


def test_desktop_does_not_choose_between_multiple_users(empty_installation, monkeypatch):
    with TestClient(app) as client:
        assert client.post("/api/setup", json=owner_data()).status_code == 201
        assert client.post("/api/auth/logout").status_code == 200
        with empty_installation() as db:
            company = db.scalar(select(Company))
            user = User(
                username="colleague",
                display_name="共同担当",
                password_hash=hash_password("another-private-password"),
            )
            db.add(user)
            db.flush()
            db.add(Member(company_id=company.id, user_id=user.id, role="member"))
            db.commit()

        monkeypatch.setenv("ESTIMATE2_DESKTOP_TOKEN", "another-launch-token")
        assert client.get("/api/desktop/launch?token=another-launch-token").status_code == 200
        assert client.post("/api/desktop/resume", json={}).status_code == 409
        assert client.get("/api/bootstrap").status_code == 401
