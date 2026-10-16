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
    samples() -> list[dict]                      the bundled sample documents (name, filename, kind, pages,
                                                 description; never a path), for the walkthrough's "Use example"
    sample_file(name, kind) -> (filename, bytes)  ValueError for an unknown name or a sample of another kind
"""
import hashlib
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import audit, config, fileid
from app.core.audit import AuditEvent
from app.modules.opportunities.models import (STATUSES, BidApproval, BidSchedule, Document, DocumentIdentity,
                                               Opportunity, UnitSchedule)

FILES = config.STORE / "files"
READABLE = (".pdf", ".docx", ".xlsx")  # Word and Excel are read through a rendered PDF (ingestion/office.py, P-28)

# Sample documents the walkthrough (and anyone without a file at hand) can attach instead of uploading one. A
# whitelist: the API serves these names only, never a path. kind "rfp" goes in as the main RFP, kind "change" as a
# change document. The Syracuse and Logan City RFPs have frozen reader answers, so new opportunities can read them
# offline; the addendum's frozen change-agent answers match the demo opportunity's requirement set only.
SAMPLES = {
    "syracuse_rfp": {
        "path": "RFP-2023-20-Switchgear-Procurement-Final.pdf", "filename": "RFP-2023-20-Switchgear-Procurement-Final.pdf",
        "kind": "rfp", "pages": 101,
        "description": "Syracuse Regional Airport Authority, RFP 2023-20 Switchgear Procurement: the public RFP behind "
                       "the demo bid. Read offline from frozen answers: about 820 line items grouped into "
                       "about 310 requirements, each anchored to its page and lines."},
    "logan_rfp": {
        "path": "Logan-City-Substation-6-15kV-Switchgear.pdf", "filename": "Logan-City-Substation-6-15kV-Switchgear.pdf",
        "kind": "rfp", "pages": 46,
        "description": "Logan City Light & Power (Utah), 15kV Switchgear for Substation 6 (2017): a public bid document "
                       "from another issuer, the independent validation case (C-11). Read offline from frozen answers "
                       "into the register; its matching answers come later (A-23)."},
    "syracuse_addendum_1": {
        "path": "samples/rfp_syracuse_addendum_1.pdf", "filename": "rfp_syracuse_addendum_1.pdf",
        "kind": "change", "pages": 1,
        "description": "Illustrative Addendum No. 1 to the Syracuse RFP, written for the PoC: it revises, removes and "
                       "adds requirements against the frozen baseline. Its frozen change-agent answers match the demo "
                       "bid's requirement set only."},
}


def samples() -> list[dict]:
    return [{"name": name} | {k: v for k, v in s.items() if k != "path"} for name, s in SAMPLES.items()]


def sample_file(name: str, kind: str) -> tuple[str, bytes]:
    s = SAMPLES.get(name)
    if s is None:
        raise ValueError(f"Unknown sample {name!r}; see /api/samples.")
    if s["kind"] != kind:
        raise ValueError(f"Sample {name!r} is {'a change document' if s['kind'] == 'change' else 'an RFP'}, "
                         f"not {'a change document' if kind == 'change' else 'an RFP'}.")
    return s["filename"], (config.DATA / "RFP" / s["path"]).read_bytes()


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
    raise ValueError("Could not allocate a bid ID; try again.")


def get(db: Session, opp_id: str) -> Opportunity | None:
    return db.get(Opportunity, opp_id)


def require(db: Session, opp_id: str) -> Opportunity:
    opp = db.get(Opportunity, opp_id)
    if opp is None:
        raise LookupError(f"Bid {opp_id} not found.")
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
        raise ValueError("This bid already has a main RFP; upload this file as an addendum, clarification / Q&A, change request or other document.")
    FILES.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower()
    path = FILES / f"{sha}{suffix if suffix in READABLE else ''}"
    path.write_bytes(data)
    doc = Document(id=f"{opp_id}-{sha[:12]}", sha256=sha, opportunity_id=opp_id, filename=filename, role=role, path=str(path),
                   status="uploaded" if path.suffix in READABLE else "unsupported")
    db.add(doc)
    ident, instance, source = fileid.identity(data, suffix)
    db.add(DocumentIdentity(document_id=doc.id, doc_ident=ident, instance_ident=instance, id_source=source))
    audit.record(db, actor, "uploaded", "document", doc.id, opp_id, sha256=sha, filename=filename, role=role,
                 document_ident=ident, instance_ident=instance)
    db.commit()
    return doc


def known_instance(db: Session, filename: str, data: bytes, opp_id: str) -> dict | None:
    """C-27: has another bid already read this document? {"bid", "document", "same_instance"} for the most recent
    such bid (a bid that has been read: status review or later), else None. same_instance False = the same Document ID
    in a different instance (the document was edited and saved again)."""
    ident, instance, _ = fileid.identity(data, Path(filename).suffix)
    rows = db.execute(select(DocumentIdentity, Document, Opportunity)
                      .join(Document, Document.id == DocumentIdentity.document_id)
                      .join(Opportunity, Opportunity.id == Document.opportunity_id)
                      .where(DocumentIdentity.doc_ident == ident, Opportunity.id != opp_id)
                      .order_by(Document.received_at.desc())).all()
    read = [(i, d, o) for i, d, o in rows if FORWARD.get(o.status, 0) >= FORWARD["review"]]
    same = next(((i, d, o) for i, d, o in read if i.instance_ident == instance), None)
    hit = same or (read[0] if read else None)
    return None if hit is None else {"bid": hit[2].id, "bid_title": hit[2].title, "document": hit[1].id,
                                     "filename": hit[1].filename, "same_instance": same is not None}


def identity_of(db: Session, doc_id: str) -> DocumentIdentity | None:
    return db.get(DocumentIdentity, doc_id)


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


READ_ONCE = True  # C-27: a document instance read in one bid is not read into another; tests of other flows switch it off


# --- schedule and approvals (C-24, P-33) ----------------------------------------------------------------------

CONSOLIDATION_DAYS = 5  # ponytail: placeholder until the business gives its consolidation time (open question 4)


def set_due(db: Session, opp_id: str, due_date: date | None, consolidation_days: int, actor: str) -> BidSchedule:
    require(db, opp_id)
    if consolidation_days < 0:
        raise ValueError("Consolidation days cannot be negative.")
    bs = db.get(BidSchedule, opp_id) or BidSchedule(opportunity_id=opp_id, updated_by=actor)
    bs.due_date, bs.consolidation_days, bs.updated_by = due_date, consolidation_days, actor
    db.add(bs)
    audit.record(db, actor, "schedule_set", "schedule", opp_id, opp_id, due_date=str(due_date) if due_date else None,
                 consolidation_days=consolidation_days)
    db.commit()
    return bs


def set_unit_completion(db: Session, opp_id: str, bu: str, when: date, note: str, actor: str) -> UnitSchedule:
    require(db, opp_id)
    row = db.scalar(select(UnitSchedule).where(UnitSchedule.opportunity_id == opp_id, UnitSchedule.bu == bu))
    before = str(row.estimated_completion) if row else None
    row = row or UnitSchedule(opportunity_id=opp_id, bu=bu, estimated_completion=when, entered_by=actor)
    row.estimated_completion, row.note, row.entered_by = when, note.strip(), actor
    db.add(row)
    audit.record(db, actor, "completion_estimated", "schedule", opp_id, opp_id, bu=bu, before=before, after=str(when))
    db.commit()
    return row


def schedule(db: Session, opp_id: str, units: list[str]) -> dict:
    """The consolidated schedule for the participating `units`: each unit's estimated completion, the latest, the
    planned submission date (latest + consolidation days) once every unit has a date, and whether it is after the due date."""
    require(db, opp_id)
    bs = db.get(BidSchedule, opp_id)
    dates = {u.bu: u for u in db.scalars(select(UnitSchedule).where(UnitSchedule.opportunity_id == opp_id))}
    days = bs.consolidation_days if bs else CONSOLIDATION_DAYS
    missing = [bu for bu in units if bu not in dates]
    latest = max((dates[bu].estimated_completion for bu in units if bu in dates), default=None)
    planned = latest + timedelta(days=days) if units and not missing else None
    due = bs.due_date if bs else None
    return {"due_date": due, "consolidation_days": days,
            "units": [{"bu": bu, "estimated_completion": dates[bu].estimated_completion if bu in dates else None,
                       "note": dates[bu].note if bu in dates else "", "entered_by": dates[bu].entered_by if bu in dates else None}
                      for bu in units],
            "missing": missing, "latest_unit_date": latest, "planned_submission": planned,
            "after_due": bool(planned and due and planned > due), "ready": bool(units) and not missing}


def approve(db: Session, opp_id: str, kind: str, snapshot: dict, actor: str, note: str = "") -> BidApproval:
    """Record the bid manager's approval of `kind` with the figures approved (the caller computes them)."""
    require(db, opp_id)
    if kind not in ("schedule", "compliance"):
        raise ValueError("Approve the schedule or the compliance position.")
    a = BidApproval(opportunity_id=opp_id, kind=kind, snapshot=snapshot, note=note.strip(), approved_by=actor)
    db.add(a)
    audit.record(db, actor, "approved", "bid_" + kind, opp_id, opp_id, snapshot=snapshot, note=note.strip())
    db.commit()
    return a


def approvals(db: Session, opp_id: str) -> dict[str, BidApproval | None]:
    """The latest approval of each kind (None when never approved)."""
    out = {}
    for kind in ("schedule", "compliance"):
        out[kind] = db.scalar(select(BidApproval).where(BidApproval.opportunity_id == opp_id, BidApproval.kind == kind)
                              .order_by(BidApproval.id.desc()).limit(1))
    return out
