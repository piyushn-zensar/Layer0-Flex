from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.catalog import service as catalog
from app.modules.requirements import service as requirements
from app.modules.workpackages import service
from app.modules.workpackages.models import BID_DESK, COMPLIANCE

router = APIRouter(tags=["workpackages"])
AssignmentId = Path(ge=1, le=2**31 - 1)


class RespondIn(BaseModel):
    compliance: Literal["met", "partial", "not_met", "exception"]  # = models.COMPLIANCE
    product_ref: str = ""
    response: str = ""


class ValidateIn(BaseModel):
    ok: bool
    note: str = ""

    @model_validator(mode="after")
    def _return_needs_note(self):  # design 7.5: "returned, with a note"
        if not self.ok and not self.note.strip():
            raise ValueError("Say why the answer is returned (note).")
        return self


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


@router.post("/opportunities/{opp_id}/dispatch")
def dispatch(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return {"created": _call(service.dispatch, db, opp_id, actor(request))}


@router.get("/opportunities/{opp_id}/handoff/{bu}")
def handoff(opp_id: str, bu: str, db: Session = Depends(get_db)):
    """The unit's hand-off payload (A-09, M8) as a JSON download."""
    payload = _call(service.handoff, db, opp_id, bu)
    return JSONResponse(payload, headers={"Content-Disposition": f'attachment; filename="{opp_id}-{bu}-handoff.json"'})


@router.get("/inbox/{bu}")
def inbox(bu: str, db: Session = Depends(get_db)):
    if bu != BID_DESK and catalog.unit(bu) is None:
        raise HTTPException(404, f"Unit {bu} not found.")

    def item(a):
        req = requirements.get(db, a.req_id)  # None if the requirement was deleted after dispatch
        return row(a) | {"requirement": row(req, "source") if req else None}
    return {"bu": bu, "unit": catalog.unit(bu), "compliance": COMPLIANCE, "items": [item(a) for a in service.inbox(db, bu)]}


@router.post("/assignments/{assignment_id}/respond")
def respond(body: RespondIn, request: Request, assignment_id: int = AssignmentId, db: Session = Depends(get_db)):
    _call(service.respond, db, assignment_id, body.compliance, body.product_ref, body.response, actor(request))
    return {"ok": True}


@router.post("/assignments/{assignment_id}/validate")
def validate(body: ValidateIn, request: Request, assignment_id: int = AssignmentId, db: Session = Depends(get_db)):
    _call(service.validate, db, assignment_id, body.ok, body.note, actor(request))
    return {"ok": True}
