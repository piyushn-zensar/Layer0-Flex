from collections import Counter
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, CORRECTORS, actor, require, row, user
from app.modules.catalog import service as catalog
from app.modules.requirements import service as requirements
from app.modules.workpackages import service
from app.modules.workpackages.models import BID_DESK, NEEDS_CHANGE, NEEDS_REASON, OFFERED

router = APIRouter(tags=["workpackages"])
AssignmentId = Path(ge=1, le=2**31 - 1)


class RespondIn(BaseModel):
    compliance: Literal["met", "partial", "deviation", "not_met"]  # = models.OFFERED; "exception" is no longer offered (16.5)
    product_ref: str = ""
    response: str = ""
    reason: str = ""       # required for partial, deviation and not_met (C-12, C-43)
    conditions: str = ""
    workaround: str = ""   # the proposed change: required for deviation (C-43)
    next_steps: str = ""

    @model_validator(mode="after")
    def _partial_needs_reason(self):
        if self.compliance in NEEDS_REASON and not self.reason.strip():
            raise ValueError("Say what is not met or what changes, and why (reason) for a partially compliant, compliant "
                             "with changes or non-compliant answer.")
        if self.compliance in NEEDS_CHANGE and not self.workaround.strip():
            raise ValueError("Say what changes from the requested specification (proposed change) for a compliant-with-changes answer.")
        return self


class CommentIn(BaseModel):
    req_id: str
    text: str
    kind: Literal["question", "comment"] = "comment"   # = models.COMMENT_KINDS
    assignment_id: int | None = Field(None, ge=1, le=2**31 - 1)


class GapIn(BaseModel):
    reason: str
    response: str = ""  # the text the compliance matrix shows (the reason when empty)


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


@router.post("/bids/{opp_id}/dispatch")
def dispatch(opp_id: str, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)  # sending for assessment is the bid manager's (technical-architecture 16.6)
    created = _call(service.dispatch, db, opp_id, actor(request))
    return {"created": created, "needs_owner": len(service.needs_owner(db, opp_id))}


@router.get("/bids/{opp_id}/assessment")
def assessment(opp_id: str, db: Session = Depends(get_db)):
    """The Assessment step (technical-architecture 16.5): bid summary, open questions, participation, routing, progress."""
    return _call(service.assessment, db, opp_id)


@router.get("/bids/{opp_id}/needs-owner")
def needs_owner(opp_id: str, db: Session = Depends(get_db)):
    """Product requirements no participating unit holds: not dispatched until a unit or a capability gap (C-08)."""
    return _call(service.needs_owner, db, opp_id)


@router.post("/bids/{opp_id}/requirements/{req_id}/capability-gap")
def capability_gap(opp_id: str, req_id: str, body: GapIn, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)  # owned by the bid manager (technical-architecture 16.5)
    return row(_call(service.record_gap, db, opp_id, req_id, body.reason, actor(request), body.response))


@router.get("/bids/{opp_id}/handoff/{bu}")
def handoff(opp_id: str, bu: str, db: Session = Depends(get_db)):
    """The unit's hand-off payload (A-09, M8) as a JSON download."""
    payload = _call(service.handoff, db, opp_id, bu)
    return JSONResponse(payload, headers={"Content-Disposition": f'attachment; filename="{opp_id}-{bu}-handoff.json"'})


@router.get("/inbox/{bu}")
def inbox(bu: str, request: Request, db: Session = Depends(get_db)):
    if bu != BID_DESK and catalog.unit(bu) is None:
        raise HTTPException(404, f"Unit {bu} not found.")

    items = service.inbox(db, bu)
    bids = {a.opportunity_id for a in items}
    questions = Counter(c.req_id for o in bids for c in service.open_questions(db, o))
    parts = {k: v for o in bids for k, v in requirements.parts(db, o).items()}  # a group's approved parts
    me, refs = user(request), service.solution_refs(db, items)

    def item(a):
        req = requirements.get(db, a.req_id)  # None if the requirement was deleted after dispatch
        return row(a) | {"requirement": row(req, "source") if req else None, "open_questions": questions[a.req_id],
                         "parts": parts.get(a.req_id, []),  # [{req_id, text}]: the group's approved sub-requirements
                         "may": service.actions(db, a, me),  # what the signed-in user may do with this row (C-25)
                         "solution": catalog.solution(a.bu, refs[a.id]) if refs[a.id] and a.bu != BID_DESK else None}
    return {"bu": bu, "unit": catalog.unit(bu), "compliance": OFFERED, "items": [item(a) for a in items]}


@router.post("/assignments/{assignment_id}/respond")
def respond(body: RespondIn, request: Request, assignment_id: int = AssignmentId, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)  # no administrator; the service checks the workflow's role in the item's unit
    _call(service.respond, db, assignment_id, body.compliance, body.product_ref, body.response, user(request),
          body.reason, body.conditions, body.workaround, body.next_steps)
    return {"ok": True}


@router.get("/bids/{opp_id}/comments")
def comments(opp_id: str, req_id: str | None = None, status: Literal["open", "closed"] | None = None, db: Session = Depends(get_db)):
    """The bid's questions and comments (C-17), oldest first; filter by requirement and status."""
    return [row(c) for c in _call(service.comments, db, opp_id, req_id, status)]


@router.post("/bids/{opp_id}/comments")
def add_comment(opp_id: str, body: CommentIn, request: Request, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)  # the administrator reads only
    try:
        return row(service.add_comment(db, opp_id, body.req_id, body.text, body.kind, actor(request), body.assignment_id))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/comments/{comment_id}/close")
def close_comment(request: Request, comment_id: int = Path(ge=1, le=2**31 - 1), db: Session = Depends(get_db)):
    u = user(request)
    return row(_call(service.close_comment, db, comment_id, u["name"], u["role"] == BID_MANAGER))


@router.get("/assignments/{assignment_id}/history")
def history(assignment_id: int = AssignmentId, db: Session = Depends(get_db)):
    """Every submission, validation, return and change of one assignment, with before and after (C-16)."""
    return _call(service.history, db, assignment_id)


@router.post("/assignments/{assignment_id}/validate")
def validate(body: ValidateIn, request: Request, assignment_id: int = AssignmentId, db: Session = Depends(get_db)):
    require(request, *CORRECTORS)  # the service checks the workflow: the unit manager validates, the bid manager returns
    _call(service.validate, db, assignment_id, body.ok, body.note, user(request))
    return {"ok": True}
