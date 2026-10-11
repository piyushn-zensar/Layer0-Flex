from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_db
from app.core.web import actor, row
from app.modules.ingestion import service as ingestion
from app.modules.opportunities import service

router = APIRouter(tags=["opportunities"])


class OpportunityIn(BaseModel):
    title: str
    customer: str = ""
    customer_type: str = ""


def _doc(d) -> dict:
    return {k: v for k, v in row(d).items() if k != "path"}  # never expose the server's file system


@router.post("/opportunities")
def create(body: OpportunityIn, request: Request, db: Session = Depends(get_db)):
    try:
        return row(service.create(db, body.title, body.customer, body.customer_type, actor(request)))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/opportunities/{opp_id}")
def detail(opp_id: str, db: Session = Depends(get_db)):
    opp = service.get(db, opp_id)
    if not opp:
        raise HTTPException(404, f"{opp_id} not found")
    return {"opportunity": row(opp), "documents": [_doc(d) for d in service.documents(db, opp_id)]}


def _ingest_in_background(doc_id: str):
    with SessionLocal() as db:
        ingestion.ingest(db, doc_id)


def _attach(db: Session, request: Request, background: BackgroundTasks, opp_id: str, filename: str, data: bytes,
            role: str) -> dict:
    """Store the file, read it in the background, answer at once (the page polls the document's status)."""
    known = {d.id for d in service.documents(db, opp_id)}
    try:
        doc = service.add_document(db, opp_id, filename, data, role, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if doc.status == "uploaded":  # also a re-upload of a file whose reading never finished: it is read again
        background.add_task(_ingest_in_background, doc.id)
    # existing: the same file was attached before (same content), so nothing new was added; the page can say so
    return _doc(doc) | {"existing": doc.id in known}


@router.post("/opportunities/{opp_id}/documents")
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


@router.post("/opportunities/{opp_id}/documents/from-sample")
def upload_sample(opp_id: str, body: SampleIn, request: Request, background: BackgroundTasks,
                  db: Session = Depends(get_db)):
    """Attach a sample RFP as the main document: the same storing, reading, JSON and status transitions as an upload."""
    if not service.get(db, opp_id):
        raise HTTPException(404, f"Opportunity {opp_id} not found.")
    try:
        filename, data = service.sample_file(body.name, "rfp")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _attach(db, request, background, opp_id, filename, data, "main")
