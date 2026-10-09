"""Decisions: participation and go/no-go, recorded with evidence and a named person.  Owner: Atharv.

Public contract:
    evidence(db, opp_id) -> dict                           the evidence pack shown before deciding
    summary(db, opp_id) -> dict                            go/no-go summary: per requirement fully / partly / not / bid
        desk (from the unit's answer, else estimated from the match), counts by category, criteria (go_no_go.json)
        with met / not_met / unknown ("data not yet available"), and advice. Never a decision.
    record(db, opp_id, kind, outcome, units, rationale, actor, criteria=None) -> Decision
        criteria: the person's judgement per criterion [{id, status: met|not_met|unknown, note}].
        LookupError: no such opportunity. ValueError: go/no-go before the requirements are frozen, a
        participation that is empty or names a unit that is not active, or an unknown criterion.
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
        "checks": matching.evidence_checks(db, opp_id),  # scope, tiers, engineering rules, LV solver (A-06)
    }


LEVEL_FROM_ANSWER = {"met": "fully", "partial": "partly", "not_met": "not", "exception": "not"}
LEVEL_FROM_OFFERING = {"CTO": "fully", "SEMI_CUSTOM": "partly", "ETO": "partly"}  # catalog vs engineering needed
WORST = ["not", "partly", "fully"]


def summary(db: Session, opp_id: str, ev: dict | None = None) -> dict:
    """Go/no-go summary (A-12): how each frozen requirement is satisfied, criteria, and advice. Layer 0 never decides."""
    from app.modules.workpackages import service as workpackages  # imported here: workpackages imports decisions
    ev = ev or evidence(db, opp_id)
    gng = catalog.go_no_go()
    reqs = [r for r in requirements.current(db, opp_id) if r.status == "approved" and r.baseline is not None]
    matches, work = matching.for_opportunity(db, opp_id), workpackages.by_requirement(db, opp_id)
    rows = []
    for r in reqs:
        m, answers = matches.get(r.req_id), [a for a in work.get(r.req_id, []) if a.compliance]
        if answers:  # the units' own answers win over the estimate; several units -> the weakest answer
            level = min((LEVEL_FROM_ANSWER[a.compliance] for a in answers), key=WORST.index)
            basis = "validated answer" if all(a.status == "validated" for a in answers) else "answer, not yet validated"
            units = [a.bu for a in answers]
        elif m and m.units:
            level = min((LEVEL_FROM_OFFERING[u["offering_type"]] for u in m.units), key=WORST.index)
            basis, units = "match", [u["bu"] for u in m.units]
        else:
            level, basis, units = ("bid_desk", "match", []) if m else ("not", "no match", [])
        rows.append({"req_id": r.req_id, "category": r.category, "text": r.text, "level": level, "basis": basis, "units": units})
    by_category = {}
    for row in rows:
        by_category.setdefault(row["category"], Counter())[row["level"]] += 1
    product = [row for row in rows if row["level"] != "bid_desk"]
    covered = sum(row["level"] in ("fully", "partly") for row in product) / len(product) if product else 0.0

    checks = ev["checks"]
    rules = {r["id"]: r for r in checks["rules"]}
    warns = [r["id"] for r in checks["rules"] if r["status"] == "warn"]
    auto = {  # criterion id -> (met?, detail); criteria with "data": "not_available" are never assessed here
        "scope_fit": (not checks["units_outside_scope"],
                      "Units outside the RFP's scope: " + ", ".join(checks["units_outside_scope"]) if checks["units_outside_scope"]
                      else f"Suggested units fit the layers in scope {checks['scope']['in_scope']}."),
        "all_matched": (not ev["unmatched"], f"{len(ev['unmatched'])} requirement(s) without a match." if ev["unmatched"] else "Every requirement is routed."),
        "coverage": (covered >= gng["coverage_threshold"],
                     f"{covered:.0%} of {len(product)} product requirements fully or partly satisfied (threshold {gng['coverage_threshold']:.0%}, placeholder)."),
        "engineering_rules": (all(r["status"] != "fail" for r in rules.values()),
                              "Failing: " + ", ".join(i for i, r in rules.items() if r["status"] == "fail") if any(r["status"] == "fail" for r in rules.values())
                              else "No engineering rule fails."),
        "open_questions": (not warns and not ev["unanchored"],
                           f"Rule warnings: {', '.join(warns) or 'none'}; unanchored requirements: {len(ev['unanchored'])}."),
        "matches_reviewed": (ev["not_reviewed"] == 0, f"{ev['not_reviewed']} product match(es) not yet accepted or changed by a person."),
        "pending_acquisition": (rules.get("R-004", {}).get("status") != "warn", rules.get("R-004", {}).get("note", "")),
    }
    schedule = [row["req_id"] for row in rows if row["category"] == "schedule"]
    criteria = []
    for c in gng["criteria"]:
        if c.get("data") == "not_available":
            detail = "Data not yet available."
            if c["id"] == "delivery" and schedule:
                detail += f" The RFP's schedule requirements: {', '.join(schedule)}."
            criteria.append({**c, "status": "unknown", "detail": detail})
        else:
            ok, detail = auto[c["id"]]
            criteria.append({**c, "status": "met" if ok else "not_met", "detail": detail})
    assessable = [c for c in criteria if c["status"] != "unknown"]
    met = sum(c["status"] == "met" for c in assessable)
    return {
        "rows": rows,
        "by_category": {cat: {lvl: n.get(lvl, 0) for lvl in ("fully", "partly", "not", "bid_desk")} for cat, n in by_category.items()},
        "coverage": round(covered, 3),
        "criteria": criteria,
        "advice": (f"Advice from Layer 0: {met} of {len(assessable)} assessable criteria met; "
                   f"{len(criteria) - len(assessable)} cannot be assessed yet (data not available). A person decides."),
    }


def record(db: Session, opp_id: str, kind: str, outcome: str, units: list[str], rationale: str, actor: str,
           criteria: list[dict] | None = None) -> Decision:
    if not opportunities.get(db, opp_id):
        raise LookupError(f"{opp_id} not found.")
    if kind == "go_no_go" and not requirements.baseline(db, opp_id):
        raise ValueError("Freeze the requirements before deciding go or no-go (review page).")
    if kind == "participation":
        active = {u["code"] for u in catalog.units()}
        if not units or set(units) - active:
            raise ValueError(f"Choose at least one active business unit; not active: {sorted(set(units) - active)}.")
    known = {c["id"] for c in catalog.go_no_go()["criteria"]}
    for c in criteria or []:
        if c["id"] not in known or c["status"] not in ("met", "not_met", "unknown"):
            raise ValueError(f"Unknown criterion or judgement: {c['id']} = {c['status']}.")
    ev = evidence(db, opp_id)
    if kind == "go_no_go":
        ev["summary"] = summary(db, opp_id, ev)  # stored as shown (design 7.3)
    d = Decision(opportunity_id=opp_id, kind=kind, outcome=outcome, units=units, evidence=ev, rationale=rationale,
                 criteria=criteria or [], decided_by=actor)
    db.add(d)
    audit.record(db, actor, "decided", kind, outcome, opp_id, units=units, rationale=rationale, criteria=criteria or [])
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
