from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, CORRECTORS, actor, require, row
from app.modules.opportunities import service as opportunities
from app.modules.requirements import service

router = APIRouter(tags=["requirements"])


class ReviewIn(BaseModel):
    action: Literal["approve", "reject", "edit"]
    text: str | None = None
    category: str | None = None
    reason: str = ""


class Part(BaseModel):
    quote: str
    text: str = ""


class SplitIn(BaseModel):
    parts: list[Part] = Field(min_length=2)
    reason: str = ""


class MergeIn(BaseModel):
    req_ids: list[str] = Field(min_length=2)
    text: str
    reason: str = ""


class AddIn(BaseModel):
    quote: str
    text: str = ""
    category: str = "technical"
    page: int | None = None


class LinesIn(BaseModel):
    page: int
    line_start: int
    line_end: int
    text: str = ""
    category: str = "technical"


class ResolveIn(BaseModel):
    page: int
    line_start: int
    line_end: int
    text: str = ""
    category: str | None = None


class DismissIn(BaseModel):
    reason: str


class ExtractIn(BaseModel):
    reason: str = ""


def _guard(fn):
    """Service errors -> HTTP: unknown id 404, not allowed in this state 409."""
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.get("/bids/{opp_id}/requirements")
def requirements(opp_id: str, db: Session = Depends(get_db)):
    _guard(lambda: opportunities.require(db, opp_id))  # an unknown opportunity is a 404, not an empty list
    b = service.baseline(db, opp_id)
    rows = service.current(db, opp_id, include_inactive=True, include_children=True)
    latest = next(iter(service.snapshots(db, opp_id)), None)
    return {"requirements": [row(r, "source") for r in rows], "baseline": row(b) if b else None,
            "exceptions": sum(r.status == "exception" for r in rows), "coverage": latest.coverage if latest else None}


def _snapshot(s, items: bool = False) -> dict:
    out = {k: getattr(s, k) for k in ("number", "document_id", "created_by", "created_at", "reason", "model",
                                       "pipeline_version", "coverage")}
    return out | {"items": s.items} if items else out


@router.get("/bids/{opp_id}/extraction")
def snapshots(opp_id: str, db: Session = Depends(get_db)):
    _guard(lambda: opportunities.require(db, opp_id))
    return [_snapshot(s) for s in service.snapshots(db, opp_id)]


@router.get("/bids/{opp_id}/extraction/{number}")
def snapshot(opp_id: str, number: int, db: Session = Depends(get_db)):
    _guard(lambda: opportunities.require(db, opp_id))
    return _snapshot(_guard(lambda: service.snapshot(db, opp_id, number)), items=True)


@router.get("/bids/{opp_id}/requirements/exceptions")
def exceptions(opp_id: str, db: Session = Depends(get_db)):
    _guard(lambda: opportunities.require(db, opp_id))
    return service.exceptions(db, opp_id)


@router.post("/bids/{opp_id}/requirements/extract")
def extract(opp_id: str, request: Request, body: ExtractIn | None = None, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)
    return _guard(lambda: service.extract(db, opp_id, actor(request), body.reason if body else ""))


@router.post("/bids/{opp_id}/requirements")
def add_missed(opp_id: str, body: AddIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    req = _guard(lambda: service.add_missed(db, opp_id, body.quote, body.text, body.category, actor(request), body.page))
    return row(req, "source")


@router.post("/bids/{opp_id}/requirements/from-lines")
def add_from_lines(opp_id: str, body: LinesIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    req = _guard(lambda: service.add_from_lines(db, opp_id, body.page, body.line_start, body.line_end, body.text,
                                                body.category, actor(request)))
    return row(req, "source")


@router.post("/bids/{opp_id}/requirements/merge")
def merge(opp_id: str, body: MergeIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    req = _guard(lambda: service.merge(db, opp_id, body.req_ids, body.text, actor(request), body.reason))
    return row(req, "source")


@router.post("/requirements/{req_id}/review")
def review(req_id: str, body: ReviewIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    _guard(lambda: service.review(db, req_id, body.action, actor(request), body.text, body.reason, body.category))
    return row(service.get(db, req_id), "source")


@router.post("/requirements/{req_id}/resolve")
def resolve(req_id: str, body: ResolveIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    return row(_guard(lambda: service.resolve(db, req_id, body.page, body.line_start, body.line_end, actor(request),
                                              body.text, body.category)), "source")


@router.post("/requirements/{req_id}/dismiss")
def dismiss(req_id: str, body: DismissIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    return row(_guard(lambda: service.dismiss(db, req_id, body.reason, actor(request))), "source")


@router.post("/requirements/{req_id}/ungroup")
def ungroup(req_id: str, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    return [row(r, "source") for r in _guard(lambda: service.ungroup(db, req_id, actor(request)))]


@router.get("/requirements/{req_id}/history")
def history(req_id: str, db: Session = Depends(get_db)):
    return _guard(lambda: service.history(db, req_id))


@router.post("/requirements/{req_id}/split")
def split(req_id: str, body: SplitIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    parts = [p.model_dump() for p in body.parts]
    return [row(r, "source") for r in _guard(lambda: service.split(db, req_id, parts, actor(request), body.reason))]


# P-32 (C-27): no publish route. A complete read freezes the register (requirements.extract); the freeze service stays.
