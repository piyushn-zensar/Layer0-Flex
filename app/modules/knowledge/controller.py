import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import llm
from app.core.web import BID_MANAGER, CORRECTORS, actor, require, row, user
from app.modules.catalog import service as catalog
from app.modules.knowledge import service

router = APIRouter(tags=["knowledge"])


class SendIn(BaseModel):
    kind: Literal["requirement", "response", "decision"]  # = models.KINDS
    ref: str = Field(min_length=1, max_length=40)
    note: str = Field("", max_length=2000)


class ReviewIn(BaseModel):
    approve: bool
    note: str = Field("", max_length=2000)
    response: str | None = Field(None, max_length=8000)


def _call(fn, *args):
    """Service errors as HTTP: unknown -> 404, wrong person -> 403, wrong state -> 409."""
    try:
        return fn(*args)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.post("/knowledge")
def send(body: SendIn, request: Request, db: Session = Depends(get_db)):
    return row(_call(service.send, db, body.kind, body.ref, body.note, actor(request)))


@router.get("/knowledge")
def items(status: Literal["queued", "approved", "rejected"] | None = None, db: Session = Depends(get_db)):
    return {"items": [row(i) for i in service.items(db, status)], "curator": service.CURATOR,
            "learned": len(catalog.learned()), "index": catalog.index_mode()}


@router.get("/opportunities/{opp_id}/knowledge")
def sent(opp_id: str, db: Session = Depends(get_db)):
    """What was already sent from this opportunity: "<kind>:<ref>" -> status (for the buttons)."""
    return service.for_opportunity(db, opp_id)


@router.post("/knowledge/{kb_id}/review")
def review(kb_id: str, body: ReviewIn, request: Request, db: Session = Depends(get_db)):
    return row(_call(service.review, db, kb_id, body.approve, body.note, actor(request), body.response))


# --- knowledge sources (P-35) ---------------------------------------------------------------------------------

def _source(src, counts: dict) -> dict:
    n, annotated = counts.get(src.id, (0, 0))
    return row(src) | {"passages": n, "annotated": annotated, "path": None}  # never expose the server path


@router.get("/knowledge/sources")
def sources(collection: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    counts = service.counts(db)
    return {"sources": [_source(s, counts) for s in service.sources(db, collection, status)],
            "collections": service.COLLECTIONS, "reviewers": service.REVIEWERS, "statuses": service.STATUSES}


@router.get("/knowledge/sources/{ks_id}")
def source(ks_id: str, db: Session = Depends(get_db)):
    src = _call(service.get, db, ks_id)
    return {"source": _source(src, service.counts(db)),
            "passages": [row(p) for p in service.source_passages(db, ks_id)]}


@router.post("/knowledge/sources")
async def register(request: Request, file: UploadFile = File(...), collection: str = Form(...), title: str = Form(""),
                   publisher: str = Form(""), revision: str = Form(""), scope: str = Form(""),
                   permissions: str = Form("public"), url: str = Form(""), db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    name = Path(file.filename or "source").name
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{Path(name).suffix.lower()}"
        path.write_bytes(await file.read())
        src, existing = _call(service.register, db, path, actor(request), collection, title or Path(name).stem,
                              publisher, revision, scope, permissions, url, None, name)
    return _source(src, service.counts(db)) | {"existing": existing}


class SourceReviewIn(BaseModel):
    approve: bool
    note: str = Field("", max_length=2000)


@router.post("/knowledge/sources/{ks_id}/review")
def review_source(ks_id: str, body: SourceReviewIn, request: Request, db: Session = Depends(get_db)):
    u = user(request)
    src = _call(service.review_source, db, ks_id, body.approve, body.note, u["name"], u["role"])
    return _source(src, service.counts(db))


@router.post("/knowledge/sources/{ks_id}/annotate")
def annotate(ks_id: str, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)
    try:
        return {"annotated": _call(service.annotate, db, ks_id, actor(request))}
    except llm.LLMUnavailable as exc:
        raise HTTPException(503, f"The model is not available for the remaining pages ({exc}). Annotations made so far are kept.")
