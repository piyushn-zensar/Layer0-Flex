"""Append-only audit log (rule R8). Every decision and change in every module calls record().

The SQLite triggers in db.init_db() reject UPDATE and DELETE on this table.
"""
from datetime import datetime

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base, utcnow


class AuditEvent(Base):
    __tablename__ = "audit_event"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(default=utcnow)
    opportunity_id: Mapped[str | None] = mapped_column(String(20), index=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(40))      # e.g. created, approved, frozen, responded
    entity: Mapped[str] = mapped_column(String(40))      # e.g. requirement, decision, assignment
    entity_id: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict] = mapped_column(JSON, default=dict)  # before / after / reason


def record(db: Session, actor: str, action: str, entity: str, entity_id: str,
           opportunity_id: str | None = None, **data) -> None:
    """Add an event to the caller's transaction. The caller commits."""
    db.add(AuditEvent(actor=actor, action=action, entity=entity, entity_id=str(entity_id),
                      opportunity_id=opportunity_id, data=data))


def history(db: Session, opportunity_id: str) -> list[AuditEvent]:
    return list(db.scalars(select(AuditEvent).where(AuditEvent.opportunity_id == opportunity_id)
                           .order_by(AuditEvent.id)))
