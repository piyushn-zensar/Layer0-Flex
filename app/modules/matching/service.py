"""Matching: requirement -> business unit(s), product, offering type, with evidence.  Owner: Atharv.

Public contract:
    match(db, opp_id, actor) -> dict                  propose a match for every approved requirement not yet decided
    for_opportunity(db, opp_id) -> dict[str, Match]   latest match per req_id, unless a person rejected it
    decide(db, match_id, action, actor)               action: accept | reject; LookupError if no such match
    set_manual(db, opp_id, req_id, bu, product_id, offering_type, actor) -> Match   a person's own choice
    suggested_units(db, opp_id) -> dict[str, list[str]]   bu -> req_ids (input to participation)
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.catalog import service as catalog
from app.modules.ingestion import service as ingestion
from app.modules.matching import agent
from app.modules.matching.models import Match
from app.modules.requirements import service as requirements

PRODUCT_CATEGORIES = {"technical", "compliance"}
MIN_SCORE = 0.08  # ponytail: starting guess; calibrate on real RFPs


def _retrieval_only(req, hits) -> dict:
    """Fallback when no model answer exists: top catalog hit for product items, else the bid manager."""
    top = next((h for h in hits if h["kind"] == "product"), None)
    if req.category not in PRODUCT_CATEGORIES or not top or top["score"] < MIN_SCORE:
        return {"bu": "", "product_id": "", "offering_type": "NONE", "confidence": 0.0,
                "rationale": "Not matched to a product; the bid manager answers it."}
    return {"bu": top["bu"], "product_id": top["id"], "offering_type": top["offering_type"],
            "confidence": top["score"], "rationale": f"Closest catalog entry {top['id']} (retrieval score {top['score']})."}


def match(db: Session, opp_id: str, actor: str) -> dict:
    """A re-run refreshes only proposals; accepted, manual and rejected matches are a person's decision (rule R4)."""
    decided = {req_id for req_id, m in _latest(db, opp_id).items() if m.status != "proposed"}
    reqs = [r for r in requirements.current(db, opp_id) if r.status == "approved" and r.req_id not in decided]
    method_count = defaultdict(int)
    layouts = {}
    for req in reqs:
        hits = catalog.search(req.quote, k=5)
        header = _header(req, layouts)
        # lines like "Apply an epoxy finish" name no equipment: add the products the page header points to
        seen = {h["id"] for h in hits}
        candidates = hits + [h for h in catalog.search(header, k=10) if h["kind"] == "product" and h["id"] not in seen][:2]
        try:
            proposal = agent.propose({"req_id": req.req_id, "category": req.category, "quote": req.quote,
                                      "header": header}, candidates)
            out, method = agent.checked(proposal, candidates), "agent"
            if out is None:  # the model named something that is not a candidate product
                out, method = _retrieval_only(req, hits), "retrieval_only"
                out["rationale"] = f"Model answer {proposal['product_id']!r} is not a candidate product. {out['rationale']}"
        except agent.LLMUnavailable:
            out, method = _retrieval_only(req, hits), "retrieval_only"
        m = Match(opportunity_id=opp_id, req_id=req.req_id, bu=out["bu"] or None, product_id=out["product_id"] or None,
                  offering_type=out["offering_type"], confidence=out["confidence"], rationale=out["rationale"],
                  evidence=candidates, method=method)
        db.add(m)
        method_count[method] += 1
        audit.record(db, actor, "proposed", "match", req.req_id, opp_id, bu=m.bu, product=m.product_id, method=method)
    db.commit()
    return {"matched": len(reqs), "kept": len(decided), **method_count}


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


def set_manual(db: Session, opp_id: str, req_id: str, bu: str | None, product_id: str | None,
               offering_type: str, actor: str) -> Match:
    m = Match(opportunity_id=opp_id, req_id=req_id, bu=bu, product_id=product_id, offering_type=offering_type,
              confidence=1.0, rationale=f"Set by {actor}.", method="manual", status="accepted", decided_by=actor)
    db.add(m)
    audit.record(db, actor, "manual", "match", req_id, opp_id, bu=bu, product=product_id)
    db.commit()
    return m


def suggested_units(db: Session, opp_id: str) -> dict[str, list[str]]:
    units = defaultdict(list)
    for req_id, m in for_opportunity(db, opp_id).items():
        if m.bu:
            units[m.bu].append(req_id)
    return dict(units)


if __name__ == "__main__":  # freeze the matcher's answers for an RFP (task A-03); commit data/llm_cache/match_requirement/
    # LLM_PROVIDER=azure .venv/Scripts/python -m app.modules.matching.service data/RFP/RFP-2023-20-Switchgear-Procurement-Final.pdf
    # Runs the real services on a throwaway database: cached reader answers -> approve all -> freeze -> match.
    # The opportunity is OPP-0001, so requirement IDs (part of the matcher prompt) match the demo's.
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
