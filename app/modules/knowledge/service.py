"""Reviewed examples (P-36, C-29 points 3 and 6; replaces the A-11 queue): people nominate a requirement, a validated
answer, a decision rationale or an extraction correction from a bid, with what it teaches (example type), its
conditions and its limits; a qualified reviewer approves or rejects it. Approved items are reusable knowledge: they
join the long-term retrieval index (catalog) and the reviewed-example evidence (evidence()). Nothing becomes
reusable without a person's approval, and illustrative material is never verified evidence.  Owner: Piyush (iteration 3).

Who reviews (item level, qualified specialists): an item of a unit (a unit's answer) by that unit's product manager or
design engineer; a bid-level item (requirement, decision, correction) by the bid manager.

Public contract:
    nominate(db, kind, ref, actor, note="", example_type="other", conditions="", limits="") -> KbItem
        kind: requirement (ref = req_id) | response (ref = assignment id, validated answers only) | decision (ref =
        decision id) | correction (ref = req_id of a requirement whose reading was corrected). LookupError: unknown
        source; ValueError: not validated, not corrected, or already queued or approved. send() = nominate()
    items(db, status=None, user=None) -> list[KbItem]      newest first; with user: only the items that user may review
    for_opportunity(db, opp_id) -> dict[str, str]         "<kind>:<ref>" -> status, for the state of the buttons
    review(db, kb_id, approve, note, user, response=None) -> KbItem   user: token claims (name, role, bu); only queued
        items; a rejection needs a note; the reviewer may tidy the response; approving a new version retires the old
    revise(db, kb_id, actor, **fields) -> KbItem           a new queued version of an approved item (fields: response,
        example_type, conditions, limits, note)
    learned(db) -> list[dict]                              approved, non-illustrative items for the long-term index
    may_review(item, user) -> bool

Knowledge sources (P-35, C-29; implemented in sources.py, re-exported here):
    register(db, path, actor, collection, title, publisher, revision, scope, permissions, url, opp_id, file_name)
        -> (KbSource, existing)                         a draft read into passages; a known document instance is returned
    sources(db, collection=None, status=None), get(db, ks_id), source_passages(db, ks_id), counts(db)
    review_source(db, ks_id, approve, note, actor, role)  document-level review by the collection's REVIEWERS
    annotate(db, ks_id, actor) -> int                   model annotations beside each passage (frozen answers)
    evidence(db, collections=None, opp_id=None)         published passages and approved reviewed examples, with
                                                        citations; bid evidence only for its bid
    register_references(db)                             the public references in data/references/sources.json
    register_product_documents(db)                      P-58: the supplied product documents as draft product evidence

Retrieval and assessment records (P-37 part 1; retrieval.py, re-exported):
    retrieve(db, task, query, opp_id=None, k=None) -> list[dict]   evidence for a task profile, each with "citation"
    reassess(db, opp_id, reason, actor) -> dict          a new numbered run of append-only assessment records
    assessments(db, opp_id, run=None, subject=None) -> dict
    profiles() -> dict                                   the task profiles of data/knowledge_base/retrieval.json
    embed_sources(db) -> dict                            freeze every source's passage vectors (needs the embedding service)
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.core.web import same_unit
from app.modules.catalog import service as catalog
from app.modules.decisions import service as decisions
from app.modules.knowledge.models import EXAMPLE_TYPES, KINDS, KbItem
from app.modules.knowledge.retrieval import assessments, embed_sources, profiles, reassess, retrieve  # noqa: F401  (public contract)
from app.modules.knowledge.sources import (  # noqa: F401  (public contract)
    COLLECTIONS, REVIEWERS, STATUSES, SUFFIXES, annotate, counts, evidence, get, register, register_product_documents, register_references,
    review as review_source, source_passages, sources)
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages

COMPLIANCE_WORDS = {"met": "Met", "partial": "Partially met", "not_met": "Not met", "exception": "Exception",
                    "deviation": "Met with changes"}
REVIEWED_BY = "a unit's manager or designer / engineer for its answers; the bid manager for bid-level items"


def _row_id(ref: str) -> bool:
    """A database row number: ASCII digits that fit an integer column ("²" or 30 digits are not)."""
    return ref.isascii() and ref.isdigit() and len(ref) <= 9


def _source(db: Session, kind: str, ref: str) -> dict:
    """What the item says, read from the module that owns it."""
    if kind == "requirement":
        req = requirements.get(db, ref)
        if req is None:
            raise LookupError(f"Requirement {ref} not found.")
        return {"opportunity_id": req.opportunity_id, "bu": "BID", "requirement": req.text,
                "response": "", "source": f"{req.req_id}, {req.source}"}
    if kind == "response":
        a = workpackages.get(db, int(ref)) if _row_id(ref) else None
        if a is None:
            raise LookupError(f"Answer {ref} not found.")
        if a.status != "validated":
            raise ValueError("Only validated answers go to the knowledge base.")
        req = requirements.get(db, a.req_id)
        product = f" Offered: {(catalog.product(a.product_ref) or {}).get('name', a.product_ref)}." if a.product_ref else ""
        return {"opportunity_id": a.opportunity_id, "bu": a.bu, "requirement": req.text if req else a.req_id,
                "response": f"{COMPLIANCE_WORDS.get(a.compliance, a.compliance)}. {a.response.strip()}{product}",
                "source": f"{a.req_id}, {req.source if req else ''}".rstrip(", ")}
    if kind == "decision":
        d = decisions.get(db, int(ref)) if _row_id(ref) else None
        if d is None:
            raise LookupError(f"Decision {ref} not found.")
        if not d.rationale.strip():
            raise ValueError("This decision has no rationale to keep.")
        what = "Go/no-go decision" if d.kind == "go_no_go" else "Participation decision"
        outcome = d.outcome.replace("_", "-") if d.kind == "go_no_go" else ", ".join(d.units)
        return {"opportunity_id": d.opportunity_id, "bu": "BID", "requirement": f"{what} ({d.opportunity_id})",
                "response": f"{outcome}: {d.rationale.strip()}", "source": f"{d.opportunity_id}, decided by {d.decided_by}"}
    if kind == "correction":
        req = requirements.get(db, ref)
        if req is None:
            raise LookupError(f"Requirement {ref} not found.")
        versions = requirements.history(db, ref)["versions"]
        fixed = [i for i, v in enumerate(versions) if i > 0 and v["origin"] == "correction"]
        if not fixed:
            raise ValueError("This requirement has no correction of its reading to keep.")
        before, after = versions[fixed[-1] - 1], versions[fixed[-1]]
        why = f" Reason: {after['reason']}." if after.get("reason") else ""
        return {"opportunity_id": req.opportunity_id, "bu": "BID", "requirement": f"Read as: {before['text']}",
                "response": f"Corrected to: {after['text']}.{why}", "source": f"{req.req_id}, {req.source}"}
    raise ValueError(f"Unknown kind {kind!r}; expected one of {KINDS}.")


def _next_kb_id(db: Session) -> str:
    last = db.scalar(select(KbItem.kb_id).order_by(KbItem.id.desc()).limit(1))
    return f"KB-{int(last.split('-')[1]) + 1 if last else 1:04d}"


def _get(db: Session, kb_id: str) -> KbItem:
    item = db.scalar(select(KbItem).where(KbItem.kb_id == kb_id))
    if item is None:
        raise LookupError(f"{kb_id} not found.")
    return item


def nominate(db: Session, kind: str, ref: str, actor: str, note: str = "", example_type: str = "other",
             conditions: str = "", limits: str = "") -> KbItem:
    if example_type not in EXAMPLE_TYPES:
        raise ValueError(f"Unknown example type {example_type!r}; one of {', '.join(EXAMPLE_TYPES)}.")
    src = _source(db, kind, str(ref))
    taken = db.scalar(select(KbItem).where(KbItem.kind == kind, KbItem.source_ref == str(ref),
                                           KbItem.status.in_(("queued", "approved"))))
    if taken:
        raise ValueError(f"Already {taken.status} as {taken.kb_id}.")
    item = KbItem(kb_id=_next_kb_id(db), kind=kind, source_ref=str(ref), note=note.strip(), sent_by=actor,
                  example_type=example_type, conditions=conditions.strip(), limits=limits.strip(), **src)
    db.add(item)
    audit.record(db, actor, "nominated", "knowledge", item.kb_id, item.opportunity_id, kind=kind, ref=str(ref),
                 example_type=example_type)
    db.commit()
    return item


def send(db: Session, kind: str, ref: str, note: str, actor: str) -> KbItem:
    """The A-11 name, kept for callers: nominate with the defaults."""
    return nominate(db, kind, ref, actor, note)


def may_review(item: KbItem, user: dict) -> bool:
    if item.bu == "BID":
        return user.get("role") == "bid_manager"
    return same_unit(user, item.bu)


def items(db: Session, status: str | None = None, user: dict | None = None) -> list[KbItem]:
    q = select(KbItem).order_by(KbItem.id.desc())
    found = list(db.scalars(q.where(KbItem.status == status) if status else q))
    return [i for i in found if may_review(i, user)] if user else found


def for_opportunity(db: Session, opp_id: str) -> dict[str, str]:
    rows = db.scalars(select(KbItem).where(KbItem.opportunity_id == opp_id).order_by(KbItem.id))
    return {f"{i.kind}:{i.source_ref}": i.status for i in rows}


def review(db: Session, kb_id: str, approve: bool, note: str, user: dict, response: str | None = None) -> KbItem:
    item = _get(db, kb_id)
    if not may_review(item, user):
        raise PermissionError(f"Reviewed by {REVIEWED_BY}" + ("." if item.bu == "BID" else f" (here: {item.bu})."))
    if item.status != "queued":
        raise ValueError(f"{kb_id} is already {item.status}.")
    if not approve and not note.strip():
        raise ValueError("A rejection needs a note saying why.")
    if approve and response is not None and response.strip():
        item.response = response.strip()
    item.status, item.reviewed_by, item.reviewed_at, item.review_note = (
        "approved" if approve else "rejected"), user["name"], utcnow(), note.strip()
    if approve and item.supersedes:
        old = _get(db, item.supersedes)
        old.status = "retired"
        audit.record(db, user["name"], "retired", "knowledge", old.kb_id, old.opportunity_id, replaced_by=kb_id)
    audit.record(db, user["name"], item.status, "knowledge", kb_id, item.opportunity_id, note=note.strip())
    db.commit()
    if approve:
        catalog.learn()  # the long-term index reads approved items from here (learned())
    return item


def revise(db: Session, kb_id: str, actor: str, **fields) -> KbItem:
    """A change to an approved item is a new queued version; the approved one stays in use until the new one is approved."""
    old = _get(db, kb_id)
    if old.status != "approved":
        raise ValueError(f"{kb_id} is {old.status}; only an approved item is revised.")
    if db.scalar(select(KbItem).where(KbItem.supersedes == kb_id, KbItem.status == "queued")):
        raise ValueError(f"A new version of {kb_id} is already waiting for review.")
    allowed = {"response", "example_type", "conditions", "limits", "note"}
    if set(fields) - allowed or fields.get("example_type", old.example_type) not in EXAMPLE_TYPES:
        raise ValueError(f"Only {', '.join(sorted(allowed))} can change, with a known example type.")
    keep = {c: getattr(old, c) for c in ("kind", "example_type", "source_ref", "opportunity_id", "bu", "requirement",
                                         "response", "source", "conditions", "limits", "note", "illustrative")}
    item = KbItem(**(keep | {k: str(v).strip() for k, v in fields.items()}), kb_id=_next_kb_id(db),
                  version=old.version + 1, supersedes=kb_id, sent_by=actor)
    db.add(item)
    audit.record(db, actor, "revised", "knowledge", item.kb_id, item.opportunity_id, supersedes=kb_id)
    db.commit()
    return item


def learned(db: Session) -> list[dict]:
    """Approved, non-illustrative reviewed examples in the shape of a past response, for the long-term index."""
    rows = db.scalars(select(KbItem).where(KbItem.status == "approved", KbItem.illustrative.is_(False))
                      .order_by(KbItem.id))
    return [{"id": i.kb_id, "bu": i.bu, "rfp": i.opportunity_id, "requirement": i.requirement, "response": i.response,
             "source": i.source, "approved_by": i.reviewed_by} for i in rows]
