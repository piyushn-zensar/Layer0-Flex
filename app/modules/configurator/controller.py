from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.llm import LLMUnavailable
from app.core.web import BID_MANAGER, actor, require, row
from app.modules.configurator import explain, service
from app.modules.opportunities import service as opportunities

router = APIRouter(tags=["configurator"])

NOTE = ("Configurator result on the supplied product data, pending engineering review. A run is not proof that the "
        "RFP can be met.")


def _bid(db: Session, opp_id: str) -> None:
    if not opportunities.get(db, opp_id):
        raise HTTPException(404, f"Bid {opp_id} not found.")


def _out(found: dict) -> dict:
    return {"run": row(found["run"]) if found["run"] else None, "components": [row(c) for c in found["components"]],
            "outcomes": explain.OUTCOMES, "note": NOTE}


@router.get("/bids/{opp_id}/components")
def components(opp_id: str, db: Session = Depends(get_db)):
    """The last configurator run (P-56): requested components, outcomes, explanations, candidates."""
    _bid(db, opp_id)
    return _out(service.latest(db, opp_id))


@router.post("/bids/{opp_id}/components")
def assess(opp_id: str, request: Request, db: Session = Depends(get_db)):
    """Run the configurator over the bid's register and store the result (the bid manager asks; the agent proposes)."""
    require(request, BID_MANAGER)
    _bid(db, opp_id)
    try:
        service.assess(db, opp_id, f"configurator ({actor(request)})")
    except LLMUnavailable as exc:
        raise HTTPException(503, f"No frozen model answer for this register: {exc}")
    return _out(service.latest(db, opp_id))


@router.get("/bids/{opp_id}/requirements/{req_id}/components")
def for_requirement(opp_id: str, req_id: str, db: Session = Depends(get_db)):
    """The components of the last run that hold this requirement, and its status there (pane 3)."""
    _bid(db, opp_id)
    return [{"component": row(x["component"]), "requirement": x["requirement"]}
            for x in service.for_requirement(db, opp_id, req_id)]
