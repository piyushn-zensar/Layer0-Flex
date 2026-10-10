from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
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
