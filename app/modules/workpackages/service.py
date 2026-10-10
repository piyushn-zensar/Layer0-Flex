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
    get(db, assignment_id) -> Assignment | None           one assignment
    respond(db, assignment_id, compliance, product_ref, response, actor)
        only that unit's product manager / design engineer (bid desk: the Bid Manager), only while assigned or
        returned. LookupError: no such assignment; PermissionError: wrong person; ValueError: wrong state
    validate(db, assignment_id, ok, note, actor)
        only the Bid Manager, only submitted work; a return (ok=False) needs a note. The unit can then answer the
        returned item again. LookupError / PermissionError / ValueError as above
    progress(db, opp_id) -> dict[str, dict]               bu -> {"total", "submitted", "validated"} (active work)
    handoff(db, opp_id, bu) -> dict                       per-unit hand-off payload (M8): items grouped by route
        (CPQ seed / basis of design / specialist queue), requires_human_completion; LookupError: unknown
        opportunity or no work for the unit; ValueError: the bid desk
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


def get(db: Session, assignment_id: int) -> Assignment | None:
    return db.get(Assignment, assignment_id)


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


ROUTES = {  # reference/v0.3.0/routing (M8): route A seeds the CPQ, route B briefs design engineering, route C queues
    "cpq_seed": "Route A: commercial CPQ (configuration seed only; Layer 0 seeds the configurator, it does not configure)",
    "basis_of_design": "Route B: design engineering (basis of design; captured requirements, not a design)",
    "specialist_queue": "Route C: specialist engineering queue (no design attempted)",
}


def _route(offering_type: str, unit_tier: str | None) -> str:
    """Offering type -> M8 route; design 7.2: CTO = CTO_AUTOMATE, semi-custom = ETO_GUIDED, ETO = ETO_GUIDED or
    ETO_EXCEPTION (the unit's default tier decides). Most conservative wins, as in the tier fail-safe."""
    if unit_tier == "ETO_EXCEPTION":
        return "specialist_queue"
    return "cpq_seed" if offering_type == "CTO" else "basis_of_design"


def handoff(db: Session, opp_id: str, bu: str) -> dict:
    """Per-unit hand-off payload (task A-09, M8): one JSON per unit and opportunity with every active assignment,
    grouped by route. Every payload requires human completion; nothing in it is a configuration or a design.
    LookupError: unknown opportunity, or no work for this unit; ValueError: the bid desk has no downstream system."""
    opp = opportunities.get(db, opp_id)
    if not opp:
        raise LookupError(f"{opp_id} not found.")
    if bu == BID_DESK:
        raise ValueError("The bid desk answers its items itself; it has no downstream system to hand off to.")
    unit = catalog.unit(bu)
    items = [a for a in inbox(db, bu) if a.opportunity_id == opp_id]
    if not unit or not items:
        raise LookupError(f"No work for {bu} in {opp_id}.")
    matches = matching.for_opportunity(db, opp_id)
    ev = matching.evidence_checks(db, opp_id)
    flags = defaultdict(list)
    for f in ev["tier_flags"]:
        if f["bu"] == bu:
            flags[f["req_id"]].append(f["note"])
    unit_tier = catalog.layers()["unit_tiers"].get(bu, {}).get("tier")
    stated = {k: v for k, v in ev["facts"].items() if v}
    routes = {r: [] for r in ROUTES}
    for a in items:
        req = requirements.get(db, a.req_id)
        m = matches.get(a.req_id)
        # every product of this unit on the requirement gets its own route (e.g. a CDU to design, a cold plate to CPQ)
        mine = [u for u in (m.units if m else []) if u["bu"] == bu] or [{"product_id": a.product_ref, "offering_type": None}]
        for u in mine:
            product_id = u["product_id"]
            offering = u["offering_type"] or (catalog.product(product_id) or {}).get("offering_type", "ETO")
            route = _route(offering, unit_tier)
            item = {
                "req_id": a.req_id, "source": req.source if req else None, "quote": req.quote if req else None,
                "requirement": req.text if req else None, "category": req.category if req else None,
                "product_id": product_id, "product": (catalog.product(product_id) or {}).get("name"),
                "offering_type": offering, "engineering_flags": flags.get(a.req_id, []),
                "unit_answer": {"status": a.status, "compliance": a.compliance, "product_ref": a.product_ref,
                                "response": a.response or None, "validated_by": a.validated_by},
            }
            if route == "cpq_seed":
                item["configuration_seed"] = {"product_id": product_id, "bom_lines": catalog.bom(product_id) if product_id else []}
            elif route == "basis_of_design":
                item["basis_of_design"] = {"captured_requirement": item["quote"], "spec_claimed": False,
                                           "note": "Layer 0 has NOT designed this: captured requirements only."}
            else:
                item["design_attempted"] = False
            routes[route].append(item)
    go = decisions.latest(db, opp_id, "go_no_go")
    return {
        "opportunity": {"id": opp.id, "title": opp.title, "customer": opp.customer},
        "document": (opportunities.main_document(db, opp_id).id if opportunities.main_document(db, opp_id) else None),
        "unit": {"code": bu, "name": unit["name"], "default_tier": unit_tier,
                 "owner": unit["design_engineer"], "product_manager": unit["product_manager"]},
        "decision": {"outcome": go.outcome, "decided_by": go.decided_by, "decided_at": go.decided_at.isoformat()} if go else None,
        "generated_at": utcnow().isoformat(),
        "requires_human_completion": True,
        "stated_facts": stated,  # from the frozen requirements, each citing its REQ (A-06)
        "routes": {r: {"destination": ROUTES[r], "items": routes[r]} for r in ROUTES if routes[r]},
        "note": ("Hand-off for the unit's own systems. Every item needs a person: CPQ seeds are starting points, "
                 "basis-of-design items are captured requirements, not designs."),
    }
