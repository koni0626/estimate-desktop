"""Desktop backup and upgrade preserve existing SQLite data."""

import shutil
import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.models import Company
from desktop import backup_database, migrate_database


ROOT = Path(__file__).resolve().parents[1]
INITIAL_REVISION = "7c8043b713ef"


def migration_config(tmp_path):
    scripts = tmp_path / "migrations"
    versions = scripts / "versions"
    versions.mkdir(parents=True)
    shutil.copy2(ROOT / "backend/migrations/env.py", scripts / "env.py")
    shutil.copy2(
        ROOT / "backend/migrations/versions/7c8043b713ef_sqlite_initial.py",
        versions / "7c8043b713ef_sqlite_initial.py",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(scripts))
    return config, versions


def add_next_revision(versions, *, fail=False):
    operation = (
        "op.execute('SELECT missing_column FROM companies')"
        if fail
        else "op.add_column('companies', sa.Column('upgrade_marker', sa.String(20)))"
    )
    (versions / "test_next.py").write_text(
        "from alembic import op\n"
        "import sqlalchemy as sa\n"
        "revision = 'test_next'\n"
        f"down_revision = '{INITIAL_REVISION}'\n"
        "branch_labels = None\n"
        "depends_on = None\n"
        f"def upgrade():\n    {operation}\n"
        "def downgrade():\n    pass\n",
        encoding="utf-8",
    )


def old_database(tmp_path):
    config, versions = migration_config(tmp_path)
    path = tmp_path / "estimate2.sqlite3"
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    assert migrate_database(config, path, engine) is None
    with Session(engine) as session:
        session.add(Company(name="既存の事業者"))
        session.commit()
    return config, versions, path, engine


def test_backup_database_includes_live_wal_data(tmp_path):
    source = tmp_path / "estimate2.sqlite3"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE samples (value TEXT NOT NULL)")
        db.execute("INSERT INTO samples VALUES ('saved')")
        db.commit()

        target = backup_database(source)

    assert target.parent == tmp_path / "backups"
    assert target != source
    with sqlite3.connect(target) as backup:
        assert backup.execute("SELECT value FROM samples").fetchall() == [("saved",)]
        assert backup.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_upgrade_backs_up_existing_database_and_preserves_data(tmp_path):
    config, versions, path, engine = old_database(tmp_path)
    try:
        add_next_revision(versions)
        backup = migrate_database(config, path, engine)
        assert backup is not None
        assert backup.name.startswith("estimate2-before-upgrade-")
        assert migrate_database(config, path, engine) is None
        assert list((tmp_path / "backups").glob("*.sqlite3")) == [backup]

        with sqlite3.connect(backup) as before, sqlite3.connect(path) as after:
            assert before.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert before.execute("SELECT name FROM companies").fetchall() == [
                ("既存の事業者",)
            ]
            assert before.execute("SELECT version_num FROM alembic_version").fetchone() == (
                INITIAL_REVISION,
            )
            assert after.execute("SELECT name FROM companies").fetchall() == [
                ("既存の事業者",)
            ]
            assert after.execute("SELECT version_num FROM alembic_version").fetchone() == (
                "test_next",
            )
            assert "upgrade_marker" in [
                row[1] for row in after.execute("PRAGMA table_info(companies)")
            ]
    finally:
        engine.dispose()


def test_failed_upgrade_reports_intact_backup(tmp_path):
    config, versions, path, engine = old_database(tmp_path)
    try:
        add_next_revision(versions, fail=True)
        with pytest.raises(RuntimeError, match="データベースの更新に失敗") as error:
            migrate_database(config, path, engine)
        backup = next((tmp_path / "backups").glob("*.sqlite3"))
        assert str(backup) in str(error.value)
        with sqlite3.connect(backup) as before:
            assert before.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert before.execute("SELECT name FROM companies").fetchall() == [
                ("既存の事業者",)
            ]
            assert before.execute("SELECT version_num FROM alembic_version").fetchone() == (
                INITIAL_REVISION,
            )
    finally:
        engine.dispose()
