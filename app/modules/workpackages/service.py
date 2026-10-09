"""Work packages: one-step dispatch to business units, checklist responses, validation.  Owner: Atharv.

Public contract:
    dispatch(db, opp_id, actor) -> int                    one assignment per matched participating unit, else the
                                                          bid desk, for every frozen approved requirement; returns
                                                          how many were created (repeatable). Work that no longer
                                                          fits the matches or participation is withdrawn, and
                                                          withdrawn work that fits again is reopened.
                                                          ValueError unless frozen and the latest go/no-go is "go"
    by_requirement(db, opp_id) -> dict[str, list[Assignment]]   active (not withdrawn) assignments
    inbox(db, bu) -> list[Assignment]                     a unit's active work across all opportunities
    respond(db, assignment_id, compliance, product_ref, response, actor)
        only that unit's product manager / design engineer (bid desk: the Bid Manager), only while assigned or
        returned. LookupError: no such assignment; PermissionError: wrong person; ValueError: wrong state
    validate(db, assignment_id, ok, note, actor)
        only the Bid Manager, only submitted work; a return (ok=False) needs a note. The unit can then answer the
        returned item again. LookupError / PermissionError / ValueError as above
    progress(db, opp_id) -> dict[str, dict]               bu -> {"total", "submitted", "validated"} (active work)
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.modules.catalog import service as catalog
from app.modules.decisions import service as decisions
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages.models import BID_DESK, COMPLIANCE, Assignment

BID_MANAGER = "Bid Manager"  # ponytail: PoC actor name from the header picker; real roles come with sign-in


def dispatch(db: Session, opp_id: str, actor: str) -> int:
    if not requirements.baseline(db, opp_id):
        raise ValueError("Freeze the requirements before dispatch (review page).")
    go = decisions.latest(db, opp_id, "go_no_go")
    if not go or go.outcome != "go":
        raise ValueError("Dispatch needs a 'go' decision first (decisions page).")
    units = set(decisions.participating_units(db, opp_id))
    matches = matching.for_opportunity(db, opp_id)
    existing = {(a.req_id, a.bu): a for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id))}
    wanted = {}
    for req in requirements.current(db, opp_id):
        if req.status != "approved" or req.baseline is None:
            continue
        m = matches.get(req.req_id)
        # one assignment per matched participating unit (its first product); none of them -> the bid desk
        targets = {}
        for u in m.units if m else []:
            if u["bu"] in units:
                targets.setdefault(u["bu"], u["product_id"])
        for bu, product_ref in (targets or {BID_DESK: None}).items():
            wanted[(req.req_id, bu)] = product_ref
    created = 0
    for (req_id, bu), product_ref in wanted.items():
        a = existing.get((req_id, bu))
        if a and a.status == "withdrawn":  # fits again: back to the unit, its earlier answer kept for reference
            a.status = "assigned"
            audit.record(db, actor, "reopened", "assignment", req_id, opp_id, bu=bu)
        elif not a:
            owner = catalog.unit(bu)["design_engineer"] if bu != BID_DESK else BID_MANAGER
            db.add(Assignment(opportunity_id=opp_id, req_id=req_id, bu=bu, owner=owner, product_ref=product_ref))
            audit.record(db, actor, "assigned", "assignment", req_id, opp_id, bu=bu, owner=owner)
            created += 1
    for key, a in existing.items():
        if key not in wanted and a.status != "withdrawn":  # match, participation or requirement changed
            audit.record(db, actor, "withdrawn", "assignment", a.req_id, opp_id, bu=a.bu, was=a.status)
            a.status = "withdrawn"
    try:
        db.commit()
    except IntegrityError:  # another dispatch of the same opportunity got there first
        db.rollback()
        raise ValueError("Dispatch is already running for this opportunity; refresh and try again.")
    opportunities.set_status(db, opp_id, "dispatched", actor)
    return created


def by_requirement(db: Session, opp_id: str) -> dict[str, list[Assignment]]:
    out = defaultdict(list)
    for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id, Assignment.status != "withdrawn")
                        .order_by(Assignment.id)):
        out[a.req_id].append(a)
    return dict(out)


def inbox(db: Session, bu: str) -> list[Assignment]:
    return list(db.scalars(select(Assignment).where(Assignment.bu == bu, Assignment.status != "withdrawn")
                           .order_by(Assignment.opportunity_id, Assignment.req_id)))


def _may_answer(actor: str, bu: str) -> bool:
    if bu == BID_DESK:
        return actor == BID_MANAGER
    unit = catalog.unit(bu)
    return bool(unit) and actor in (unit["product_manager"], unit["design_engineer"])


def respond(db: Session, assignment_id: int, compliance: str, product_ref: str | None, response: str, actor: str) -> None:
    assert compliance in COMPLIANCE, compliance
    a = _get(db, assignment_id)
    if not _may_answer(actor, a.bu):
        raise PermissionError(f"Only {a.bu}'s product manager or design engineer can answer this item.")
    if a.status not in ("assigned", "returned"):
        raise ValueError(f"This item is {a.status}; only assigned or returned items can be answered.")
    a.compliance, a.product_ref, a.response = compliance, product_ref or a.product_ref, response
    a.status, a.responded_by, a.responded_at = "submitted", actor, utcnow()
    audit.record(db, actor, "responded", "assignment", a.req_id, a.opportunity_id, bu=a.bu, compliance=compliance)
    db.commit()


def _get(db: Session, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a:
        raise LookupError(f"Assignment {assignment_id} not found.")
    return a


def validate(db: Session, assignment_id: int, ok: bool, note: str, actor: str) -> None:
    a = _get(db, assignment_id)
    if actor != BID_MANAGER:
        raise PermissionError("Only the Bid Manager validates or returns answers.")
    if a.status != "submitted":
        raise ValueError(f"This item is {a.status}; only submitted answers can be validated or returned.")
    if not ok and not note.strip():
        raise ValueError("A returned answer needs a note saying why (design 7.5).")
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
