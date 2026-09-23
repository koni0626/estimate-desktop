import os
from datetime import timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import DateTime, MetaData, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
database_url = make_url(os.getenv("DATABASE_URL", "sqlite:///data/estimate2.sqlite3"))
if database_url.get_backend_name() != "sqlite" or not database_url.database:
    raise RuntimeError("This application requires a file-based SQLite database.")
database_path = Path(database_url.database)
if not database_path.is_absolute():
    database_path = ROOT / database_path
database_path.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = database_url.set(database=str(database_path)).render_as_string(hide_password=False)
engine = create_engine(DATABASE_URL, connect_args={"timeout": 30, "check_same_thread": False})


@event.listens_for(engine, "connect")
def sqlite_connection(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(engine, expire_on_commit=False)


class UTCDateTime(TypeDecorator):
    """Store UTC in SQLite and restore timezone-aware values when reading."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name == "sqlite" and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and dialect.name == "sqlite" and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def get_db(request: Request):
    with SessionLocal() as db:
        try:
            # SQLite ignores SELECT FOR UPDATE. Serialize mutations before reads.
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                db.execute(text("BEGIN IMMEDIATE"))
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
