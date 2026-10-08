from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.catalog import service as catalog
from app.modules.requirements import service as requirements
from app.modules.workpackages import service
from app.modules.workpackages.models import COMPLIANCE

router = APIRouter(tags=["workpackages"])


class RespondIn(BaseModel):
    compliance: Literal["met", "partial", "not_met", "exception"]  # = models.COMPLIANCE
    product_ref: str = ""
    response: str = ""


class ValidateIn(BaseModel):
    ok: bool
    note: str = ""


@router.post("/opportunities/{opp_id}/dispatch")
def dispatch(opp_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        return {"created": service.dispatch(db, opp_id, actor(request))}
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.get("/inbox/{bu}")
def inbox(bu: str, db: Session = Depends(get_db)):
    items = service.inbox(db, bu)
    return {"bu": bu, "unit": catalog.unit(bu), "compliance": COMPLIANCE,
            "items": [row(a) | {"requirement": row(requirements.get(db, a.req_id), "source")} for a in items]}


@router.post("/assignments/{assignment_id}/respond")
def respond(assignment_id: int, body: RespondIn, request: Request, db: Session = Depends(get_db)):
    try:
        service.respond(db, assignment_id, body.compliance, body.product_ref, body.response, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return {"ok": True}


@router.post("/assignments/{assignment_id}/validate")
def validate(assignment_id: int, body: ValidateIn, request: Request, db: Session = Depends(get_db)):
    try:
        service.validate(db, assignment_id, body.ok, body.note, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return {"ok": True}
