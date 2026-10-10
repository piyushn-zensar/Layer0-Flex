"""Knowledge-base queue (A-11): people send a requirement, a validated answer or a decision rationale to the
knowledge base; the curator approves or rejects each item. Approved items join the long-term retrieval index
(catalog.learn), so the next opportunity's matching evidence, response outline and catalog search can find them.
Nothing enters the knowledge base without a person's approval.  Owner: Atharv.

Public contract:
    send(db, kind, ref, note, actor) -> KnowledgeItem   kind: requirement (ref = req_id) | response (ref = assignment
        id, validated answers only) | decision (ref = decision id). LookupError: unknown source; ValueError: not
        validated, or already queued or approved
    items(db, status=None) -> list[KnowledgeItem]         newest first
    for_opportunity(db, opp_id) -> dict[str, str]         "<kind>:<ref>" -> status, for the "sent" state of buttons
    review(db, kb_id, approve, note, actor, response=None) -> KnowledgeItem
        only the curator (PoC: the Bid Manager), only queued items; a rejection needs a note; the curator may
        tidy the response text before approving. LookupError / PermissionError / ValueError
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import utcnow
from app.modules.catalog import service as catalog
from app.modules.decisions import service as decisions
from app.modules.knowledge.models import KINDS, KnowledgeItem
from app.modules.requirements import service as requirements
from app.modules.workpackages import service as workpackages

CURATOR = "Bid Manager"  # ponytail: PoC actor; a named knowledge curator role comes with sign-in
COMPLIANCE_WORDS = {"met": "Met", "partial": "Partially met", "not_met": "Not met", "exception": "Exception"}


def _source(db: Session, kind: str, ref: str) -> dict:
    """What the item says, read from the module that owns it."""
    if kind == "requirement":
        req = requirements.get(db, ref)
        if req is None:
            raise LookupError(f"Requirement {ref} not found.")
        return {"opportunity_id": req.opportunity_id, "bu": "BID", "requirement": req.text,
                "response": "", "source": f"{req.req_id}, {req.source}"}
    if kind == "response":
        a = workpackages.get(db, int(ref)) if ref.isdigit() else None
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
        d = decisions.get(db, int(ref)) if ref.isdigit() else None
        if d is None:
            raise LookupError(f"Decision {ref} not found.")
        if not d.rationale.strip():
            raise ValueError("This decision has no rationale to keep.")
        what = "Go/no-go decision" if d.kind == "go_no_go" else "Participation decision"
        outcome = d.outcome.replace("_", "-") if d.kind == "go_no_go" else ", ".join(d.units)
        return {"opportunity_id": d.opportunity_id, "bu": "BID", "requirement": f"{what} ({d.opportunity_id})",
                "response": f"{outcome}: {d.rationale.strip()}", "source": f"{d.opportunity_id}, decided by {d.decided_by}"}
    raise ValueError(f"Unknown kind {kind!r}; expected one of {KINDS}.")


def _next_kb_id(db: Session) -> str:
    last = db.scalar(select(KnowledgeItem.kb_id).order_by(KnowledgeItem.id.desc()).limit(1))
    return f"KB-{int(last.split('-')[1]) + 1 if last else 1:04d}"


def send(db: Session, kind: str, ref: str, note: str, actor: str) -> KnowledgeItem:
    src = _source(db, kind, str(ref))
    taken = db.scalar(select(KnowledgeItem).where(KnowledgeItem.kind == kind, KnowledgeItem.source_ref == str(ref),
                                                  KnowledgeItem.status != "rejected"))
    if taken:
        raise ValueError(f"Already {taken.status} as {taken.kb_id}.")
    item = KnowledgeItem(kb_id=_next_kb_id(db), kind=kind, source_ref=str(ref), note=note.strip(), sent_by=actor, **src)
    db.add(item)
    audit.record(db, actor, "sent", "knowledge", item.kb_id, item.opportunity_id, kind=kind, ref=str(ref))
    db.commit()
    return item


def items(db: Session, status: str | None = None) -> list[KnowledgeItem]:
    q = select(KnowledgeItem).order_by(KnowledgeItem.id.desc())
    return list(db.scalars(q.where(KnowledgeItem.status == status) if status else q))


def for_opportunity(db: Session, opp_id: str) -> dict[str, str]:
    rows = db.scalars(select(KnowledgeItem).where(KnowledgeItem.opportunity_id == opp_id).order_by(KnowledgeItem.id))
    return {f"{i.kind}:{i.source_ref}": i.status for i in rows}


def review(db: Session, kb_id: str, approve: bool, note: str, actor: str, response: str | None = None) -> KnowledgeItem:
    item = db.scalar(select(KnowledgeItem).where(KnowledgeItem.kb_id == kb_id))
    if item is None:
        raise LookupError(f"{kb_id} not found.")
    if actor != CURATOR:
        raise PermissionError("Only the knowledge curator (in the PoC, the Bid Manager) approves knowledge.")
    if item.status != "queued":
        raise ValueError(f"{kb_id} is already {item.status}.")
    if not approve and not note.strip():
        raise ValueError("A rejection needs a note saying why.")
    if approve and response is not None and response.strip():
        item.response = response.strip()
    item.status, item.reviewed_by, item.reviewed_at, item.review_note = (
        "approved" if approve else "rejected"), actor, utcnow(), note.strip()
    audit.record(db, actor, item.status, "knowledge", kb_id, item.opportunity_id, note=note.strip())
    db.commit()
    if approve:  # into the long-term index, after the decision is stored
        catalog.learn({"id": item.kb_id, "bu": item.bu, "rfp": item.opportunity_id, "requirement": item.requirement,
                       "response": item.response, "source": item.source, "approved_by": actor})
    return item
