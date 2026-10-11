"""Opportunities: the engagement workspace and its documents.  Owner: Piyush.

Public contract (other modules call only these):
    create(db, title, customer, customer_type, actor) -> Opportunity
    get(db, opp_id) -> Opportunity | None
    require(db, opp_id) -> Opportunity            LookupError if it does not exist (call it before any write)
    list_all(db) -> list[Opportunity]
    set_status(db, opp_id, status, actor) -> bool  moves forward only (see FORWARD); False if the move was ignored;
                                                 "go" after a "no_go" resumes at the status the stop replaced
    add_document(db, opp_id, filename, data, role, actor) -> Document   id = <opp>-<sha256[:12]>;
                                                 ValueError if a second main RFP is uploaded
    get_document(db, doc_id) -> Document | None
    documents(db, opp_id) -> list[Document]
    main_document(db, opp_id) -> Document | None
    set_document_status(db, doc_id, status, page_count=None)
"""
import hashlib

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import audit, config
from app.core.audit import AuditEvent
from app.modules.opportunities.models import STATUSES, Document, Opportunity

FILES = config.STORE / "files"


def create(db: Session, title: str, customer: str, customer_type: str, actor: str) -> Opportunity:
    if not title.strip():
        raise ValueError("A title is required.")
    for _ in range(20):  # two people creating at once: the loser takes the next number
        ids = db.scalars(select(Opportunity.id)).all()
        n = max((int(i.split("-")[1]) for i in ids), default=0) + 1
        opp = Opportunity(id=f"OPP-{n:04d}", title=title.strip(), customer=customer,
                          customer_type=customer_type, created_by=actor)
        db.add(opp)
        audit.record(db, actor, "created", "opportunity", opp.id, opp.id, title=title)
        try:
            db.commit()
            return opp
        except IntegrityError:
            db.rollback()
    raise ValueError("Could not allocate an opportunity ID; try again.")


def get(db: Session, opp_id: str) -> Opportunity | None:
    return db.get(Opportunity, opp_id)


def require(db: Session, opp_id: str) -> Opportunity:
    opp = db.get(Opportunity, opp_id)
    if opp is None:
        raise LookupError(f"Opportunity {opp_id} not found.")
    return opp


def list_all(db: Session) -> list[Opportunity]:
    return list(db.scalars(select(Opportunity).order_by(Opportunity.id.desc())))


# The status only moves forward through the workflow, so a repeated or late step (re-deciding "go" after
# dispatch, re-reading drafts) never sends the opportunity back. Exceptions: "no_go" stops a bid at any
# point before submission, and "go" may replace a "no_go".
FORWARD = {s: i for i, s in enumerate(STATUSES)} | {"no_go": STATUSES.index("go")}


def set_status(db: Session, opp_id: str, status: str, actor: str) -> bool:
    if status not in STATUSES:
        raise ValueError(f"Unknown status {status!r}.")
    opp = require(db, opp_id)
    stop_or_resume = {opp.status, status} == {"go", "no_go"} or (status == "no_go" and opp.status != "submitted")
    if status == opp.status or (FORWARD[status] < FORWARD[opp.status] and not stop_or_resume):
        return False
    if status == "go" and opp.status == "no_go":
        status = _resumed_status(db, opp_id)
    audit.record(db, actor, "status", "opportunity", opp_id, opp_id, before=opp.status, after=status)
    opp.status = status
    db.commit()
    return True


def _resumed_status(db: Session, opp_id: str) -> str:
    """A "go" after a "no_go" resumes where the bid stopped (e.g. dispatched), not at "go": the audit log holds the
    status the stop replaced."""
    events = db.scalars(select(AuditEvent).where(AuditEvent.entity == "opportunity", AuditEvent.entity_id == opp_id,
                                                 AuditEvent.action == "status").order_by(AuditEvent.id.desc()))
    stop = next((e for e in events if e.data.get("after") == "no_go"), None)
    was = stop.data.get("before") if stop else None
    return was if was in FORWARD and FORWARD[was] > FORWARD["go"] else "go"


def add_document(db: Session, opp_id: str, filename: str, data: bytes, role: str, actor: str) -> Document:
    require(db, opp_id)
    sha = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.opportunity_id == opp_id, Document.sha256 == sha))
    if existing:
        return existing
    if role == "main" and main_document(db, opp_id):
        raise ValueError("This opportunity already has a main RFP; upload this file as an addendum, Q&A or other.")
    FILES.mkdir(parents=True, exist_ok=True)
    path = FILES / f"{sha}{'.pdf' if filename.lower().endswith('.pdf') else ''}"
    path.write_bytes(data)
    doc = Document(id=f"{opp_id}-{sha[:12]}", sha256=sha, opportunity_id=opp_id, filename=filename, role=role, path=str(path),
                   status="uploaded" if path.suffix == ".pdf" else "unsupported")
    db.add(doc)
    audit.record(db, actor, "uploaded", "document", doc.id, opp_id, sha256=sha, filename=filename, role=role)
    db.commit()
    return doc


def get_document(db: Session, doc_id: str) -> Document | None:
    return db.get(Document, doc_id)


def documents(db: Session, opp_id: str) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.opportunity_id == opp_id)
                           .order_by(Document.received_at)))


def main_document(db: Session, opp_id: str) -> Document | None:
    return db.scalar(select(Document).where(Document.opportunity_id == opp_id, Document.role == "main"))


def set_document_status(db: Session, doc_id: str, status: str, page_count: int | None = None) -> None:
    doc = db.get(Document, doc_id)
    doc.status = status
    if page_count is not None:
        doc.page_count = page_count
    db.commit()
