from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.catalog import service as catalog
from app.modules.decisions import service

router = APIRouter(tags=["decisions"])


class ParticipationIn(BaseModel):
    units: list[str]
    rationale: str = ""


class GoNoGoIn(BaseModel):
    outcome: str  # go | no_go
    rationale: str = ""


@router.get("/opportunities/{opp_id}/decisions")
def decisions(opp_id: str, db: Session = Depends(get_db)):
    p, g = service.latest(db, opp_id, "participation"), service.latest(db, opp_id, "go_no_go")
    return {"evidence": service.evidence(db, opp_id), "units": catalog.units(),
            "participation": row(p) if p else None, "go_no_go": row(g) if g else None}


@router.post("/opportunities/{opp_id}/participation")
def participation(opp_id: str, body: ParticipationIn, request: Request, db: Session = Depends(get_db)):
    return row(service.record(db, opp_id, "participation", "units", body.units, body.rationale, actor(request)))


@router.post("/opportunities/{opp_id}/go-no-go")
def go_no_go(opp_id: str, body: GoNoGoIn, request: Request, db: Session = Depends(get_db)):
    units = service.participating_units(db, opp_id)
    return row(service.record(db, opp_id, "go_no_go", body.outcome, units, body.rationale, actor(request)))
