"""Database engine, session and the declarative Base every module's models.py uses."""
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
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
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            for op in ("UPDATE", "DELETE"):
                conn.execute(text(
                    f"CREATE TRIGGER IF NOT EXISTS audit_event_no_{op.lower()} BEFORE {op} ON audit_event "
                    "BEGIN SELECT RAISE(ABORT, 'audit_event is append-only'); END"
                ))
