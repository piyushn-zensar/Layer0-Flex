from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, CORRECTORS, actor, require
from app.modules.changes import service
from app.modules.opportunities import service as opportunities

router = APIRouter(tags=["changes"])


class DecideIn(BaseModel):
    kind: Literal["added", "modified", "removed", "unchanged", "not_a_requirement"]  # = models.KINDS
    target: str | None = Field(None, max_length=20)
    text: str | None = Field(None, max_length=2000)


class CorrectionIn(BaseModel):
    """POST /api/opportunities/{id}/corrections: the fields each kind needs (requirements.apply_correction)."""
    kind: Literal["add", "edit", "split", "merge", "exclude", "resolve"]
    reason: str = Field(max_length=1000)
    req_id: str | None = Field(None, max_length=20)
    req_ids: list[str] | None = None
    text: str | None = Field(None, max_length=2000)
    category: str | None = None
    page: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    parts: list[dict] | None = None


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
def upload(opp_id: str, request: Request, file: UploadFile = File(...), role: str = Form("change"),
           db: Session = Depends(get_db)):
    """Synchronous: the change document is read and classified before the answer (frozen answers make it quick).
    role: the document type (addendum, qa, change)."""
    require(request, BID_MANAGER)
    data = file.file.read()
    return service.view(db, _call(service.upload, db, opp_id, file.filename or "change.pdf", data, actor(request), role))


@router.post("/opportunities/{opp_id}/corrections")
def correct(opp_id: str, body: CorrectionIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    fields = body.model_dump(exclude={"kind", "reason"}, exclude_none=True)
    return _call(service.correct, db, opp_id, body.kind, fields, body.reason, actor(request))


class SampleIn(BaseModel):
    name: str


@router.post("/opportunities/{opp_id}/changes/from-sample")
def upload_sample(opp_id: str, body: SampleIn, request: Request, db: Session = Depends(get_db)):
    """A bundled sample change document (GET /api/samples, kind "change") goes through upload() exactly like a file.
    In mock mode a 409 says no frozen answers exist when the opportunity's requirements differ from the demo's."""
    require(request, BID_MANAGER)
    _call(opportunities.require, db, opp_id)
    filename, data = _call(opportunities.sample_file, body.name, "change")
    return service.view(db, _call(service.upload, db, opp_id, filename, data, actor(request)))


@router.post("/changes/{set_id}/items/{item_id}")
def decide(set_id: int, item_id: int, body: DecideIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    item = _call(service.decide, db, set_id, item_id, body.kind, body.target, body.text, actor(request))
    return service.item_view(db, item)


@router.post("/changes/{set_id}/confirm-all")
def confirm_all(set_id: int, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)
    return service.view(db, _call(service.confirm_all, db, set_id, actor(request)))


@router.post("/changes/{set_id}/apply")
def apply(set_id: int, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)
    return service.view(db, _call(service.apply, db, set_id, actor(request)))


@router.post("/changes/{set_id}/discard")
def discard(set_id: int, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)
    return service.view(db, _call(service.discard, db, set_id, actor(request)))
