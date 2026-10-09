from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
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


def _guard(fn):
    """Service errors -> HTTP: unknown id 404, not allowed in this state 409."""
    try:
        return fn()
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.get("/opportunities/{opp_id}/requirements")
def requirements(opp_id: str, db: Session = Depends(get_db)):
    b = service.baseline(db, opp_id)
    return {"requirements": [row(r, "source") for r in service.current(db, opp_id, include_inactive=True, include_children=True)],
            "baseline": row(b) if b else None}


@router.post("/opportunities/{opp_id}/requirements/extract")
def extract(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return _guard(lambda: service.extract(db, opp_id, actor(request)))


@router.post("/opportunities/{opp_id}/requirements")
def add_missed(opp_id: str, body: AddIn, request: Request, db: Session = Depends(get_db)):
    req = _guard(lambda: service.add_missed(db, opp_id, body.quote, body.text, body.category, actor(request), body.page))
    return row(req, "source")


@router.post("/opportunities/{opp_id}/requirements/merge")
def merge(opp_id: str, body: MergeIn, request: Request, db: Session = Depends(get_db)):
    req = _guard(lambda: service.merge(db, opp_id, body.req_ids, body.text, actor(request), body.reason))
    return row(req, "source")


@router.post("/requirements/{req_id}/review")
def review(req_id: str, body: ReviewIn, request: Request, db: Session = Depends(get_db)):
    _guard(lambda: service.review(db, req_id, body.action, actor(request), body.text, body.reason, body.category))
    return row(service.get(db, req_id), "source")


@router.post("/requirements/{req_id}/ungroup")
def ungroup(req_id: str, request: Request, db: Session = Depends(get_db)):
    return [row(r, "source") for r in _guard(lambda: service.ungroup(db, req_id, actor(request)))]


@router.get("/requirements/{req_id}/history")
def history(req_id: str, db: Session = Depends(get_db)):
    return _guard(lambda: service.history(db, req_id))


@router.post("/requirements/{req_id}/split")
def split(req_id: str, body: SplitIn, request: Request, db: Session = Depends(get_db)):
    parts = [p.model_dump() for p in body.parts]
    return [row(r, "source") for r in _guard(lambda: service.split(db, req_id, parts, actor(request), body.reason))]


@router.post("/opportunities/{opp_id}/baselines")
def freeze(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return row(_guard(lambda: service.freeze(db, opp_id, actor(request))))
