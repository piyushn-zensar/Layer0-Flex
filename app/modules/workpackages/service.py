"""Work packages: one-step dispatch to business units, checklist responses, validation.  Owner: Atharv.

Public contract:
    dispatch(db, opp_id, actor) -> int                    one assignment per matched participating unit for every
                                                          published approved requirement; with no such unit a
                                                          non-product item goes to the bid desk and a product item
                                                          is not dispatched (needs an owner, C-08) unless a capability
                                                          gap is recorded; returns
                                                          how many were created (repeatable). Work that no longer
                                                          fits the matches or participation is withdrawn, and
                                                          withdrawn work that fits again is reopened. Needs no go
                                                          decision (C-06): ValueError without a published register
                                                          or a participation, or when the latest go/no-go is "no_go"
    withdraw_open(db, opp_id, actor) -> int               a no-go: the units' open work (assigned or returned) is
                                                          withdrawn, submitted and validated answers stay; returns
                                                          how many. A later go and dispatch reopen it
    needs_owner(db, opp_id) -> list[dict]                 published product requirements with no participating unit
                                                          and no capability gap: {req_id, text, category, suggested
                                                          (matched units not taking part)}; not dispatched
    record_gap(db, opp_id, req_id, reason, actor) -> Assignment   a capability gap: no unit can offer this product
        requirement; a validated non-compliant bid desk answer with the reason, kept in the register and the matrix.
        LookupError: not in the published register; ValueError: no reason, or a participating unit holds it
    assessment(db, opp_id) -> dict                        the Assessment step (16.5): published, baseline, summary
        {requirements, by_category, by_offering, sections, suggested_units}, open_questions {exceptions, needs_owner,
        rule_warnings, questions}, participation {id, units, rationale, decided_by} | None, no_go, units (catalog),
        routing [{req_id, text, category, section, route: unit | bid_desk |
        capability_gap | needs_owner, units [{bu, product_id, specialists}]}] (before publishing: a preview of the
        register; without a participation: with the suggested units), sent, progress. LookupError: unknown bid
    by_requirement(db, opp_id) -> dict[str, list[Assignment]]   active (not withdrawn) assignments
    inbox(db, bu) -> list[Assignment]                     a unit's active work across all opportunities
    workflow() -> dict                                    data/knowledge_base/workflow.json: who answers, validates and
        returns with a question (C-07, C-25), and which non-technical categories go to the units' managers
    people(db, assignment) -> dict                        {"answer": [...], "validate": [...]}: the people
        ({name, role, bu}) the workflow gives this assignment (scripts act as them, e.g. the seed)
    actions(db, assignment, user) -> dict                 what the signed-in user may do now: {answer, validate,
        return}; role and unit come from the token (C-25)
    get(db, assignment_id) -> Assignment | None           one assignment
    history(db, assignment_id) -> list[dict]              every event of the assignment, oldest first (C-16):
        {id, at, actor, action, note, before, after}; before / after hold only what the event changed (status,
        compliance, product_ref, response, reason, conditions, workaround, next_steps). LookupError: no such assignment
    respond(db, assignment_id, compliance, product_ref, response, user, reason="", conditions="", workaround="",
            next_steps="")
        user = {name, role, bu}: the workflow's answering role in the assignment's unit (technical items: unit
        designer / engineer; non-technical: unit manager; bid desk: bid manager), only while assigned or
        returned. partial and not_met need a reason (C-12); empty fields are stored as None.
        LookupError: no such assignment; PermissionError: wrong person; ValueError: wrong state, missing reason
    validate(db, assignment_id, ok, note, user)
        the unit's validating role (unit manager; bid desk: bid manager) validates or returns submitted work; the
        return_with_question roles (bid manager) may also return submitted or validated work. A return (ok=False)
        needs a note; the unit answers the returned item again. LookupError / PermissionError / ValueError as above
    progress(db, opp_id) -> dict[str, dict]               bu -> {"total", "submitted", "validated"} (active work)
    handoff(db, opp_id, bu) -> dict                       per-unit hand-off payload (M8): items grouped by route
        (CPQ seed / basis of design / specialist queue), each with its source document (the main RFP or a change
        document), requires_human_completion; LookupError: unknown
        opportunity or no work for the unit; ValueError: the bid desk
    comments(db, opp_id, req_id=None, status=None) -> list[Comment]   a bid's questions and comments, oldest first (C-17)
    add_comment(db, opp_id, req_id, text, kind, actor, assignment_id=None) -> Comment   kind: question | comment.
        LookupError: unknown bid, a requirement outside it, or an assignment of another requirement; ValueError: no
        text or an unknown kind
    close_comment(db, comment_id, actor, any_author=False) -> Comment   the author closes it (any_author: the bid
        manager closes anyone's). LookupError / PermissionError / ValueError: already closed
    open_questions(db, opp_id) -> list[Comment]           open questions: they block consolidation (C-17)
    return_for_change(db, opp_id, req_ids, note, actor) -> int   a change document changed these requirements:
        their submitted / validated answers are returned with the note (the unit answers again), assigned and
        returned work keeps its status and gets the note. Returns how many assignments were touched
"""
import functools
import json
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import audit, config
from app.core.db import utcnow
from app.core.web import same_unit
from app.modules.catalog import service as catalog
from app.modules.decisions import service as decisions
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements
from app.modules.workpackages.models import BID_DESK, COMMENT_KINDS, COMPLIANCE, EXTENDED, NEEDS_REASON, Assignment, Comment

BID_MANAGER = "Bid Manager"  # the bid desk's person (the seeded bid manager account), shown as the owner of its items


@functools.cache
def workflow() -> dict:
    return json.loads((config.DATA / "knowledge_base" / "workflow.json").read_text("utf-8"))


def _kind(category: str | None) -> str:
    return "technical" if category in matching.PRODUCT_CATEGORIES else "non_technical"


def _roles(bu: str, category: str | None) -> tuple[list[str], list[str]]:
    """(answering roles, validating roles) for an item of this unit and category."""
    wf = workflow()
    if bu == BID_DESK:
        return wf["respond"]["BID"], wf["validate"]["BID"]
    kind = _kind(category)
    return wf["respond"][kind], wf["validate"].get(kind, wf["validate"].get("unit", []))


def _staff(bu: str, role: str) -> dict:
    if bu == BID_DESK or role == "bid_manager":  # the bid manager is no unit's person
        return {"name": BID_MANAGER, "role": role, "bu": None}
    return {"name": catalog.unit(bu)[role], "role": role, "bu": bu}


def _category(db: Session, a: Assignment) -> str | None:
    req = requirements.get(db, a.req_id)
    return req.category if req else None


def people(db: Session, a: Assignment) -> dict:
    answer, check = _roles(a.bu, _category(db, a))
    return {"answer": [_staff(a.bu, r) for r in answer], "validate": [_staff(a.bu, r) for r in check]}


def _holds(user: dict, a: Assignment, roles: list[str]) -> bool:
    """The user has one of `roles`, in the assignment's own unit (bid desk items: no unit)."""
    return user["role"] in roles and (a.bu == BID_DESK or user["role"] == "bid_manager" or same_unit(user, a.bu))


def actions(db: Session, a: Assignment, user: dict) -> dict:
    answer, check = _roles(a.bu, _category(db, a))
    validator = a.status == "submitted" and _holds(user, a, check)
    question = a.status in ("submitted", "validated") and user["role"] in workflow()["return_with_question"]
    return {"answer": a.status in ("assigned", "returned") and _holds(user, a, answer), "validate": validator,
            "return": validator or question}


def dispatch(db: Session, opp_id: str, actor: str) -> int:
    opportunities.require(db, opp_id)  # an unknown bid is a 404, not "not frozen"
    if not requirements.baseline(db, opp_id):
        raise ValueError("The requirement register is not frozen yet: read the RFP first (RFP step).")
    go = decisions.latest(db, opp_id, "go_no_go")
    if go and go.outcome == "no_go":
        raise ValueError("The bid is marked no-go: nothing is dispatched until a go decision resumes it.")
    units = set(decisions.participating_units(db, opp_id))
    if not units:
        raise ValueError("Record which business units take part before dispatch.")
    existing = _existing(db, opp_id)
    wanted, categories = {}, {}
    for req, targets in _routing(db, opp_id, units, existing):
        categories[req.req_id] = req.category
        for bu, product_ref in (targets or {}).items():  # None: needs an owner, not dispatched
            wanted[(req.req_id, bu)] = product_ref
    created = 0
    for (req_id, bu), product_ref in wanted.items():
        a = existing.get((req_id, bu))
        if a and a.status == "withdrawn":  # fits again: back to the unit, its earlier answer kept for reference
            a.status, a.compliance, a.validated_by, a.validation_note = "assigned", None, None, ""
            audit.record(db, actor, "reopened", "assignment", req_id, opp_id, bu=bu)
        elif not a:
            owner = _staff(bu, _roles(bu, categories[req_id])[0][0])["name"]  # the first answering role
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
        raise ValueError("Dispatch is already running for this bid; refresh and try again.")
    opportunities.set_status(db, opp_id, "dispatched", actor)
    return created


def _existing(db: Session, opp_id: str) -> dict:
    return {(a.req_id, a.bu): a for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id))}


def _is_gap(a: Assignment | None) -> bool:
    """A recorded capability gap: the bid desk's answered non-compliant item with a reason (record_gap)."""
    return bool(a) and a.status in ("submitted", "validated", "returned") and a.compliance == "not_met" and bool(a.reason)


def _routing(db: Session, opp_id: str, units: set[str], existing: dict, preview: bool = False):
    """(requirement, targets) for every published approved requirement (preview: the register before publishing too):
    targets = {bu: product_ref}, one per matched participating unit (its first product); else every participating
    unit's manager for a non-technical item of workflow()["unit_manager_categories"] that the matcher routed by rule
    (C-25); else the bid desk for a non-product item or a recorded capability gap; else None: a product requirement
    that needs an owner (C-08)."""
    matches = matching.for_opportunity(db, opp_id)
    for req in requirements.current(db, opp_id):
        if req.status != "approved" or (req.baseline is None and not preview):
            continue
        m = matches.get(req.req_id)
        targets = {}
        for u in m.units if m else []:
            if u["bu"] in units:
                targets.setdefault(u["bu"], u["product_id"])
        by_rule = not m or m.method == "rule"  # a person's own "no unit" keeps a non-product item on the bid desk
        if not targets and by_rule and units and req.category in workflow()["unit_manager_categories"]:
            targets = {bu: None for bu in sorted(units)}
        elif not targets and (req.category not in matching.PRODUCT_CATEGORIES or _is_gap(existing.get((req.req_id, BID_DESK)))):
            targets = {BID_DESK: None}
        yield req, targets or None


def needs_owner(db: Session, opp_id: str) -> list[dict]:
    units = set(decisions.participating_units(db, opp_id)) or set(matching.suggested_units(db, opp_id))
    matches = matching.for_opportunity(db, opp_id)
    return [{"req_id": req.req_id, "text": req.text, "category": req.category,
             "suggested": [u["bu"] for u in (matches[req.req_id].units if req.req_id in matches else [])]}
            for req, targets in _routing(db, opp_id, units, _existing(db, opp_id)) if targets is None]


def _specialists(bu: str, category: str | None) -> list[str]:
    """Who answers, then who validates (the same person is named once)."""
    answer, check = _roles(bu, category)
    return list(dict.fromkeys(_staff(bu, r)["name"] for r in answer + check))


def assessment(db: Session, opp_id: str) -> dict:
    opportunities.require(db, opp_id)
    ev, base = decisions.evidence(db, opp_id), requirements.baseline(db, opp_id)
    p, go = decisions.latest(db, opp_id, "participation"), decisions.latest(db, opp_id, "go_no_go")
    units = set(p.units if p else ev["suggested_units"])  # no participation yet: route with the suggested units (a preview)
    existing, matches = _existing(db, opp_id), matching.for_opportunity(db, opp_id)
    routing, sections = [], defaultdict(int)
    for req, targets in _routing(db, opp_id, units, existing, preview=True):
        sections[req.section] += bool(req.section)
        m = matches.get(req.req_id)
        if targets is None:
            route, rows = "needs_owner", [{"bu": u["bu"], "product_id": u["product_id"], "specialists": []} for u in (m.units if m else [])]
        elif BID_DESK in targets:
            route = "capability_gap" if _is_gap(existing.get((req.req_id, BID_DESK))) else "bid_desk"
            rows = [{"bu": BID_DESK, "product_id": None, "specialists": [BID_MANAGER]}]
        else:
            route = "unit"
            rows = [{"bu": bu, "product_id": p, "specialists": _specialists(bu, req.category)} for bu, p in targets.items()]
        routing.append({"req_id": req.req_id, "text": req.text, "category": req.category, "section": req.section,
                        "route": route, "units": rows})
    rules = [{"id": r["id"], "status": r["status"], "note": r["note"]} for r in ev["checks"]["rules"] if r["status"] in ("warn", "fail")]
    return {
        "published": base is not None, "baseline": base.number if base else None,
        "summary": {"requirements": len(routing), "by_category": dict(Counter(r["category"] for r in routing)),
                    "by_offering": ev["offering_mix"], "suggested_units": ev["suggested_units"],
                    "sections": [{"section": s, "count": n} for s, n in sorted(sections.items(), key=lambda x: -x[1]) if s][:8]},
        "open_questions": {
            "exceptions": [{"req_id": e["req_id"], "text": e["text"], "reason": e["reason"]} for e in requirements.exceptions(db, opp_id)],
            "needs_owner": [{"req_id": r["req_id"], "text": r["text"], "category": r["category"],
                             "suggested": [u["bu"] for u in r["units"]]} for r in routing if r["route"] == "needs_owner"],
            "rule_warnings": rules,
            "questions": [{"id": c.id, "req_id": c.req_id, "author": c.author, "text": c.text} for c in open_questions(db, opp_id)],
        },
        "participation": {"id": p.id, "units": p.units, "rationale": p.rationale, "decided_by": p.decided_by} if p else None,
        "no_go": bool(go and go.outcome == "no_go"), "units": catalog.units(), "routing": routing,
        "sent": bool(by_requirement(db, opp_id)), "progress": progress(db, opp_id),
    }


def record_gap(db: Session, opp_id: str, req_id: str, reason: str, actor: str) -> Assignment:
    if not reason.strip():
        raise ValueError("Say why no unit can offer it (reason).")
    existing = _existing(db, opp_id)
    route = {req.req_id: targets for req, targets in _routing(db, opp_id, set(decisions.participating_units(db, opp_id)), existing)}
    if req_id not in route:
        raise LookupError(f"{req_id} is not in the published register of {opp_id}.")
    if route[req_id] and BID_DESK not in route[req_id]:
        raise ValueError(f"{req_id} is held by {', '.join(route[req_id])}: that unit answers it.")
    a = existing.get((req_id, BID_DESK))
    if not a:
        a = Assignment(opportunity_id=opp_id, req_id=req_id, bu=BID_DESK, owner=BID_MANAGER)
        db.add(a)
    a.status, a.compliance, a.reason, a.response = "validated", "not_met", reason.strip(), a.response or ""
    a.responded_by, a.responded_at, a.validated_by = actor, utcnow(), actor
    audit.record(db, actor, "capability_gap", "assignment", req_id, opp_id, bu=BID_DESK, reason=a.reason)
    db.commit()
    return a


def withdraw_open(db: Session, opp_id: str, actor: str) -> int:
    rows = list(db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id,
                                                    Assignment.status.in_(("assigned", "returned")))))
    for a in rows:
        audit.record(db, actor, "withdrawn", "assignment", a.req_id, opp_id, bu=a.bu, was=a.status, reason="no-go")
        a.status = "withdrawn"
    db.commit()
    return len(rows)


def by_requirement(db: Session, opp_id: str) -> dict[str, list[Assignment]]:
    out = defaultdict(list)
    for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id, Assignment.status != "withdrawn")
                        .order_by(Assignment.id)):
        out[a.req_id].append(a)
    return dict(out)


def inbox(db: Session, bu: str) -> list[Assignment]:
    return list(db.scalars(select(Assignment).where(Assignment.bu == bu, Assignment.status != "withdrawn")
                           .order_by(Assignment.opportunity_id, Assignment.req_id)))


def respond(db: Session, assignment_id: int, compliance: str, product_ref: str | None, response: str, user: dict,
            reason: str = "", conditions: str = "", workaround: str = "", next_steps: str = "") -> None:
    # ponytail: "exception" is still accepted here for the seed's earlier-value answer; the API offers only OFFERED
    assert compliance in COMPLIANCE, compliance
    if compliance in NEEDS_REASON and not (reason or "").strip():
        raise ValueError("Say what is not met and why (reason) for a partially or non-compliant answer.")
    a = _get(db, assignment_id)
    who = people(db, a)["answer"]
    if not _holds(user, a, [p["role"] for p in who]):
        raise PermissionError(f"Only {' or '.join(p['name'] for p in who)} can answer this item.")
    if a.status not in ("assigned", "returned"):
        raise ValueError(f"This item is {a.status}; only assigned or returned items can be answered.")
    a.compliance, a.product_ref, a.response = compliance, product_ref or a.product_ref, response
    fields = {"reason": reason, "conditions": conditions, "workaround": workaround, "next_steps": next_steps}
    for f in EXTENDED:
        setattr(a, f, (fields[f] or "").strip() or None)
    actor = user["name"]
    a.status, a.responded_by, a.responded_at = "submitted", actor, utcnow()
    audit.record(db, actor, "responded", "assignment", a.req_id, a.opportunity_id, bu=a.bu, compliance=compliance,
                 product_ref=a.product_ref, response=a.response, **{f: getattr(a, f) for f in EXTENDED if getattr(a, f)})
    db.commit()


def get(db: Session, assignment_id: int) -> Assignment | None:
    return db.get(Assignment, assignment_id)


# The status each assignment event leaves behind ("validated" and "returned" are both recorded by validate()).
STATUS_AFTER = {"assigned": "assigned", "reopened": "assigned", "responded": "submitted", "validated": "validated",
                "returned": "returned", "withdrawn": "withdrawn", "capability_gap": "validated"}


def history(db: Session, assignment_id: int) -> list[dict]:
    a = _get(db, assignment_id)
    events = audit.activity(db, a.opportunity_id, entity="assignment", req_id=a.req_id, bu=a.bu,
                            limit=audit.MAX_ACTIVITY)["events"][::-1]  # oldest first; one assignment = req and unit
    state, out = {}, []
    for e in events:
        data = e["data"]
        after = state | {"status": STATUS_AFTER.get(e["action"], state.get("status"))}
        if e["action"] == "responded":  # earlier events lack product_ref and response: those stay as they were
            after |= {f: data.get(f) for f in ("compliance", "product_ref", "response", *EXTENDED) if f in data or f in EXTENDED}
        elif e["action"] == "capability_gap":
            after |= {"compliance": "not_met", "reason": data.get("reason")}
        changed = [k for k in after if after[k] != state.get(k)]
        out.append({"id": e["id"], "at": e["at"], "actor": e["actor"], "action": e["action"], "note": data.get("note") or "",
                    "before": {k: state.get(k) for k in changed}, "after": {k: after[k] for k in changed}})
        state = after
    return out


def _get(db: Session, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a:
        raise LookupError(f"Assignment {assignment_id} not found.")
    return a


def validate(db: Session, assignment_id: int, ok: bool, note: str, user: dict) -> None:
    a = _get(db, assignment_id)
    who = people(db, a)["validate"]
    validator = _holds(user, a, [p["role"] for p in who])
    question = not ok and user["role"] in workflow()["return_with_question"]  # the bid manager's return with a question
    if not (validator or question):
        raise PermissionError(f"Only {' or '.join(p['name'] for p in who)} validates this answer; the bid manager may "
                              "return it with a question.")
    if a.status not in ({"submitted"} | ({"validated"} if question else set())):
        raise ValueError(f"This item is {a.status}; only submitted answers can be validated or returned.")
    if not ok and not note.strip():
        raise ValueError("A returned answer needs a note saying why.")
    actor = user["name"]
    a.status, a.validated_by, a.validation_note = ("validated" if ok else "returned"), actor, note
    audit.record(db, actor, a.status, "assignment", a.req_id, a.opportunity_id, bu=a.bu, note=note)
    db.commit()


def comments(db: Session, opp_id: str, req_id: str | None = None, status: str | None = None) -> list[Comment]:
    opportunities.require(db, opp_id)
    q = select(Comment).where(Comment.opportunity_id == opp_id)
    if req_id:
        q = q.where(Comment.req_id == req_id)
    if status:
        q = q.where(Comment.status == status)
    return list(db.scalars(q.order_by(Comment.id)))


def add_comment(db: Session, opp_id: str, req_id: str, text: str, kind: str, actor: str,
                assignment_id: int | None = None) -> Comment:
    opportunities.require(db, opp_id)
    if kind not in COMMENT_KINDS:
        raise ValueError(f"A comment is a question or a comment, not {kind!r}.")
    if not text.strip():
        raise ValueError("Write the question or comment first.")
    req = requirements.get(db, req_id)
    if not req or req.opportunity_id != opp_id:
        raise LookupError(f"{req_id} is not a requirement of {opp_id}.")
    if assignment_id is not None:
        a = db.get(Assignment, assignment_id)
        if not a or (a.opportunity_id, a.req_id) != (opp_id, req_id):
            raise LookupError(f"Assignment {assignment_id} is not on {req_id}.")
    c = Comment(opportunity_id=opp_id, req_id=req_id, assignment_id=assignment_id, author=actor, text=text.strip(), kind=kind)
    db.add(c)
    db.flush()
    audit.record(db, actor, "asked" if kind == "question" else "commented", "comment", str(c.id), opp_id,
                 req_id=req_id, assignment_id=assignment_id, text=c.text)
    db.commit()
    return c


def close_comment(db: Session, comment_id: int, actor: str, any_author: bool = False) -> Comment:
    c = db.get(Comment, comment_id)
    if not c:
        raise LookupError(f"Comment {comment_id} not found.")
    if c.author != actor and not any_author:
        raise PermissionError(f"Only {c.author} or the bid manager closes this {c.kind}.")
    if c.status == "closed":
        raise ValueError(f"This {c.kind} was closed by {c.closed_by}.")
    c.status, c.closed_by, c.closed_at = "closed", actor, utcnow()
    audit.record(db, actor, "closed", "comment", str(c.id), c.opportunity_id, req_id=c.req_id)
    db.commit()
    return c


def open_questions(db: Session, opp_id: str) -> list[Comment]:
    return [c for c in comments(db, opp_id, status="open") if c.kind == "question"]


def return_for_change(db: Session, opp_id: str, req_ids: list[str], note: str, actor: str) -> int:
    """Changes module (section 8, step 5): work on a changed requirement goes back to its unit for review."""
    touched = 0
    for a in db.scalars(select(Assignment).where(Assignment.opportunity_id == opp_id, Assignment.req_id.in_(req_ids),
                                                 Assignment.status != "withdrawn").order_by(Assignment.id)):
        was = a.status
        if a.status in ("submitted", "validated"):  # the answer was for the old wording
            a.status, a.validated_by = "returned", actor
        a.validation_note = note
        audit.record(db, actor, "returned", "assignment", a.req_id, opp_id, bu=a.bu, note=note, reason="change", was=was)
        touched += 1
    db.commit()
    return touched


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
        raise LookupError(f"Bid {opp_id} not found.")
    if bu == BID_DESK:
        raise ValueError("The bid desk (commercial and submission items) answers its items itself; it has no downstream system to hand off to.")
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
                "document": req.document_id if req else None,  # the source's document: a change document (P-11)
                "requirement": req.text if req else None, "category": req.category if req else None,
                "product_id": product_id, "product": (catalog.product(product_id) or {}).get("name"),
                "offering_type": offering, "engineering_flags": flags.get(a.req_id, []),
                "unit_answer": {"status": a.status, "compliance": a.compliance, "product_ref": a.product_ref,
                                "response": a.response or None, "validated_by": a.validated_by,
                                **{f: getattr(a, f) for f in EXTENDED}},
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
