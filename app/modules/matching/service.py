"""Matching: requirement -> business unit(s), product, offering type, with evidence.  Owner: Atharv.

Public contract:
    match(db, opp_id, actor) -> dict                  propose a match for every baseline requirement
    for_opportunity(db, opp_id) -> dict[str, Match]   latest match per req_id
    decide(db, match_id, action, actor)               action: accept | reject
    set_manual(db, opp_id, req_id, bu, product_id, offering_type, actor) -> Match   a person's own choice
    suggested_units(db, opp_id) -> dict[str, list[str]]   bu -> req_ids (input to participation)
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.catalog import service as catalog
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
    reqs = [r for r in requirements.current(db, opp_id) if r.status == "approved"]
    method_count = defaultdict(int)
    for req in reqs:
        hits = catalog.search(req.quote, k=5)
        try:
            out, method = agent.propose({"req_id": req.req_id, "category": req.category, "quote": req.quote}, hits), "agent"
        except agent.LLMUnavailable:
            out, method = _retrieval_only(req, hits), "retrieval_only"
        m = Match(opportunity_id=opp_id, req_id=req.req_id, bu=out["bu"] or None, product_id=out["product_id"] or None,
                  offering_type=out["offering_type"], confidence=out["confidence"], rationale=out["rationale"],
                  evidence=hits, method=method)
        db.add(m)
        method_count[method] += 1
        audit.record(db, actor, "proposed", "match", req.req_id, opp_id, bu=m.bu, product=m.product_id, method=method)
    db.commit()
    return {"matched": len(reqs), **method_count}


def for_opportunity(db: Session, opp_id: str) -> dict[str, Match]:
    rows = db.scalars(select(Match).where(Match.opportunity_id == opp_id, Match.status != "rejected").order_by(Match.id))
    return {m.req_id: m for m in rows}  # later rows win


def decide(db: Session, match_id: int, action: str, actor: str) -> None:
    m = db.get(Match, match_id)
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
