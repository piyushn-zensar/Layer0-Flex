from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import SessionLocal, get_db
from app.core.web import BID_MANAGER, UNIT_MANAGER, actor, require, row, same_unit, user
from app.modules.consolidation import service as consolidation
from app.modules.decisions import service as decisions
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service

router = APIRouter(tags=["opportunities"])


class OpportunityIn(BaseModel):
    title: str
    customer: str = ""
    customer_type: str = ""


def _doc(d) -> dict:
    return {k: v for k, v in row(d).items() if k != "path"}  # never expose the server's file system


@router.post("/bids")
def create(body: OpportunityIn, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)  # section 16.6: the bid manager creates bids and uploads their documents
    try:
        return row(service.create(db, body.title, body.customer, body.customer_type, actor(request)))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/bids/{opp_id}")
def detail(opp_id: str, db: Session = Depends(get_db)):
    opp = service.get(db, opp_id)
    if not opp:
        raise HTTPException(404, f"Bid {opp_id} not found.")
    return {"opportunity": row(opp), "documents": [_doc(d) for d in service.documents(db, opp_id)]}


@router.get("/bids/{opp_id}/activity")
def activity(opp_id: str, entity: str | None = None, req_id: str | None = None, bu: str | None = None,
             person: str | None = None, before: int | None = None, limit: int = 200, db: Session = Depends(get_db)):
    """The bid's activity log (C-16): every recorded event, newest first, read-only, open to everyone signed in."""
    if not service.get(db, opp_id):
        raise HTTPException(404, f"Bid {opp_id} not found.")
    return audit.activity(db, opp_id, entity, req_id, bu, person, before, limit)


def _ingest_in_background(doc_id: str):
    with SessionLocal() as db:
        ingestion.ingest(db, doc_id)


def _attach(db: Session, request: Request, background: BackgroundTasks, opp_id: str, filename: str, data: bytes,
            role: str) -> dict:
    """Store the file, read it in the background, answer at once (the page polls the document's status)."""
    require(request, BID_MANAGER)
    known = {d.id for d in service.documents(db, opp_id)}
    seen = service.known_instance(db, filename, data, opp_id) if role == "main" and service.READ_ONCE else None
    if seen and seen["same_instance"]:  # C-27: a document instance is read once; its bid holds the frozen requirements
        return {"existing_bid": seen["bid"], "document": seen["document"],
                "message": f"This document was already read in bid {seen['bid']} ({seen['bid_title']}). "
                           "Its stored requirements are shown there; it is not read again."}
    try:
        doc = service.add_document(db, opp_id, filename, data, role, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if doc.status == "uploaded":  # also a re-upload of a file whose reading never finished: it is read again
        background.add_task(_ingest_in_background, doc.id)
    # existing: the same file was attached before (same content), so nothing new was added; the page can say so
    # earlier_instance: another bid read an earlier version of this document (same Document ID, new Instance ID)
    return _doc(doc) | {"existing": doc.id in known, "earlier_instance": seen}


@router.post("/bids/{opp_id}/documents")
async def upload(opp_id: str, request: Request, background: BackgroundTasks, role: str = Form("main"),
                 file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    return _attach(db, request, background, opp_id, file.filename, data, role)


class SampleIn(BaseModel):
    name: str


@router.get("/samples")
def samples():
    """The bundled sample documents (the walkthrough's "Use example" path); the file inputs stay the manual path."""
    return {"samples": service.samples()}


@router.post("/bids/{opp_id}/documents/from-sample")
def upload_sample(opp_id: str, body: SampleIn, request: Request, background: BackgroundTasks,
                  db: Session = Depends(get_db)):
    """Attach a sample RFP as the main document: the same storing, reading, JSON and status transitions as an upload."""
    require(request, BID_MANAGER)  # P-31: the role check comes first, before anything about the bid or the sample
    if not service.get(db, opp_id):
        raise HTTPException(404, f"Bid {opp_id} not found.")
    try:
        filename, data = service.sample_file(body.name, "rfp")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _attach(db, request, background, opp_id, filename, data, "main")


# --- schedule and approvals (C-24, P-33) ----------------------------------------------------------------------

def _guard(fn):
    """Service errors as HTTP: unknown bid -> 404, wrong state -> 409."""
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


def _compliance(db: Session, opp_id: str) -> dict:
    """The high-level compliance position: per unit, validated answers by compliance and answers still open."""
    out: dict[str, dict] = {}
    for r in consolidation.compliance_matrix(db, opp_id)["rows"]:
        if not r["unit"]:
            continue
        unit = out.setdefault(r["unit"], {"met": 0, "partial": 0, "not_met": 0, "open": 0})
        unit[r["compliance"] if r["status"] == "validated" and r["compliance"] in unit else "open"] += 1
    return out


def _snapshot(db: Session, opp_id: str, kind: str) -> dict:
    if kind == "compliance":
        return _compliance(db, opp_id)
    s = service.schedule(db, opp_id, decisions.participating_units(db, opp_id))
    return {"due_date": str(s["due_date"]) if s["due_date"] else None, "planned_submission": str(s["planned_submission"]),
            "units": {u["bu"]: str(u["estimated_completion"]) for u in s["units"]}}


def _approval(db: Session, opp_id: str, a) -> dict | None:
    """An approval and whether it still matches the current figures (else it is reopened)."""
    return None if a is None else row(a) | {"current": a.snapshot == _snapshot(db, opp_id, a.kind)}


@router.get("/bids/{opp_id}/schedule")
def schedule(opp_id: str, db: Session = Depends(get_db)):
    """The consolidated schedule, the compliance position and the bid manager's approvals (C-24)."""
    s = _guard(lambda: service.schedule(db, opp_id, decisions.participating_units(db, opp_id)))
    return s | {"compliance": _compliance(db, opp_id),
                "approvals": {k: _approval(db, opp_id, a) for k, a in service.approvals(db, opp_id).items()}}


class DueIn(BaseModel):
    due_date: date | None = None
    consolidation_days: int = Field(5, ge=0, le=365)


@router.put("/bids/{opp_id}/schedule")
def set_due(opp_id: str, body: DueIn, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)
    return row(_guard(lambda: service.set_due(db, opp_id, body.due_date, body.consolidation_days, actor(request))))


class CompletionIn(BaseModel):
    estimated_completion: date
    note: str = Field("", max_length=2000)


@router.put("/bids/{opp_id}/units/{bu}/completion")
def set_completion(opp_id: str, bu: str, body: CompletionIn, request: Request, db: Session = Depends(get_db)):
    """The unit manager of `bu` gives the unit's estimated completion date (C-24, C-25)."""
    u = require(request, UNIT_MANAGER)
    if not same_unit(u, bu):
        raise HTTPException(403, f"Only {bu}'s unit manager gives its completion date.")
    if bu not in decisions.participating_units(db, opp_id):
        raise HTTPException(409, f"{bu} does not take part in this bid.")
    return row(_guard(lambda: service.set_unit_completion(db, opp_id, bu, body.estimated_completion, body.note, u["name"])))


class ApproveIn(BaseModel):
    kind: Literal["schedule", "compliance"]
    note: str = Field("", max_length=2000)


@router.post("/bids/{opp_id}/approvals")
def approve(opp_id: str, body: ApproveIn, request: Request, db: Session = Depends(get_db)):
    """The bid manager approves the overall schedule (only once every participating unit has a date) or the
    high-level compliance position (C-24)."""
    require(request, BID_MANAGER)
    if body.kind == "schedule":
        s = _guard(lambda: service.schedule(db, opp_id, decisions.participating_units(db, opp_id)))
        if not s["ready"]:
            raise HTTPException(409, "The schedule can be approved once every participating unit has given its estimated "
                                     f"completion date (missing: {', '.join(s['missing']) or 'no participating unit'}).")
    elif not _compliance(db, opp_id):
        raise HTTPException(409, "Nothing has been sent to the units yet; there is no compliance position to approve.")
    a = _guard(lambda: service.approve(db, opp_id, body.kind, _snapshot(db, opp_id, body.kind), actor(request), body.note))
    return _approval(db, opp_id, a)
