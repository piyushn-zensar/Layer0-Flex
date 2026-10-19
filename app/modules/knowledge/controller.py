import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import llm
from app.core.web import BID_MANAGER, CORRECTORS, actor, require, row, user
from app.modules.catalog import service as catalog
from app.modules.knowledge import service
from app.modules.opportunities import service as opportunities


def _bid(db: Session, opp_id: str) -> None:
    """An unknown bid is a 404, as on every other bid route."""
    if not opportunities.get(db, opp_id):
        raise HTTPException(404, f"Bid {opp_id} not found.")

router = APIRouter(tags=["knowledge"])


class SendIn(BaseModel):
    kind: Literal["requirement", "response", "decision", "correction"]  # = models.KINDS
    ref: str = Field(min_length=1, max_length=40)
    note: str = Field("", max_length=2000)
    example_type: Literal["requirement", "preference", "background", "partial_compliance", "insufficient_evidence",
                          "other"] = "other"  # = models.EXAMPLE_TYPES
    conditions: str = Field("", max_length=2000)
    limits: str = Field("", max_length=2000)


class ReviewIn(BaseModel):
    approve: bool
    note: str = Field("", max_length=2000)
    response: str | None = Field(None, max_length=8000)


class ReviseIn(BaseModel):
    response: str | None = Field(None, max_length=8000)
    example_type: str | None = None
    conditions: str | None = Field(None, max_length=2000)
    limits: str | None = Field(None, max_length=2000)
    note: str | None = Field(None, max_length=2000)


def _call(fn, *args, **kwargs):
    """Service errors as HTTP: unknown -> 404, wrong person -> 403, wrong state -> 409."""
    try:
        return fn(*args, **kwargs)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


def _item(i, request: Request) -> dict:
    return row(i) | {"may_review": service.may_review(i, user(request))}


@router.post("/knowledge")
def send(body: SendIn, request: Request, db: Session = Depends(get_db)):
    """Nominate a reviewed example (P-36)."""
    require(request, *CORRECTORS)
    return _item(_call(service.nominate, db, body.kind, body.ref, actor(request), body.note, body.example_type,
                       body.conditions, body.limits), request)


@router.get("/knowledge")
def items(request: Request, status: Literal["queued", "approved", "rejected", "retired"] | None = None,
          reviewable: bool = False, db: Session = Depends(get_db)):
    """All items, or with reviewable=true only those the signed-in person may review (the review list in My work)."""
    found = service.items(db, status, user(request) if reviewable else None)
    return {"items": [_item(i, request) for i in found], "curator": service.REVIEWED_BY,
            "example_types": service.EXAMPLE_TYPES, "learned": len(catalog.learned()), "index": catalog.index_mode()}


@router.get("/bids/{opp_id}/knowledge")
def sent(opp_id: str, db: Session = Depends(get_db)):
    """What was already nominated from this bid: "<kind>:<ref>" -> status (for the buttons)."""
    _bid(db, opp_id)
    return service.for_opportunity(db, opp_id)


@router.post("/knowledge/{kb_id}/review")
def review(kb_id: str, body: ReviewIn, request: Request, db: Session = Depends(get_db)):
    return _item(_call(service.review, db, kb_id, body.approve, body.note, user(request), body.response), request)


@router.post("/knowledge/{kb_id}/revise")
def revise(kb_id: str, body: ReviseIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    item = _call(service._get, db, kb_id)
    if not service.may_review(item, user(request)):  # only the item's own unit (bid desk: bid manager) revises it
        raise HTTPException(403, f"Only the reviewers of {kb_id} revise it.")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return _item(_call(service.revise, db, kb_id, actor(request), **fields), request)


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
                   permissions: str = Form("public"), url: str = Form(""), bid: str | None = Form(None),
                   db: Session = Depends(get_db)):
    require(request, *CORRECTORS)  # bid: the bid a "Current bid evidence" source belongs to (19 Oct review)
    name = Path(file.filename or "source").name
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{Path(name).suffix.lower()}"
        path.write_bytes(await file.read())
        src, existing = _call(service.register, db, path, actor(request), collection, title or Path(name).stem,
                              publisher, revision, scope, permissions, url, bid or None, name)
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


# --- retrieval and assessment records (P-37 part 1) -----------------------------------------------------------

@router.get("/knowledge/retrieve")
def retrieve(task: str, q: str, bid: str | None = None, k: int | None = Query(None, ge=1, le=50), db: Session = Depends(get_db)):
    """The evidence a task would use for a question (each hit with its citation); see retrieval.json."""
    return {"task": task, "hits": _call(service.retrieve, db, task, q, bid, k)}


class ReassessIn(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


@router.post("/bids/{opp_id}/reassessments")
def reassess(opp_id: str, body: ReassessIn, request: Request, db: Session = Depends(get_db)):
    """An explicit, versioned reassessment: a new run of evidence records; earlier runs stay and requirements are untouched."""
    require(request, BID_MANAGER)
    return _call(service.reassess, db, opp_id, body.reason, actor(request))


@router.get("/bids/{opp_id}/assessments")
def assessments(opp_id: str, run: int | None = Query(None, ge=1, le=2**31 - 1), req_id: str | None = None,
                db: Session = Depends(get_db)):
    _bid(db, opp_id)
    out = service.assessments(db, opp_id, run, req_id)
    return out | {"records": [row(r) for r in out["records"]]}

