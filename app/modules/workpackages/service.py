"""Work packages: one-step dispatch to business units, checklist responses, validation.  Owner: Atharv.

Public contract:
    dispatch(db, opp_id, actor) -> int                    create assignments for participating units (idempotent)
    by_requirement(db, opp_id) -> dict[str, list[Assignment]]
    inbox(db, bu) -> list[Assignment]                     a unit's open work across all opportunities
    respond(db, assignment_id, compliance, product_ref, response, actor)
    validate(db, assignment_id, ok, note, actor)
    progress(db, opp_id) -> dict[str, dict]               bu -> {"total", "submitted", "validated"}
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.modules.catalog import service as catalog
from app.modules.decisions import service as decisions
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages.models import BID_DESK, COMPLIANCE, Assignment


def dispatch(db: Session, opp_id: str, actor: str) -> int:
    units = set(decisions.participating_units(db, opp_id))
    matches = matching.for_opportunity(db, opp_id)
    existing = {(a.req_id, a.bu) for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id))}
    created = 0
    for req in requirements.current(db, opp_id):
        m = matches.get(req.req_id)
        bu = m.bu if m and m.bu in units else BID_DESK
        if (req.req_id, bu) in existing:
            continue
        owner = catalog.unit(bu)["design_engineer"] if bu != BID_DESK else "Bid Manager"
        db.add(Assignment(opportunity_id=opp_id, req_id=req.req_id, bu=bu, owner=owner,
                          product_ref=m.product_id if m and bu != BID_DESK else None))
        audit.record(db, actor, "assigned", "assignment", req.req_id, opp_id, bu=bu, owner=owner)
        created += 1
    db.commit()
    opportunities.set_status(db, opp_id, "dispatched", actor)
    return created


def by_requirement(db: Session, opp_id: str) -> dict[str, list[Assignment]]:
    out = defaultdict(list)
    for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id).order_by(Assignment.id)):
        out[a.req_id].append(a)
    return dict(out)


def inbox(db: Session, bu: str) -> list[Assignment]:
    return list(db.scalars(select(Assignment).where(Assignment.bu == bu)
                           .order_by(Assignment.opportunity_id, Assignment.req_id)))


def respond(db: Session, assignment_id: int, compliance: str, product_ref: str | None, response: str, actor: str) -> None:
    assert compliance in COMPLIANCE, compliance
    a = db.get(Assignment, assignment_id)
    a.compliance, a.product_ref, a.response = compliance, product_ref or a.product_ref, response
    a.status, a.responded_by, a.responded_at = "submitted", actor, utcnow()
    audit.record(db, actor, "responded", "assignment", a.req_id, a.opportunity_id, bu=a.bu, compliance=compliance)
    db.commit()


def validate(db: Session, assignment_id: int, ok: bool, note: str, actor: str) -> None:
    a = db.get(Assignment, assignment_id)
    a.status, a.validated_by, a.validation_note = ("validated" if ok else "returned"), actor, note
    audit.record(db, actor, a.status, "assignment", a.req_id, a.opportunity_id, bu=a.bu, note=note)
    db.commit()


def progress(db: Session, opp_id: str) -> dict[str, dict]:
    out = defaultdict(lambda: {"total": 0, "submitted": 0, "validated": 0})
    for items in by_requirement(db, opp_id).values():
        for a in items:
            out[a.bu]["total"] += 1
            out[a.bu]["submitted"] += a.status in ("submitted", "validated")
            out[a.bu]["validated"] += a.status == "validated"
    return dict(out)
