from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor
from app.modules.matching import service

router = APIRouter(tags=["matching"])


class DecideIn(BaseModel):
    action: Literal["accept", "reject"]


@router.post("/opportunities/{opp_id}/match")
def match(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return service.match(db, opp_id, actor(request))


@router.post("/matches/{match_id}/decide")
def decide(match_id: int, body: DecideIn, request: Request, db: Session = Depends(get_db)):
    try:
        service.decide(db, match_id, body.action, actor(request))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return {"ok": True}
