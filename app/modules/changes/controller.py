from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor
from app.modules.changes import service

router = APIRouter(tags=["changes"])


class DecideIn(BaseModel):
    kind: Literal["added", "modified", "removed", "unchanged", "not_a_requirement"]  # = models.KINDS
    target: str | None = Field(None, max_length=20)
    text: str | None = Field(None, max_length=2000)


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


@router.get("/opportunities/{opp_id}/changes")
def changes(opp_id: str, db: Session = Depends(get_db)):
    return _call(service.overview, db, opp_id)


@router.post("/opportunities/{opp_id}/changes")
def upload(opp_id: str, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Synchronous: the change document is read and classified before the answer (frozen answers make it quick)."""
    data = file.file.read()
    return service.view(db, _call(service.upload, db, opp_id, file.filename or "change.pdf", data, actor(request)))


@router.post("/changes/{set_id}/items/{item_id}")
def decide(set_id: int, item_id: int, body: DecideIn, request: Request, db: Session = Depends(get_db)):
    item = _call(service.decide, db, set_id, item_id, body.kind, body.target, body.text, actor(request))
    return service.item_view(db, item)


@router.post("/changes/{set_id}/confirm-all")
def confirm_all(set_id: int, request: Request, db: Session = Depends(get_db)):
    return service.view(db, _call(service.confirm_all, db, set_id, actor(request)))


@router.post("/changes/{set_id}/apply")
def apply(set_id: int, request: Request, db: Session = Depends(get_db)):
    return service.view(db, _call(service.apply, db, set_id, actor(request)))


@router.post("/changes/{set_id}/discard")
def discard(set_id: int, request: Request, db: Session = Depends(get_db)):
    return service.view(db, _call(service.discard, db, set_id, actor(request)))
