from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import actor, row
from app.modules.catalog import service as catalog
from app.modules.decisions import service
from app.modules.opportunities import service as opportunities

router = APIRouter(tags=["decisions"])


class ParticipationIn(BaseModel):
    units: list[str]
    rationale: str = ""


class CriterionIn(BaseModel):
    id: str
    status: Literal["met", "not_met", "unknown"]
    note: str = ""


class GoNoGoIn(BaseModel):
    outcome: Literal["go", "no_go"]
    rationale: str = ""
    criteria: list[CriterionIn] = []  # the person's judgement per criterion (A-12)


@router.get("/opportunities/{opp_id}/decisions")
def decisions(opp_id: str, db: Session = Depends(get_db)):
    try:
        opportunities.require(db, opp_id)  # an unknown opportunity is a 404, not an empty evidence pack
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    p, g = service.latest(db, opp_id, "participation"), service.latest(db, opp_id, "go_no_go")
    ev = service.evidence(db, opp_id)
    return {"evidence": ev, "summary": service.summary(db, opp_id, ev) if ev["frozen"] else None, "units": catalog.units(),
            "participation": row(p) if p else None, "go_no_go": row(g) if g else None}


def _record(db: Session, opp_id: str, kind: str, outcome: str, units: list[str], rationale: str, who: str,
            bad_input: int, criteria: list[dict] | None = None) -> dict:
    try:
        return row(service.record(db, opp_id, kind, outcome, units, rationale, who, criteria))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(bad_input, str(exc))


@router.post("/opportunities/{opp_id}/participation")
def participation(opp_id: str, body: ParticipationIn, request: Request, db: Session = Depends(get_db)):
    return _record(db, opp_id, "participation", "units", body.units, body.rationale, actor(request), 422)


@router.post("/opportunities/{opp_id}/go-no-go")
def go_no_go(opp_id: str, body: GoNoGoIn, request: Request, db: Session = Depends(get_db)):
    known = {c["id"] for c in catalog.go_no_go()["criteria"]}
    if unknown := [c.id for c in body.criteria if c.id not in known]:
        raise HTTPException(422, f"Unknown criteria: {unknown}.")
    units = service.participating_units(db, opp_id)
    return _record(db, opp_id, "go_no_go", body.outcome, units, body.rationale, actor(request), 409,
                   [c.model_dump() for c in body.criteria])
