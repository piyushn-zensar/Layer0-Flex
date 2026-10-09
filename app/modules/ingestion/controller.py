from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.ingestion import service

router = APIRouter(tags=["ingestion"])


def _found(fn, *args):
    try:
        return fn(*args)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.post("/documents/{doc_id}/ingest")
def ingest(doc_id: str, db: Session = Depends(get_db)):
    return _found(service.ingest, db, doc_id)


@router.get("/documents/{doc_id}/pages/{page_no:int}")
def page(doc_id: str, page_no: int, db: Session = Depends(get_db)):
    return _found(service.page, db, doc_id, page_no)


@router.get("/documents/{doc_id}/pages/{page_no:int}.png")
def page_png(doc_id: str, page_no: int, db: Session = Depends(get_db)):
    return Response(_found(service.page_png, db, doc_id, page_no), media_type="image/png")
