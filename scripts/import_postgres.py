"""One-time copy from the previous PostgreSQL estimate2 DB into empty SQLite."""

from hashlib import sha256
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import dotenv_values
from sqlalchemy import LargeBinary, create_engine, func, select, text
from sqlalchemy.engine import make_url

from backend.app.db import ROOT, Base, engine as sqlite_engine
from backend.app import models  # noqa: F401 - register all tables


source_env = ROOT / "data" / "postgres-source.env"
if not source_env.is_file():
    raise SystemExit(f"PostgreSQL connection file is missing: {source_env}")
source_url = dotenv_values(source_env).get("DATABASE_URL")
if not source_url or make_url(source_url).get_backend_name() != "postgresql":
    raise SystemExit("Source DATABASE_URL must point to the old PostgreSQL DB.")
if sqlite_engine.url.get_backend_name() != "sqlite":
    raise SystemExit("Destination DATABASE_URL must point to SQLite.")

source_engine = create_engine(source_url)
tables = Base.metadata.sorted_tables


def blob_digests(connection, table):
    columns = [column for column in table.columns if isinstance(column.type, LargeBinary)]
    if not columns:
        return None
    result = []
    for row in connection.execute(select(table)).mappings():
        result.append(
            (
                row["id"],
                tuple(
                    sha256(bytes(row[column.name])).hexdigest()
                    if row[column.name] is not None
                    else None
                    for column in columns
                ),
            )
        )
    return sorted(result)


with source_engine.connect() as source, sqlite_engine.begin() as destination:
    for table in tables:
        if destination.scalar(select(func.count()).select_from(table)):
            raise SystemExit("Destination is not empty; import was cancelled without changes.")

    counts = {}
    for table in tables:
        rows = [dict(row) for row in source.execute(select(table)).mappings()]
        if rows:
            destination.execute(table.insert(), rows)
        counts[table.name] = len(rows)

    for table in tables:
        copied = destination.scalar(select(func.count()).select_from(table))
        if copied != counts[table.name] or blob_digests(source, table) != blob_digests(destination, table):
            raise RuntimeError(f"Data verification failed for {table.name}")
    violations = destination.execute(text("PRAGMA foreign_key_check")).fetchall()
    if violations:
        raise RuntimeError(f"SQLite foreign-key verification failed: {violations[:3]}")

source_engine.dispose()
print(f"Copied {sum(counts.values())} rows across {len(tables)} tables; blob hashes and foreign keys verified.")
