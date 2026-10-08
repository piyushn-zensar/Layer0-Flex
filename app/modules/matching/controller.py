from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.matching import service

router = APIRouter(tags=["matching"])


class DecideIn(BaseModel):
    action: Literal["accept", "reject"]


class UnitIn(BaseModel):
    product_id: str
    offering_type: Literal["CTO", "SEMI_CUSTOM", "ETO"]


class ChangeIn(BaseModel):
    units: list[UnitIn]  # empty = not a product item (bid manager)


@router.post("/opportunities/{opp_id}/match")
def match(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return service.match(db, opp_id, f"matching agent ({actor(request)})")  # the agent proposes; the person asked


@router.post("/matches/{match_id}/decide")
def decide(body: DecideIn, request: Request, match_id: int = Path(ge=1, le=2**31 - 1), db: Session = Depends(get_db)):
    try:
        service.decide(db, match_id, body.action, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return {"ok": True}


@router.post("/opportunities/{opp_id}/requirements/{req_id}/match")
def change(opp_id: str, req_id: str, body: ChangeIn, request: Request, db: Session = Depends(get_db)):
    try:
        m = service.set_manual(db, opp_id, req_id, [u.model_dump() for u in body.units], actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return row(m)
