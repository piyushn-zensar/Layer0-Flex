from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, actor, require, row, user
from app.modules.matching import service

router = APIRouter(tags=["matching"])


class DecideIn(BaseModel):
    action: Literal["accept", "reject"]


class UnitIn(BaseModel):
    product_id: str
    offering_type: Literal["CTO", "SEMI_CUSTOM", "ETO"]


class ChangeIn(BaseModel):
    units: list[UnitIn]  # empty = no unit (a non-product item goes to the bid desk, a product item needs an owner)


class RouteIn(BaseModel):
    units: list[str] = Field(default_factory=list, max_length=20)  # business unit codes; empty = no unit


@router.post("/bids/{opp_id}/match")
def match(opp_id: str, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)  # the bid manager runs the matcher; accepting or correcting a match is per item (C-41)
    return service.match(db, opp_id, f"matching agent ({actor(request)})")  # the agent proposes; the person asked


@router.post("/matches/{match_id}/decide")
def decide(body: DecideIn, request: Request, match_id: int = Path(ge=1, le=2**31 - 1), db: Session = Depends(get_db)):
    try:
        service.decide(db, match_id, body.action, user(request))  # C-41: service.may_change decides who
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    return {"ok": True}


@router.post("/bids/{opp_id}/requirements/{req_id}/match")
def change(opp_id: str, req_id: str, body: ChangeIn, request: Request, db: Session = Depends(get_db)):
    try:
        m = service.set_manual(db, opp_id, req_id, [u.model_dump() for u in body.units], user(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return row(m)


@router.post("/bids/{opp_id}/requirements/{req_id}/route")
def route(opp_id: str, req_id: str, body: RouteIn, request: Request, db: Session = Depends(get_db)):
    require(request, BID_MANAGER)  # C-41: the bid manager routes requirements to teams (the unit only)
    try:
        m = service.route(db, opp_id, req_id, body.units, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return row(m)
