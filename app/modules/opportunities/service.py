"""Opportunities: the engagement workspace and its documents.  Owner: Piyush.

Public contract (other modules call only these):
    create(db, title, customer, customer_type, actor) -> Opportunity
    get(db, opp_id) -> Opportunity | None
    list_all(db) -> list[Opportunity]
    set_status(db, opp_id, status, actor)
    add_document(db, opp_id, filename, data, role, actor) -> Document   id = <opp>-<sha256[:12]>
    get_document(db, doc_id) -> Document | None
    documents(db, opp_id) -> list[Document]
    main_document(db, opp_id) -> Document | None
    set_document_status(db, doc_id, status, page_count=None)
"""
import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit, config
from app.modules.opportunities.models import STATUSES, Document, Opportunity

FILES = config.STORE / "files"


def create(db: Session, title: str, customer: str, customer_type: str, actor: str) -> Opportunity:
    # ponytail: count-based IDs; fine for one SQLite writer, use a sequence on PostgreSQL
    n = db.scalar(select(func.count()).select_from(Opportunity)) + 1
    opp = Opportunity(id=f"OPP-{n:04d}", title=title, customer=customer,
                      customer_type=customer_type, created_by=actor)
    db.add(opp)
    audit.record(db, actor, "created", "opportunity", opp.id, opp.id, title=title)
    db.commit()
    return opp


def get(db: Session, opp_id: str) -> Opportunity | None:
    return db.get(Opportunity, opp_id)


def list_all(db: Session) -> list[Opportunity]:
    return list(db.scalars(select(Opportunity).order_by(Opportunity.id.desc())))


def set_status(db: Session, opp_id: str, status: str, actor: str) -> None:
    assert status in STATUSES, status
    opp = db.get(Opportunity, opp_id)
    audit.record(db, actor, "status", "opportunity", opp_id, opp_id, before=opp.status, after=status)
    opp.status = status
    db.commit()


def add_document(db: Session, opp_id: str, filename: str, data: bytes, role: str, actor: str) -> Document:
    sha = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.opportunity_id == opp_id, Document.sha256 == sha))
    if existing:
        return existing
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
