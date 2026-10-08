"""Requirements: line items with exact sources, human review, frozen baseline.  Owner: Piyush.

Public contract:
    extract(db, opp_id, actor) -> dict           run the reader agent on the main document (drafts only)
    add(db, opp_id, document_id, quote, text, category, actor, section="", hint_page=None) -> Requirement
    current(db, opp_id, include_inactive=False) -> list[Requirement]   latest version of each active line item
                                                 (inactive = rejected, or replaced by a split / merge)
    get(db, req_id) -> Requirement | None        latest version
    review(db, req_id, action, actor, text=None, reason="", category=None)   action: approve | reject | edit
    split(db, req_id, parts, actor, reason="") -> list[Requirement]   parts: [{"quote", "text"}], >= 2
    merge(db, opp_id, req_ids, text, actor, reason="") -> Requirement  >= 2 line items into one
    add_missed(db, opp_id, quote, text, category, actor, page=None) -> Requirement   a person adds what the agent missed
    freeze(db, opp_id, actor) -> Baseline        approved items become baseline N; every item must be decided first
    baseline(db, opp_id) -> Baseline | None      latest frozen baseline
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service as opportunities
from app.modules.requirements import agent, anchoring
from app.modules.requirements.models import CATEGORIES, Baseline, Requirement

INACTIVE = {"rejected", "split", "merged"}


def _next_req_id(db: Session, opp_id: str) -> str:
    prefix = f"REQ-{opp_id.split('-')[1]}-"
    last = db.scalar(select(func.max(Requirement.req_id)).where(Requirement.opportunity_id == opp_id))
    return f"{prefix}{(int(last.rsplit('-', 1)[1]) if last else 0) + 1:04d}"


def add(db: Session, opp_id: str, document_id: str, quote: str, text: str, category: str, actor: str,
        section: str = "", hint_page: int | None = None, derived_from: list[str] | None = None,
        commit: bool = True) -> Requirement:
    hit = anchoring.find(quote, ingestion.layout(document_id)["pages"], hint_page)
    req = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=document_id,
                      text=text, quote=quote, category=category, section=section, created_by=actor,
                      derived_from=derived_from or [], provenance="EXTRACTED" if hit else "UNANCHORED", **(hit or {}))
    db.add(req)
    db.flush()  # the next _next_req_id sees this one
    audit.record(db, actor, "proposed", "requirement", req.req_id, opp_id, provenance=req.provenance,
                 derived_from=req.derived_from)
    if commit:
        db.commit()
    return req


def _draft(db: Session, req_id: str) -> Requirement:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    if req.baseline is not None:
        raise ValueError(f"{req_id} is frozen in baseline {req.baseline}; change it through the changes module.")
    if req.status in INACTIVE:
        raise ValueError(f"{req_id} is {req.status}; it can no longer be changed.")
    return req


def split(db: Session, req_id: str, parts: list[dict], actor: str, reason: str = "") -> list[Requirement]:
    """One line item that holds several obligations becomes one item per part. Each part is anchored again."""
    req = _draft(db, req_id)
    parts = [p for p in parts if p.get("quote", "").strip()]
    if len(parts) < 2:
        raise ValueError("A split needs at least two parts.")
    children = [add(db, req.opportunity_id, req.document_id, p["quote"], p.get("text") or p["quote"][:200],
                    req.category, actor, req.section, req.page, [req.req_id], commit=False) for p in parts]
    req.status = "split"
    audit.record(db, actor, "split", "requirement", req_id, req.opportunity_id,
                 into=[c.req_id for c in children], reason=reason)
    db.commit()
    return children


def merge(db: Session, opp_id: str, req_ids: list[str], text: str, actor: str, reason: str = "") -> Requirement:
    """Several line items that are really one obligation become one. Sources are kept (all boxes, joined quote)."""
    reqs = [_draft(db, r) for r in dict.fromkeys(req_ids)]
    if len(reqs) < 2:
        raise ValueError("A merge needs at least two line items.")
    if any(r.opportunity_id != opp_id for r in reqs):
        raise ValueError("Line items from another opportunity cannot be merged.")
    reqs.sort(key=lambda r: (r.page or 0, r.line_start or 0))
    first, same_page = reqs[0], len({r.page for r in reqs}) == 1
    merged = Requirement(
        req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=first.document_id, text=text,
        quote=" … ".join(r.quote for r in reqs), category=first.category, section=first.section, created_by=actor,
        derived_from=[r.req_id for r in reqs], page=first.page,
        line_start=first.line_start, line_end=max(r.line_end or 0 for r in reqs) if same_page else first.line_end,
        bboxes=[b for r in reqs if r.page == first.page for b in r.bboxes],
        provenance="EXTRACTED" if all(r.provenance == "EXTRACTED" for r in reqs) else "UNANCHORED")
    db.add(merged)
    for r in reqs:
        r.status = "merged"
    db.flush()
    audit.record(db, actor, "merged", "requirement", merged.req_id, opp_id,
                 merged_from=[r.req_id for r in reqs], reason=reason)
    db.commit()
    return merged


def add_missed(db: Session, opp_id: str, quote: str, text: str, category: str, actor: str,
               page: int | None = None) -> Requirement:
    if baseline(db, opp_id):
        raise ValueError("Requirements are frozen; add new ones through the changes module.")
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    doc = opportunities.main_document(db, opp_id)
    return add(db, opp_id, doc.id, quote, text or quote[:200], category, actor, hint_page=page)


def extract(db: Session, opp_id: str, actor: str) -> dict:
    if baseline(db, opp_id):
        raise ValueError("Requirements are frozen; process changes as a delta (changes module).")
    doc = opportunities.main_document(db, opp_id)
    proposed, problems = agent.read(ingestion.layout(doc.id))
    for old in db.scalars(select(Requirement).where(Requirement.opportunity_id == opp_id,
                                                    Requirement.status == "proposed",
                                                    Requirement.created_by.startswith("reader agent"))):
        db.delete(old)  # a re-run replaces the agent's unreviewed proposals; people's additions stay
    db.commit()
    for item in proposed:
        add(db, opp_id, doc.id, item["quote"], item["text"], item["category"], f"reader agent ({actor})",
            item["section"], item["page"])
    opportunities.set_status(db, opp_id, "review", actor)
    return {"proposed": len(proposed), "problems": problems}


def current(db: Session, opp_id: str, include_inactive: bool = False) -> list[Requirement]:
    latest = (select(Requirement.req_id, func.max(Requirement.version).label("v"))
              .where(Requirement.opportunity_id == opp_id).group_by(Requirement.req_id).subquery())
    rows = db.scalars(select(Requirement).join(latest, (Requirement.req_id == latest.c.req_id)
                                               & (Requirement.version == latest.c.v)).order_by(Requirement.req_id))
    return [r for r in rows if include_inactive or r.status not in INACTIVE]


def get(db: Session, req_id: str) -> Requirement | None:
    return db.scalar(select(Requirement).where(Requirement.req_id == req_id)
                     .order_by(Requirement.version.desc()).limit(1))


def review(db: Session, req_id: str, action: str, actor: str, text: str | None = None, reason: str = "",
           category: str | None = None) -> None:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    if req.baseline is not None:
        raise ValueError(f"{req_id} is frozen in baseline {req.baseline}; change it through the changes module.")
    if req.status in ("split", "merged"):
        raise ValueError(f"{req_id} is {req.status}; review its replacement instead.")
    before = {"status": req.status, "text": req.text, "category": req.category}
    if action == "edit":
        if category and category not in CATEGORIES:
            raise ValueError(f"Unknown category {category!r}.")
        req.text, req.category = (text or req.text), (category or req.category)
    elif action in ("approve", "reject"):
        req.status = {"approve": "approved", "reject": "rejected"}[action]
    else:
        raise ValueError(f"Unknown action {action!r}.")
    audit.record(db, actor, action, "requirement", req_id, req.opportunity_id, before=before,
                 after={"status": req.status, "text": req.text, "category": req.category}, reason=reason)
    db.commit()


def freeze(db: Session, opp_id: str, actor: str) -> Baseline:
    undecided = [r.req_id for r in current(db, opp_id) if r.status == "proposed"]
    if undecided:
        raise ValueError(f"{len(undecided)} line items still need approve or reject before freezing.")
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
