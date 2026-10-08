from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.requirements import service

router = APIRouter(tags=["requirements"])


class ReviewIn(BaseModel):
    action: str            # approve | reject | edit
    text: str | None = None
    reason: str = ""


@router.get("/opportunities/{opp_id}/requirements")
def requirements(opp_id: str, db: Session = Depends(get_db)):
    b = service.baseline(db, opp_id)
    return {"requirements": [row(r, "source") for r in service.current(db, opp_id, include_rejected=True)],
            "baseline": row(b) if b else None}


@router.post("/opportunities/{opp_id}/requirements/extract")
def extract(opp_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        return service.extract(db, opp_id, actor(request))
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.post("/requirements/{req_id}/review")
def review(req_id: str, body: ReviewIn, request: Request, db: Session = Depends(get_db)):
    try:
        service.review(db, req_id, body.action, actor(request), body.text, body.reason)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return row(service.get(db, req_id), "source")


@router.post("/opportunities/{opp_id}/baselines")
def freeze(opp_id: str, request: Request, db: Session = Depends(get_db)):
    return row(service.freeze(db, opp_id, actor(request)))
