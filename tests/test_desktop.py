"""Desktop data is backed up consistently while the source database is open."""

import sqlite3

from desktop import backup_database


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
