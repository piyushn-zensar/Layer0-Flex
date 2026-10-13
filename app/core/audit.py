"""Append-only audit log (rule R8). Every decision and change in every module calls record().

The SQLite triggers in db.init_db() reject UPDATE and DELETE on this table.

    record(db, actor, action, entity, entity_id, opportunity_id=None, **data)   add an event (the caller commits)
    history(db, opportunity_id) -> list[AuditEvent]                              a bid's events, oldest first
    activity(db, opportunity_id, entity=None, req_id=None, bu=None, person=None, before=None, limit=200) -> dict
        the bid's activity log (C-16), newest first and read-only: filtered by entity, requirement (an event about
        it, its match or its unit answers: they use the requirement ID), unit (data "bu") and person (the actor);
        paged with before = the last id seen. {"events", "total", "next_before", "filters": {entities, people, units}}
"""
from datetime import datetime

from sqlalchemy import JSON, String, func, select
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


MAX_ACTIVITY = 1000


def activity(db: Session, opportunity_id: str, entity: str | None = None, req_id: str | None = None,
             bu: str | None = None, person: str | None = None, before: int | None = None, limit: int = 200) -> dict:
    bid = AuditEvent.opportunity_id == opportunity_id
    q = select(AuditEvent).where(bid)
    if entity:
        q = q.where(AuditEvent.entity == entity)
    if req_id:
        q = q.where(AuditEvent.entity_id == req_id)
    if bu:
        q = q.where(AuditEvent.data["bu"].as_string() == bu)
    if person:
        q = q.where(AuditEvent.actor == person)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    if before:
        q = q.where(AuditEvent.id < before)
    limit = max(1, min(limit, MAX_ACTIVITY))
    events = list(db.scalars(q.order_by(AuditEvent.id.desc()).limit(limit)))
    units = db.scalars(select(AuditEvent.data["bu"].as_string()).where(bid).distinct())
    return {"events": [{"id": e.id, "at": e.at, "actor": e.actor, "action": e.action, "entity": e.entity,
                        "entity_id": e.entity_id, "data": e.data} for e in events],
            "total": total, "next_before": events[-1].id if len(events) == limit else None,
            "filters": {"entities": sorted(db.scalars(select(AuditEvent.entity).where(bid).distinct())),
                        "people": sorted(db.scalars(select(AuditEvent.actor).where(bid).distinct())),
                        "units": sorted(u for u in units if u)}}
