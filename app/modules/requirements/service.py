"""Requirements: line items with exact sources, human review, frozen baseline.  Owner: Piyush.

Public contract:
    extract(db, opp_id, actor) -> dict           run the reader agent on the main document (drafts only)
    add(db, opp_id, document_id, quote, text, category, actor, section="", hint_page=None) -> Requirement
    current(db, opp_id, include_rejected=False) -> list[Requirement]   latest version of each line item
    get(db, req_id) -> Requirement | None        latest version
    review(db, req_id, action, actor, text=None, reason="")   action: approve | reject | edit
    freeze(db, opp_id, actor) -> Baseline        approved items become baseline N
    baseline(db, opp_id) -> Baseline | None      latest frozen baseline
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service as opportunities
from app.modules.requirements import agent, anchoring
from app.modules.requirements.models import Baseline, Requirement


def _next_req_id(db: Session, opp_id: str) -> str:
    prefix = f"REQ-{opp_id.split('-')[1]}-"
    last = db.scalar(select(func.max(Requirement.req_id)).where(Requirement.opportunity_id == opp_id))
    return f"{prefix}{(int(last.rsplit('-', 1)[1]) if last else 0) + 1:04d}"


def add(db: Session, opp_id: str, document_id: str, quote: str, text: str, category: str, actor: str,
        section: str = "", hint_page: int | None = None) -> Requirement:
    hit = anchoring.find(quote, ingestion.layout(document_id)["pages"], hint_page)
    req = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=document_id,
                      text=text, quote=quote, category=category, section=section, created_by=actor,
                      provenance="EXTRACTED" if hit else "UNANCHORED", **(hit or {}))
    db.add(req)
    audit.record(db, actor, "proposed", "requirement", req.req_id, opp_id, provenance=req.provenance)
    db.commit()
    return req


def extract(db: Session, opp_id: str, actor: str) -> dict:
    if baseline(db, opp_id):
        raise ValueError("Requirements are frozen; process changes as a delta (changes module).")
    doc = opportunities.main_document(db, opp_id)
    proposed, problems = agent.read(ingestion.layout(doc.id))
    for old in db.scalars(select(Requirement).where(Requirement.opportunity_id == opp_id,
                                                    Requirement.status == "proposed")):
        db.delete(old)  # drafts only: a re-run replaces unreviewed proposals
    db.commit()
    for item in proposed:
        add(db, opp_id, doc.id, item["quote"], item["text"], item["category"], f"reader agent ({actor})",
            item["section"], item["page"])
    opportunities.set_status(db, opp_id, "review", actor)
    return {"proposed": len(proposed), "problems": problems}


def current(db: Session, opp_id: str, include_rejected: bool = False) -> list[Requirement]:
    latest = (select(Requirement.req_id, func.max(Requirement.version).label("v"))
              .where(Requirement.opportunity_id == opp_id).group_by(Requirement.req_id).subquery())
    rows = db.scalars(select(Requirement).join(latest, (Requirement.req_id == latest.c.req_id)
                                               & (Requirement.version == latest.c.v)).order_by(Requirement.req_id))
    return [r for r in rows if include_rejected or r.status != "rejected"]


def get(db: Session, req_id: str) -> Requirement | None:
    return db.scalar(select(Requirement).where(Requirement.req_id == req_id)
                     .order_by(Requirement.version.desc()).limit(1))


def review(db: Session, req_id: str, action: str, actor: str, text: str | None = None, reason: str = "") -> None:
    req = get(db, req_id)
    if req.baseline is not None:
        raise ValueError(f"{req_id} is frozen in baseline {req.baseline}; change it through the changes module.")
    before = {"status": req.status, "text": req.text}
    if action == "edit" and text:
        req.text = text
    elif action in ("approve", "reject"):
        req.status = {"approve": "approved", "reject": "rejected"}[action]
    audit.record(db, actor, action, "requirement", req_id, req.opportunity_id, before=before,
                 after={"status": req.status, "text": req.text}, reason=reason)
    db.commit()


def freeze(db: Session, opp_id: str, actor: str) -> Baseline:
    items = [r for r in current(db, opp_id) if r.status == "approved" and r.baseline is None]
    number = (baseline(db, opp_id).number if baseline(db, opp_id) else 0) + 1
    for r in items:
        r.baseline = number
    b = Baseline(opportunity_id=opp_id, number=number, count=len(items), frozen_by=actor)
    db.add(b)
    audit.record(db, actor, "frozen", "baseline", str(number), opp_id, count=len(items))
    db.commit()
    opportunities.set_status(db, opp_id, "frozen", actor)
    return b


def baseline(db: Session, opp_id: str) -> Baseline | None:
    return db.scalar(select(Baseline).where(Baseline.opportunity_id == opp_id)
                     .order_by(Baseline.number.desc()).limit(1))
