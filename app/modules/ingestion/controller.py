from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.ingestion import service

router = APIRouter(tags=["ingestion"])


@router.post("/documents/{doc_id}/ingest")
def ingest(doc_id: str, db: Session = Depends(get_db)):
    return service.ingest(db, doc_id)


@router.get("/documents/{doc_id}/pages/{page_no:int}")
def page(doc_id: str, page_no: int):
    return service.page(doc_id, page_no)


@router.get("/documents/{doc_id}/pages/{page_no:int}.png")
def page_png(doc_id: str, page_no: int, db: Session = Depends(get_db)):
    return Response(service.page_png(db, doc_id, page_no), media_type="image/png")
