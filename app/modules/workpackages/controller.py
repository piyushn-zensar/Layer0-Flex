from fastapi import APIRouter, Depends, Request
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
    compliance: str  # met | partial | not_met | exception
    product_ref: str = ""
    response: str = ""


class ValidateIn(BaseModel):
    ok: bool
    note: str = ""


@router.post("/opportunities/{opp_id}/dispatch")
def dispatch(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return {"created": service.dispatch(db, opp_id, actor(request))}


@router.get("/inbox/{bu}")
def inbox(bu: str, db: Session = Depends(get_db)):
    items = service.inbox(db, bu)
    return {"bu": bu, "unit": catalog.unit(bu), "compliance": COMPLIANCE,
            "items": [row(a) | {"requirement": row(requirements.get(db, a.req_id), "source")} for a in items]}


@router.post("/assignments/{assignment_id}/respond")
def respond(assignment_id: int, body: RespondIn, request: Request, db: Session = Depends(get_db)):
    service.respond(db, assignment_id, body.compliance, body.product_ref, body.response, actor(request))
    return {"ok": True}


@router.post("/assignments/{assignment_id}/validate")
def validate(assignment_id: int, body: ValidateIn, request: Request, db: Session = Depends(get_db)):
    service.validate(db, assignment_id, body.ok, body.note, actor(request))
    return {"ok": True}
