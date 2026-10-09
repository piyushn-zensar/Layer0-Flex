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
    freeze(db, opp_id, actor) -> Baseline        approved items become baseline 1; needs a read main RFP, every item
                                                 decided and at least one approved; once only (later: changes module)
Every write refuses once the opportunity has a baseline, and LookupError for an unknown opportunity or item.
Requirement IDs are never reused: the next number is taken over every ID ever issued, including discarded drafts.
    baseline(db, opp_id) -> Baseline | None      latest frozen baseline
    history(db, req_id) -> dict                  every version (who, when, text, category) and every event; LookupError
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.audit import AuditEvent
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service as opportunities
from app.modules.requirements import agent, anchoring
from app.modules.requirements.models import CATEGORIES, Baseline, Requirement

INACTIVE = {"rejected", "split", "merged"}


def _next_req_id(db: Session, opp_id: str) -> str:
    """Highest number ever issued for this opportunity + 1. Discarded drafts live on in the append-only audit log,
    so their IDs are never handed out again (a unit's answer can never land on a different requirement)."""
    prefix = f"REQ-{opp_id.split('-')[1]}-"
    issued = set(db.scalars(select(Requirement.req_id).where(Requirement.opportunity_id == opp_id)))
    issued |= set(db.scalars(select(AuditEvent.entity_id).where(AuditEvent.opportunity_id == opp_id,
                                                                AuditEvent.entity == "requirement")))
    last = max((int(i.rsplit("-", 1)[1]) for i in issued if i.startswith(prefix)), default=0)
    return f"{prefix}{last + 1:04d}"


def _writable(db: Session, opp_id: str) -> None:
    opportunities.require(db, opp_id)
    b = baseline(db, opp_id)
    if b:
        raise ValueError(f"Requirements are frozen in baseline {b.number}; later changes go through the changes module.")


def add(db: Session, opp_id: str, document_id: str, quote: str, text: str, category: str, actor: str,
        section: str = "", hint_page: int | None = None, derived_from: list[str] | None = None,
        commit: bool = True, pages: list[dict] | None = None) -> Requirement:
    if not quote.strip():
        raise ValueError("A requirement needs a quote copied from the RFP.")
    hit = anchoring.find(quote, pages if pages is not None else ingestion.layout(document_id)["pages"], hint_page)
    req = Requirement(req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=document_id,
                      text=text, quote=quote, category=category, section=section, created_by=actor,
                      derived_from=derived_from or [], provenance="EXTRACTED" if hit else "UNANCHORED", **(hit or {}))
    db.add(req)
    db.flush()  # the next _next_req_id sees this one
    audit.record(db, actor, "proposed", "requirement", req.req_id, opp_id, provenance=req.provenance,
                 derived_from=req.derived_from, text=req.text, category=req.category, quote=req.quote)
    if commit:
        db.commit()
    return req


def _draft(db: Session, req_id: str) -> Requirement:
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    _writable(db, req.opportunity_id)
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
    if not text.strip():
        raise ValueError("Give the merged requirement a short text.")
    reqs = [_draft(db, r) for r in dict.fromkeys(req_ids)]
    if len(reqs) < 2:
        raise ValueError("A merge needs at least two line items.")
    if any(r.opportunity_id != opp_id for r in reqs):
        raise ValueError("Line items from another opportunity cannot be merged.")
    if len({r.page for r in reqs}) > 1:
        # ponytail: one requirement = one page, so its highlight is complete; multi-page anchors if ever needed
        raise ValueError("Only line items on the same page can be merged; keep cross-page items separate.")
    reqs.sort(key=lambda r: r.line_start or 0)
    first = reqs[0]
    merged = Requirement(
        req_id=_next_req_id(db, opp_id), opportunity_id=opp_id, document_id=first.document_id, text=text.strip(),
        quote=" … ".join(r.quote for r in reqs), category=first.category, section=first.section, created_by=actor,
        derived_from=[r.req_id for r in reqs], page=first.page,
        line_start=first.line_start, line_end=max(r.line_end or 0 for r in reqs),
        bboxes=[b for r in reqs for b in r.bboxes],
        provenance="EXTRACTED" if all(r.provenance == "EXTRACTED" for r in reqs) else "UNANCHORED")
    db.add(merged)
    for r in reqs:
        r.status = "merged"
    db.flush()
    audit.record(db, actor, "merged", "requirement", merged.req_id, opp_id,
                 merged_from=[r.req_id for r in reqs], reason=reason)
    for r in reqs:  # the originals' own history shows where they went
        audit.record(db, actor, "merged_into", "requirement", r.req_id, opp_id, into=merged.req_id, reason=reason)
    db.commit()
    return merged


def add_missed(db: Session, opp_id: str, quote: str, text: str, category: str, actor: str,
               page: int | None = None) -> Requirement:
    _writable(db, opp_id)
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}.")
    doc = _read_main_document(db, opp_id)
    return add(db, opp_id, doc.id, quote, (text or quote).strip()[:200], category, actor, hint_page=page)


def _read_main_document(db: Session, opp_id: str):
    doc = opportunities.main_document(db, opp_id)
    if doc is None or doc.status != "ingested":
        raise ValueError("Upload the main RFP and wait until it has been read.")
    return doc


def extract(db: Session, opp_id: str, actor: str) -> dict:
    _writable(db, opp_id)
    doc = _read_main_document(db, opp_id)
    reviewed = db.scalar(select(func.count()).select_from(AuditEvent).where(
        AuditEvent.opportunity_id == opp_id, AuditEvent.entity == "requirement",
        AuditEvent.action.in_(["approve", "reject", "edit", "split", "merged"])))
    if reviewed:
        raise ValueError(f"Review has started ({reviewed} review actions); re-reading would lose that work. "
                         "Add what is missing with 'Add a requirement' instead.")
    layout = ingestion.layout(doc.id)
    proposed, problems = agent.read(layout)
    for old in db.scalars(select(Requirement).where(Requirement.opportunity_id == opp_id,
                                                    Requirement.status == "proposed",
                                                    Requirement.created_by.startswith("reader agent"))):
        audit.record(db, actor, "discarded", "requirement", old.req_id, opp_id, reason="re-read replaced the draft")
        db.delete(old)  # a re-run replaces the agent's unreviewed proposals; people's additions stay
    db.commit()
    for item in proposed:
        add(db, opp_id, doc.id, item["quote"], item["text"], item["category"], f"reader agent ({actor})",
            item["section"], item["page"], commit=False, pages=layout["pages"])
    db.commit()
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
    _writable(db, req.opportunity_id)
    if req.status in ("split", "merged"):
        raise ValueError(f"{req_id} is {req.status}; review its replacement instead.")
    before = {"status": req.status, "text": req.text, "category": req.category}
    if action == "edit":
        if category and category not in CATEGORIES:
            raise ValueError(f"Unknown category {category!r}.")
        req.text, req.category = ((text or "").strip() or req.text), (category or req.category)
    elif action in ("approve", "reject"):
        req.status = {"approve": "approved", "reject": "rejected"}[action]
    else:
        raise ValueError(f"Unknown action {action!r}.")
    audit.record(db, actor, action, "requirement", req_id, req.opportunity_id, before=before,
                 after={"status": req.status, "text": req.text, "category": req.category}, reason=reason)
    db.commit()


def freeze(db: Session, opp_id: str, actor: str) -> Baseline:
    _writable(db, opp_id)
    _read_main_document(db, opp_id)
    undecided = [r.req_id for r in current(db, opp_id) if r.status == "proposed"]
    if undecided:
        raise ValueError(f"{len(undecided)} line items still need approve or reject before freezing.")
    items = [r for r in current(db, opp_id) if r.status == "approved"]
    if not items:
        raise ValueError("Nothing is approved; a baseline needs at least one requirement.")
    number = 1
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


def history(db: Session, req_id: str) -> dict:
    """The change history of one line item, rebuilt from the append-only audit log (it is the source of truth).

    versions: the original wording, then one entry per edit that changed text or category.
    events:   everything that happened to it (proposed, edits, approve / reject, split, merge, freeze).
    """
    req = get(db, req_id)
    if req is None:
        raise LookupError(f"{req_id} not found.")
    events = list(db.scalars(select(AuditEvent).where(
        AuditEvent.opportunity_id == req.opportunity_id, AuditEvent.entity == "requirement",
        AuditEvent.entity_id == req_id).order_by(AuditEvent.id)))
    frozen = db.scalar(select(AuditEvent).where(AuditEvent.opportunity_id == req.opportunity_id,
                                                AuditEvent.entity == "baseline").order_by(AuditEvent.id).limit(1))
    if frozen and req.baseline is not None:
        events.append(frozen)

    def wording(d: dict) -> dict:
        return {"text": d.get("text"), "category": d.get("category")}

    edits = [e for e in events if e.action == "edit" and wording(e.data.get("before", {})) != wording(e.data.get("after", {}))]
    proposed = next((e for e in events if e.action == "proposed"), None)
    if proposed and "text" in proposed.data:
        first = wording(proposed.data)
    elif edits:  # line items read before 9 Oct: the first edit's "before" is the original wording
        first = wording(edits[0].data["before"])
    else:
        first = {"text": req.text, "category": req.category}
    versions = [{"n": 1, "at": proposed.at if proposed else req.created_at, "by": proposed.actor if proposed else req.created_by,
                 "label": "original", **first}]
    for e in edits:
        versions.append({"n": len(versions) + 1, "at": e.at, "by": e.actor, "label": "edited",
                         "reason": e.data.get("reason", ""), **wording(e.data["after"])})
    return {"req_id": req_id, "quote": req.quote, "source": req.source, "derived_from": req.derived_from,
            "versions": versions,
            "events": [{"at": e.at, "by": e.actor, "action": e.action,
                        "details": {k: v for k, v in e.data.items() if k not in ("text", "quote", "before", "after")}}
                       for e in events]}
