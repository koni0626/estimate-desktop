"""Create a consistent local backup of the SQLite database, including WAL data."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db import ROOT, database_path  # noqa: E402

if not database_path.is_file():
    raise SystemExit(f"Database file does not exist: {database_path}")

backup_dir = ROOT / "data" / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
backup_path = backup_dir / f"estimate2-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.sqlite3"
if backup_path.exists():
    raise SystemExit(f"Backup already exists: {backup_path}")

with sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True) as source:
    with sqlite3.connect(backup_path) as destination:
        source.backup(destination)
        if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Backup integrity check failed")

print(f"Backup created: {backup_path}")
