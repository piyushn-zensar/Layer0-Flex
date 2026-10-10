"""Matching: requirement -> business unit(s), product, offering type, with evidence.  Owner: Atharv.

Public contract:
    match(db, opp_id, actor, req_ids=None) -> dict    propose a match for every approved requirement not yet decided;
        req_ids: only these (the changes module re-matches only what a change added or modified, so the frozen
        page batches of the untouched requirements stay as they were)
    for_opportunity(db, opp_id) -> dict[str, Match]   latest match per req_id, unless a person rejected it.
        Match.units lists every unit [{bu, product_id, offering_type}], main unit first; Match.bu, .product_id
        and .offering_type repeat the main unit (None / "NONE" when the bid manager answers it).
    decide(db, match_id, action, actor)               action: accept | reject; LookupError if no such match
    set_manual(db, opp_id, req_id, units, actor) -> Match   a person's own choice: units = [{product_id,
        offering_type}] (empty = bid manager); unit taken from the product. LookupError: no such requirement in
        the opportunity; ValueError: unknown or inactive product, or bad offering type
    suggested_units(db, opp_id) -> dict[str, list[str]]   bu -> req_ids, every listed unit (input to participation)
    evidence_checks(db, opp_id) -> dict   scope (M3), tier flags (M4), rules R-001..R-004 (M5), LV solver (M13) and
        units suggested outside the scope, over the frozen approved requirements (see checks.py)
"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.matching import agent, checks
from app.modules.matching.models import OFFERING_TYPES, Match
from app.modules.requirements import service as requirements

PRODUCT_CATEGORIES = {"technical", "compliance"}
MIN_SCORE = 0.08  # ponytail: starting guess; calibrate on real RFPs


def _retrieval_only(req, hits) -> dict:
    """Fallback when no model answer exists: top catalog hit for product items, else the bid manager."""
    top = next((h for h in hits if h["kind"] == "product"), None)
    if req.category not in PRODUCT_CATEGORIES or not top or top["score"] < MIN_SCORE:
        return {"units": [], "confidence": 0.0, "rationale": "Not matched to a product; the bid manager answers it."}
    return {"units": [{"bu": top["bu"], "product_id": top["id"], "offering_type": top["offering_type"]}],
            "confidence": top["score"], "rationale": f"Closest catalog entry {top['id']} (retrieval score {top['score']})."}


def _row(opp_id: str, req_id: str, units: list[dict], **fields) -> Match:
    """A match row; bu / product_id / offering_type repeat the main (first) unit."""
    main = units[0] if units else {"bu": None, "product_id": None, "offering_type": "NONE"}
    return Match(opportunity_id=opp_id, req_id=req_id, units=units, bu=main["bu"], product_id=main["product_id"],
                 offering_type=main["offering_type"], **fields)


BATCH = 15           # requirements per matcher call (one page; a dense page is split)
PARALLEL_CALLS = 4


def match(db: Session, opp_id: str, actor: str, req_ids: list[str] | None = None) -> dict:
    """A re-run refreshes only proposals; accepted, manual and rejected matches are a person's decision (rule R4).

    Token cuts (P-18): requirements outside PRODUCT_CATEGORIES go to the bid manager by rule, with no model call;
    the rest are sent one page at a time with the whole catalog in the fixed part of the prompt."""
    decided = {req_id for req_id, m in _latest(db, opp_id).items() if m.status != "proposed"}
    reqs = [r for r in requirements.current(db, opp_id) if r.status == "approved" and r.req_id not in decided
            and (req_ids is None or r.req_id in req_ids)]
    evidence = dict(zip((r.req_id for r in reqs), catalog.search_many([r.quote for r in reqs], k=5)))
    products, past = catalog.products(), catalog.past_responses()
    candidates = [{"kind": "product", "id": p["id"], "bu": p["bu"]} for p in products]
    layouts: dict = {}
    results: dict[str, tuple[dict, str]] = {}
    batches = []
    for req in reqs:
        if req.category not in PRODUCT_CATEGORIES:
            results[req.req_id] = ({"units": [], "confidence": 1.0, "rationale":
                                    f"A {req.category} requirement, not a product item: the bid manager answers it."}, "rule")
        elif batches and batches[-1][0] == (req.document_id, req.page) and len(batches[-1][1]) < BATCH:
            batches[-1][1].append(req)
        else:
            batches.append(((req.document_id, req.page), [req]))

    def ask(batch):
        (_, page), items = batch
        header = _header(items[0], layouts)
        try:
            return items, agent.propose_page(header, [{"category": r.category, "quote": r.quote} for r in items],
                                             products, past)
        except agent.LLMUnavailable:
            return items, [None] * len(items)

    for r in reqs:  # load layouts once, before the threads read them
        if r.page is not None:
            _header(r, layouts)
    with ThreadPoolExecutor(PARALLEL_CALLS) as pool:
        for items, answers in pool.map(ask, batches):
            for req, answer in zip(items, answers):
                out = agent.checked(answer, candidates) if answer else None
                if out is not None:
                    results[req.req_id] = (out, "agent")
                else:
                    fallback = _retrieval_only(req, evidence[req.req_id])
                    if answer:  # the model named only things that are not catalog products
                        fallback["rationale"] = f"Model answer {[u['product_id'] for u in answer['units']]} has no catalog product. {fallback['rationale']}"
                    results[req.req_id] = (fallback, "retrieval_only")
    method_count = defaultdict(int)
    for req in reqs:
        out, method = results[req.req_id]
        m = _row(opp_id, req.req_id, out["units"], confidence=out["confidence"], rationale=out["rationale"],
                 evidence=evidence[req.req_id], method=method)
        db.add(m)
        method_count[method] += 1
        audit.record(db, actor, "proposed", "match", req.req_id, opp_id, units=m.units, method=method)
    db.commit()
    return {"matched": len(reqs), "kept": len(decided), "calls": len(batches), **method_count}


def _header(req, layouts: dict) -> str:
    """Header block of the requirement's source page, from the frozen layout ("" when unanchored)."""
    if req.page is None:
        return ""
    if req.document_id not in layouts:
        layouts[req.document_id] = ingestion.layout(req.document_id)["pages"]
    return agent.page_header(layouts[req.document_id][req.page - 1])


def _latest(db: Session, opp_id: str) -> dict[str, Match]:
    rows = db.scalars(select(Match).where(Match.opportunity_id == opp_id).order_by(Match.id))
    return {m.req_id: m for m in rows}  # later rows win


def for_opportunity(db: Session, opp_id: str) -> dict[str, Match]:
    return {req_id: m for req_id, m in _latest(db, opp_id).items() if m.status != "rejected"}


def decide(db: Session, match_id: int, action: str, actor: str) -> None:
    m = db.get(Match, match_id)
    if not m:
        raise LookupError(f"Match {match_id} not found.")
    m.status, m.decided_by = {"accept": "accepted", "reject": "rejected"}[action], actor
    audit.record(db, actor, action, "match", m.req_id, m.opportunity_id, bu=m.bu, product=m.product_id)
    db.commit()


def set_manual(db: Session, opp_id: str, req_id: str, units: list[dict], actor: str) -> Match:
    req = requirements.get(db, req_id)
    if not req or req.opportunity_id != opp_id:
        raise LookupError(f"{req_id} is not a requirement of {opp_id}.")
    active = {u["code"] for u in catalog.units()}
    chosen = []
    for u in units:
        p = catalog.product(u["product_id"])
        if not p or p["bu"] not in active:
            raise ValueError(f"{u['product_id']} is not a product of an active business unit.")
        if u["offering_type"] not in OFFERING_TYPES or u["offering_type"] == "NONE":
            raise ValueError(f"{u['offering_type']} is not an offering type.")
        if all(c["product_id"] != p["id"] for c in chosen):
            chosen.append({"bu": p["bu"], "product_id": p["id"], "offering_type": u["offering_type"]})
    m = _row(opp_id, req_id, chosen, confidence=1.0, rationale=f"Set by {actor}.", method="manual",
             status="accepted", decided_by=actor)
    db.add(m)
    audit.record(db, actor, "manual", "match", req_id, opp_id, units=chosen)
    db.commit()
    return m


def suggested_units(db: Session, opp_id: str) -> dict[str, list[str]]:
    units = defaultdict(list)
    for req_id, m in for_opportunity(db, opp_id).items():
        for bu in dict.fromkeys(u["bu"] for u in m.units):  # each unit once per requirement
            units[bu].append(req_id)
    return dict(units)


def evidence_checks(db: Session, opp_id: str) -> dict:
    reqs = [{"req_id": r.req_id, "quote": r.quote} for r in requirements.current(db, opp_id)
            if r.status == "approved" and r.baseline is not None]
    ids = {r["req_id"] for r in reqs}
    matched = {req_id: m.units for req_id, m in for_opportunity(db, opp_id).items() if req_id in ids and m.units}
    kb, eng = catalog.layers(), catalog.engineering_rules()
    scope, facts = checks.scope(reqs, kb), checks.facts(reqs)
    unit_layers = {u: {l["n"] for l in kb["layers"] if u in l["units"]} for u in kb["unit_tiers"]}
    outside = defaultdict(list)  # a unit suggested although nothing in the RFP points to its layers
    for req_id, units in matched.items():
        for bu in {u["bu"] for u in units}:
            if not unit_layers.get(bu, set()) & set(scope["in_scope"]):
                outside[bu].append(req_id)
    return {"requirements_checked": len(reqs), "scope": scope, "facts": facts,
            "units_outside_scope": dict(outside), "tier_flags": checks.tier_flags(reqs, matched, kb),
            "rules": checks.rules(facts, scope["in_scope"], matched, kb, eng),
            "solver": checks.solve(facts, scope["in_scope"], eng)}


if __name__ == "__main__":  # freeze the matcher's answers for an RFP (task A-03); commit data/llm_cache/match_requirement/
    # LLM_PROVIDER=azure .venv/Scripts/python -m app.modules.matching.service data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf
    # Runs the real services on a throwaway database: cached reader answers -> approve all -> freeze -> match.
    # The opportunity is OPP-0001, so requirement IDs (part of the matcher prompt) match an OPP-0001 read from the
    # same RFP by the real reader (P-08), not the 13 hand-picked seed items. Layout and page files still go to
    # data/store (gitignored), as for any upload.
    import sys
    import tempfile
    from collections import Counter
    from pathlib import Path

    from sqlalchemy import create_engine

    from app.core import config
    from app.core.db import Base
    from app.main import app  # noqa: F401  (registers every module's tables)
    from app.modules.opportunities import service as opportunities

    who = "matcher freeze"
    engine = create_engine(f"sqlite:///{Path(tempfile.mkdtemp(), 'freeze.db').as_posix()}")
    Base.metadata.create_all(engine)
    for arg in sys.argv[1:]:
        pdf = Path(arg)
        with Session(engine) as db:
            opp = opportunities.create(db, pdf.stem, "", "", who)
            doc = opportunities.add_document(db, opp.id, pdf.name, pdf.read_bytes(), "main", who)
            ingestion.ingest(db, doc.id)
            print(f"{arg}: provider={config.LLM_PROVIDER} model={config.LLM_MODEL}", flush=True)
            print("reader:", requirements.extract(db, opp.id, who), flush=True)
            for r in requirements.current(db, opp.id):
                requirements.review(db, r.req_id, "approve", who)
            requirements.freeze(db, opp.id, who)
            print("matcher:", match(db, opp.id, "matching agent"))
            ms = for_opportunity(db, opp.id).values()
            print("by unit:", Counter(m.bu or "BID" for m in ms))
            print("by offering type:", Counter(m.offering_type for m in ms))
            print("by product:", Counter(m.product_id for m in ms if m.product_id).most_common())
            print("by method:", Counter(m.method for m in ms))
            print("several units:", sum(len({u["bu"] for u in m.units}) > 1 for m in ms))
