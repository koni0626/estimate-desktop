"""Integration tests use a newly created, disposable SQLite database."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "data").mkdir(exist_ok=True)
test_directory = TemporaryDirectory(prefix="estimate_test_", dir=ROOT / "data")
os.environ["DATABASE_URL"] = "sqlite:///" + (
    Path(test_directory.name) / "test.sqlite3"
).as_posix()


@pytest.fixture(scope="session", autouse=True)
def database():
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    from backend.seed import seed

    seed()
    yield
    from backend.app.db import engine

    engine.dispose()
    test_directory.cleanup()


@pytest.fixture
def clients():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    cache = {}

    def get(username):
        if username not in cache:
            client = TestClient(app)
            assert (
                client.post(
                    "/api/auth/login",
                    json={"username": username, "password": "demo1234"},
                ).status_code
                == 200
            )
            cache[username] = client
        return cache[username]

    yield get
    for client in cache.values():
        client.close()
