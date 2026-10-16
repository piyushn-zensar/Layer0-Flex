"""Decisions: participation and go/no-go, recorded with evidence and a named person.  Owner: Atharv.

Public contract:
    evidence(db, opp_id) -> dict                           the evidence pack shown before deciding
    summary(db, opp_id) -> dict                            go/no-go summary: per requirement fully / partly / not / bid
        desk or needs an owner (from the unit's answer, else estimated from the match), counts by category,
        needs_owner (workpackages.needs_owner: product requirements no participating unit holds), open_questions
        (how many questions are open, C-17), assessment {items,
        validated} (the work sent to the units), criteria (go_no_go.json) with met / not_met / unknown, where
        completeness, compliance and schedule come from validated answers (C-10), and advice. Never a decision.
    record(db, opp_id, kind, outcome, units, rationale, actor, criteria=None) -> Decision
        criteria: the person's judgement per criterion [{id, status: met|not_met|unknown, note}].
        LookupError: no such bid. ValueError: go/no-go before the register is published, a
        participation that is empty or names a unit that is not active, or an unknown criterion.
    latest(db, opp_id, kind) -> Decision | None
    get(db, decision_id) -> Decision | None
    participating_units(db, opp_id) -> list[str]
"""
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.catalog import service as catalog
from app.modules.decisions import portfolio
from app.modules.decisions.models import Decision
from app.modules.matching import service as matching
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service as requirements


def evidence(db: Session, opp_id: str) -> dict:
    """Counts, engineering checks (A-06), and the bid and portfolio checks (A-10: deviations, workload)."""
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
        "deviations": portfolio.deviations(db, opp_id),  # A-10: RFP data sheet vs standard product ratings
        "workload": portfolio.workload(db, opp_id),      # A-10: open work per unit across opportunities vs capacity
    }


LEVEL_FROM_ANSWER = {"met": "fully", "partial": "partly", "not_met": "not", "exception": "not"}
LEVEL_FROM_OFFERING = {"CTO": "fully", "SEMI_CUSTOM": "partly", "ETO": "partly"}  # catalog vs engineering needed
WORST = ["not", "partly", "fully"]


def _worst(answers: list) -> str:
    """The weakest level among several units' answers to one requirement."""
    return min((LEVEL_FROM_ANSWER[a.compliance] for a in answers), key=WORST.index)


def summary(db: Session, opp_id: str, ev: dict | None = None) -> dict:
    """Go/no-go summary (A-12, A-15): how each published requirement is satisfied, criteria, and advice. Layer 0 never decides."""
    from app.modules.workpackages import service as workpackages  # imported here: workpackages imports decisions
    ev = ev or evidence(db, opp_id)
    gng = catalog.go_no_go()
    reqs = [r for r in requirements.current(db, opp_id) if r.status == "approved" and r.baseline is not None]
    matches, work = matching.for_opportunity(db, opp_id), workpackages.by_requirement(db, opp_id)
    rows = []
    for r in reqs:
        m, answers = matches.get(r.req_id), [a for a in work.get(r.req_id, []) if a.compliance]
        if answers:  # the units' own answers win over the estimate; several units -> the weakest answer
            level = _worst(answers)
            basis = "validated answer" if all(a.status == "validated" for a in answers) else "answer, not yet validated"
            units = [a.bu for a in answers]
        elif m and m.units:
            level = min((LEVEL_FROM_OFFERING[u["offering_type"]] for u in m.units), key=WORST.index)
            basis, units = "match", [u["bu"] for u in m.units]
        else:
            # C-08: only non-product items belong to the bid desk; a product item without a unit needs an owner
            level, basis, units = (("bid_desk", "rule", []) if r.category not in matching.PRODUCT_CATEGORIES
                                   else ("not", "needs an owner" if m else "no match", []))
        rows.append({"req_id": r.req_id, "category": r.category, "text": r.text, "level": level, "basis": basis, "units": units})
    by_category = {}
    for row in rows:
        by_category.setdefault(row["category"], Counter())[row["level"]] += 1
    owners, questions = workpackages.needs_owner(db, opp_id), workpackages.open_questions(db, opp_id)
    # C-10: completeness, compliance and schedule come from the units' validated answers, not from the matches
    items = [a for r in reqs for a in work.get(r.req_id, [])]  # the work sent to the units (bid desk included)
    done = sum(a.status == "validated" for a in items)
    valid = {r.req_id: [a for a in work.get(r.req_id, []) if a.status == "validated" and a.compliance] for r in reqs}
    product = [valid[r.req_id] for r in reqs if (m := matches.get(r.req_id)) and m.units and valid[r.req_id]]
    share, threshold = (sum(_worst(v) in ("fully", "partly") for v in product) / len(product) if product else 0.0,
                        gng["compliance_threshold"])

    checks = ev["checks"]
    rules = {r["id"]: r for r in checks["rules"]}
    warns = [r["id"] for r in checks["rules"] if r["status"] == "warn"]
    auto = {  # criterion id -> (met?, detail) or (status, detail)
        "completeness": (bool(items) and done == len(items),
                         f"{done} of {len(items)} item(s) sent to the units have a validated answer." if items
                         else "Nothing has been sent to the units yet."),
        "compliance": ("unknown", "No validated answer to a product requirement yet.") if not product else
                      (share >= threshold, f"{share:.0%} of {len(product)} product requirement(s) with validated answers are "
                                           f"fully or partially compliant (threshold {threshold:.0%}, placeholder)."),
        "schedule": _schedule_criterion([r.req_id for r in reqs if r.category == "schedule"], valid),
        "scope_fit": (not checks["units_outside_scope"],
                      "Units outside the RFP's scope: " + ", ".join(checks["units_outside_scope"]) if checks["units_outside_scope"]
                      else f"Suggested units fit the layers in scope {checks['scope']['in_scope']}."),
        "all_matched": (not ev["unmatched"] and not owners,
                        f"{len(ev['unmatched'])} requirement(s) without a match; {len(owners)} product requirement(s) need an owner."
                        if ev["unmatched"] or owners else "Every requirement is routed."),
        "engineering_rules": (all(r["status"] != "fail" for r in rules.values()),
                              "Failing: " + ", ".join(i for i, r in rules.items() if r["status"] == "fail") if any(r["status"] == "fail" for r in rules.values())
                              else "No engineering rule fails."),
        "open_questions": (not warns and not ev["unanchored"] and not questions,
                           f"Rule warnings: {', '.join(warns) or 'none'}; requirements with source not verified: {len(ev['unanchored'])}; "
                           f"open questions: {len(questions)}."),
        "pending_acquisition": (rules.get("R-004", {}).get("status") != "warn", rules.get("R-004", {}).get("note", "")),
        "deviations": _deviations_criterion(ev["deviations"]),
        "capacity": _capacity_criterion(ev["workload"]),
    }
    criteria = []
    for c in gng["criteria"]:
        ok, detail = auto[c["id"]]
        criteria.append({**c, "status": ok if isinstance(ok, str) else "met" if ok else "not_met", "detail": detail})
    assessable = [c for c in criteria if c["status"] != "unknown"]
    met = sum(c["status"] == "met" for c in assessable)
    return {
        "rows": rows,
        "by_category": {cat: {lvl: n.get(lvl, 0) for lvl in ("fully", "partly", "not", "bid_desk")} for cat, n in by_category.items()},
        "assessment": {"items": len(items), "validated": done},
        "needs_owner": owners,
        "open_questions": len(questions),
        "criteria": criteria,
        "advice": (f"Advice from Layer 0: {met} of {len(assessable)} assessable criteria met; "
                   f"{len(criteria) - len(assessable)} not known yet. The bid manager decides."),
    }


def _schedule_criterion(schedule: list[str], valid: dict) -> tuple[str, str]:
    """C-10: met when every schedule requirement has a validated answer and none is non-compliant."""
    if not schedule:
        return "unknown", "The RFP states no schedule requirement."
    late = [i for i in schedule if valid[i] and _worst(valid[i]) == "not"]
    if late:
        return "not_met", f"Non-compliant: {', '.join(late)}."
    waiting = [i for i in schedule if not valid[i]]
    if waiting:
        return "unknown", f"{len(schedule) - len(waiting)} of {len(schedule)} schedule requirement(s) validated; waiting: {', '.join(waiting)}."
    return "met", f"All {len(schedule)} schedule requirement(s) validated, none non-compliant."


def _deviations_criterion(dev: dict) -> tuple[bool, str]:
    serious = [d for d in dev["rows"] if d["severity"] in ("high", "medium")]
    if not dev["checked"]:
        return True, "No data-sheet rating found to compare with a standard product."
    detail = ("; ".join(f"{d['field']}: RFP {d['rfp']} vs standard {d['standard']} ({d['product_id']}, {d['severity']}, {d['source']})"
                        for d in serious) or f"{dev['checked']} data-sheet ratings within the standard products.")
    return not serious, detail.rstrip(".") + ". Standards are placeholders."


def _capacity_criterion(load: dict) -> tuple[bool, str]:
    over = [r for r in load["rows"] if r["over"]]
    parts = [f"{r['bu']} {r['total']}/{r['capacity']}" + (f" (also in {', '.join(r['other_opportunities'])})" if r["other_opportunities"] else "")
             for r in load["rows"] if r["capacity"]]
    return not over, (("Over capacity: " if over else "Open work vs capacity: ") + ("; ".join(parts) if parts else "no unit work yet")
                      + ". Capacity is a placeholder.")


def record(db: Session, opp_id: str, kind: str, outcome: str, units: list[str], rationale: str, actor: str,
           criteria: list[dict] | None = None) -> Decision:
    if not opportunities.get(db, opp_id):
        raise LookupError(f"Bid {opp_id} not found.")
    if kind == "go_no_go" and not requirements.baseline(db, opp_id):
        raise ValueError("The requirement register is not frozen yet: read the RFP before deciding go or no-go (RFP step).")
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


def get(db: Session, decision_id: int) -> Decision | None:
    return db.get(Decision, decision_id)


def participating_units(db: Session, opp_id: str) -> list[str]:
    d = latest(db, opp_id, "participation")
    return d.units if d else []
