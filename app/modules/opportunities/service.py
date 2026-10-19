"""Opportunities: the engagement workspace and its documents.  Owner: Piyush.

Public contract (other modules call only these):
    create(db, title, customer, customer_type, actor) -> Opportunity
    get(db, opp_id) -> Opportunity | None
    require(db, opp_id) -> Opportunity            LookupError if it does not exist (call it before any write)
    list_all(db) -> list[Opportunity]
    set_status(db, opp_id, status, actor) -> bool  moves forward only (see FORWARD); False if the move was ignored;
                                                 "go" after a "no_go" resumes at the status the stop replaced
    add_document(db, opp_id, filename, data, role, actor) -> Document   id = <opp>-<sha256[:12]>; records its
                                                 identity (DocumentIdentity); ValueError if a second main RFP is uploaded
    identity(filename, data) -> dict             {doc_uid, instance_uid, source}: the IDs embedded in the file
                                                 (P-32, C-27), the SHA-256 for both when it carries none
    known(db, opp_id, filename, data) -> dict | None   the same document in another bid: {kind: "instance" (this very
                                                 instance is that bid's main RFP: open it) | "document" (an earlier
                                                 instance: add this one there as a change document), bid, title,
                                                 document, filename}
    get_document(db, doc_id) -> Document | None
    remove_document(db, doc_id, actor, reason)    a document whose reading failed before it was used (a change
                                                 upload the change agent could not read): removed with its identity, audited
    documents(db, opp_id) -> list[Document]
    main_document(db, opp_id) -> Document | None
    set_document_status(db, doc_id, status, page_count=None)
    samples() -> list[dict]                      the bundled sample documents (name, filename, kind, pages,
                                                 description; never a path), for the walkthrough's "Use example"
    sample_file(name, kind) -> (filename, bytes)  ValueError for an unknown name or a sample of another kind
"""
import hashlib
from datetime import date, timedelta
import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pymupdf

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import audit, config
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
    if opp.status == "no_go" and status != "go":  # a stopped bid moves on only after a go decision
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
    db.add(DocumentIdentity(document_id=doc.id, opportunity_id=opp_id, **identity(filename, data)))
    audit.record(db, actor, "uploaded", "document", doc.id, opp_id, sha256=sha, filename=filename, role=role)
    db.commit()
    return doc


XMP_MM = "{http://ns.adobe.com/xap/1.0/mm/}"
WORD_DOC_ID = ("{http://schemas.microsoft.com/office/word/2012/wordml}docId",   # w15: a GUID, preferred
               "{http://schemas.microsoft.com/office/word/2010/wordml}docId")   # w14: hex


def _xmp(xmp: str, name: str) -> str:
    """xmpMM:<name> from XMP metadata, as an element or as an attribute of rdf:Description."""
    for el in ET.fromstring(xmp).iter():
        if el.tag == XMP_MM + name and (el.text or "").strip():
            return el.text.strip()
        if el.get(XMP_MM + name):
            return el.get(XMP_MM + name).strip()
    return ""


def _pdf_strings(value: str) -> list[str]:
    """The strings of a PDF array (as PyMuPDF prints it) in upper-case hex: <hex> as written, (literal) decoded from
    its escapes. Writers use either form for the trailer /ID, so both give the same value."""
    out, i = [], 0
    while i < len(value):
        if value[i] == "<":
            j = value.index(">", i)
            out.append("".join(value[i + 1:j].split()).upper())
            i = j + 1
        elif value[i] == "(":
            buf, depth, i = bytearray(), 1, i + 1
            while i < len(value):
                c = value[i]
                if c == "\\" and i + 1 < len(value):
                    digits = ""
                    while len(digits) < 3 and i + 1 + len(digits) < len(value) and value[i + 1 + len(digits)] in "01234567":
                        digits += value[i + 1 + len(digits)]
                    if digits:
                        buf.append(int(digits, 8) & 0xFF)
                        i += 1 + len(digits)
                    else:
                        n = value[i + 1]
                        buf += {"n": b"\n", "r": b"\r", "t": b"\t", "b": b"\b", "f": b"\f"}.get(n, n.encode("latin-1", "replace"))
                        i += 2
                    continue
                depth += c == "("
                depth -= c == ")"
                i += 1
                if not depth:
                    break
                buf += c.encode("latin-1", "replace")
            out.append(buf.hex().upper())
        else:
            i += 1
    return out


def identity(filename: str, data: bytes) -> dict:
    sha = hashlib.sha256(data).hexdigest()
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                kind, value = pdf.xref_get_key(-1, "ID")  # trailer /ID: [<permanent ID><changing ID>]
                ids = _pdf_strings(value) if kind == "array" else []
                if len(ids) == 2:
                    return {"doc_uid": ids[0].upper(), "instance_uid": ids[1].upper(), "source": "pdf_trailer"}
                xmp = pdf.get_xml_metadata()
                doc_uid, instance = (_xmp(xmp, "DocumentID"), _xmp(xmp, "InstanceID")) if xmp else ("", "")
                if doc_uid and instance:
                    return {"doc_uid": doc_uid, "instance_uid": instance, "source": "xmp"}
        elif suffix == ".docx":
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                settings = ET.fromstring(z.read("word/settings.xml"))
            for tag in WORD_DOC_ID:  # Word keeps a document ID only; every save is a new instance (its fingerprint)
                found = next((el for el in settings.iter(tag)), None)
                val = found.get(tag.replace("docId", "val")) if found is not None else None
                if val:
                    return {"doc_uid": val.strip("{}").upper(), "instance_uid": sha, "source": "docx"}
    except Exception:  # noqa: BLE001 - unreadable or odd metadata: fall back to the fingerprint, never fail the upload
        pass
    return {"doc_uid": sha, "instance_uid": sha, "source": "sha256"}


def known(db: Session, opp_id: str, filename: str, data: bytes) -> dict | None:
    ident = identity(filename, data)
    rows = db.execute(select(DocumentIdentity, Document).join(Document, Document.id == DocumentIdentity.document_id)
                      .where(DocumentIdentity.doc_uid == ident["doc_uid"], DocumentIdentity.opportunity_id != opp_id)
                      .order_by(Document.received_at)).all()
    same = [(i, d) for i, d in rows if i.instance_uid == ident["instance_uid"] and d.role == "main"]
    hit = (same or rows or [None])[0]
    if not hit:
        return None
    d = hit[1]
    return {"kind": "instance" if same else "document", "bid": d.opportunity_id, "title": require(db, d.opportunity_id).title,
            "document": d.id, "filename": d.filename}


def remove_document(db: Session, doc_id: str, actor: str, reason: str) -> None:
    doc = db.get(Document, doc_id)
    if doc is None:
        return
    ident = db.get(DocumentIdentity, doc_id)
    if ident is not None:
        db.delete(ident)
    audit.record(db, actor, "removed", "document", doc_id, doc.opportunity_id, filename=doc.filename, reason=reason)
    db.delete(doc)
    db.commit()


def reset_interrupted_reads(db: Session) -> int:
    """On start: a background read cannot survive an API restart, so a document left "ingesting" goes back to
    "uploaded" and the next upload or ingest reads it again (19 Oct review)."""
    stuck = list(db.scalars(select(Document).where(Document.status == "ingesting")))
    for d in stuck:
        d.status = "uploaded"
    db.commit()
    return len(stuck)


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
