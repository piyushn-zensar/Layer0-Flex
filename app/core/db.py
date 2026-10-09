"""Database engine, session and the declarative Base every module's models.py uses."""
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_db():
    """FastAPI dependency: one session per request."""
    with SessionLocal() as db:
        yield db


def init_db():
    """Create tables for every imported module, and make the audit log append-only (rule R8).
    ponytail: create_all, no migrations. Delete data/store/layer0.db after a model change; add Alembic for the pilot."""
    Base.metadata.create_all(engine)
    _check_columns()
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            for op in ("UPDATE", "DELETE"):
                conn.execute(text(
                    f"CREATE TRIGGER IF NOT EXISTS audit_event_no_{op.lower()} BEFORE {op} ON audit_event "
                    "BEGIN SELECT RAISE(ABORT, 'audit_event is append-only'); END"
                ))


class SchemaOutOfDate(RuntimeError):
    pass


def _check_columns() -> None:
    """create_all adds missing tables, never missing columns. After a teammate adds a column, an older local
    database would fail later on a random page; stop at start-up with the fix instead."""
    found = inspect(engine)
    missing = [f"{t.name}.{c.name}" for t in Base.metadata.sorted_tables
               for c in t.columns if c.name not in {col["name"] for col in found.get_columns(t.name)}]
    if missing:
        raise SchemaOutOfDate(
            f"The local database is older than the code (missing: {', '.join(missing)}). Stop the API, then run "
            "'.venv\Scripts\python -m scripts.seed_demo --reset' (or reset-demo.cmd) to rebuild the demo data.")
