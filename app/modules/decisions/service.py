"""Decisions: participation and go/no-go, recorded with evidence and a named person.  Owner: Atharv.

Public contract:
    evidence(db, opp_id) -> dict                           the evidence pack shown before deciding
    record(db, opp_id, kind, outcome, units, rationale, actor) -> Decision
        LookupError: no such opportunity. ValueError: go/no-go before the requirements are frozen, or a
        participation that is empty or names a unit that is not active.
    latest(db, opp_id, kind) -> Decision | None
    participating_units(db, opp_id) -> list[str]
"""
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.catalog import service as catalog
from app.modules.decisions.models import Decision
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements


def evidence(db: Session, opp_id: str) -> dict:
    """ponytail: counts only. Add v1.1 bid/portfolio checks (capacity, deviations) after the Monday demo."""
    reqs = requirements.current(db, opp_id)
    active = {r.req_id for r in reqs}  # matches of split, merged or rejected items no longer count
    matches = {req_id: m for req_id, m in matching.for_opportunity(db, opp_id).items() if req_id in active}
    return {
        "requirements": len(reqs),
        "frozen": requirements.baseline(db, opp_id) is not None,
        "by_category": dict(Counter(r.category for r in reqs)),
        "unanchored": [r.req_id for r in reqs if r.provenance == "UNANCHORED"],
        "suggested_units": {bu: len(ids) for bu, ids in matching.suggested_units(db, opp_id).items()},
        "offering_mix": dict(Counter(m.offering_type for m in matches.values())),
        "unmatched": [r.req_id for r in reqs if r.req_id not in matches],
        "not_reviewed": sum(m.status == "proposed" and bool(m.units) for m in matches.values()),  # product matches nobody accepted
    }


def record(db: Session, opp_id: str, kind: str, outcome: str, units: list[str], rationale: str, actor: str) -> Decision:
    if not opportunities.get(db, opp_id):
        raise LookupError(f"{opp_id} not found.")
    if kind == "go_no_go" and not requirements.baseline(db, opp_id):
        raise ValueError("Freeze the requirements before deciding go or no-go (review page).")
    if kind == "participation":
        active = {u["code"] for u in catalog.units()}
        if not units or set(units) - active:
            raise ValueError(f"Choose at least one active business unit; not active: {sorted(set(units) - active)}.")
    d = Decision(opportunity_id=opp_id, kind=kind, outcome=outcome, units=units,
                 evidence=evidence(db, opp_id), rationale=rationale, decided_by=actor)
    db.add(d)
    audit.record(db, actor, "decided", kind, outcome, opp_id, units=units, rationale=rationale)
    db.commit()
    if kind == "go_no_go":
        opportunities.set_status(db, opp_id, outcome, actor)
    return d


def latest(db: Session, opp_id: str, kind: str) -> Decision | None:
    return db.scalar(select(Decision).where(Decision.opportunity_id == opp_id, Decision.kind == kind)
                     .order_by(Decision.id.desc()).limit(1))


def participating_units(db: Session, opp_id: str) -> list[str]:
    d = latest(db, opp_id, "participation")
    return d.units if d else []
