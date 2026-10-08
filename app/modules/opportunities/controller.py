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


@router.post("/opportunities")
def create(body: OpportunityIn, request: Request, db: Session = Depends(get_db)):
    return row(service.create(db, body.title, body.customer, body.customer_type, actor(request)))


@router.get("/opportunities/{opp_id}")
def detail(opp_id: str, db: Session = Depends(get_db)):
    opp = service.get(db, opp_id)
    if not opp:
        raise HTTPException(404, f"{opp_id} not found")
    return {"opportunity": row(opp), "documents": [row(d) for d in service.documents(db, opp_id)]}


def _ingest_in_background(doc_id: str):
    with SessionLocal() as db:
        ingestion.ingest(db, doc_id)


@router.post("/opportunities/{opp_id}/documents")
async def upload(opp_id: str, request: Request, background: BackgroundTasks, role: str = Form("main"),
                 file: UploadFile = File(...), db: Session = Depends(get_db)):
    doc = service.add_document(db, opp_id, file.filename, await file.read(), role, actor(request))
    if doc.status == "uploaded":
        background.add_task(_ingest_in_background, doc.id)
    return row(doc)
