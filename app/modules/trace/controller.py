from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import row
from app.modules.trace import service

router = APIRouter(tags=["trace"])


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db)):
    return [i | {"opp": row(i["opp"])} for i in service.portfolio(db)]


@router.get("/opportunities/{opp_id}/trace")
def trace(opp_id: str, db: Session = Depends(get_db)):
    try:
        t = service.trace(db, opp_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    # The match's retrieval evidence (about half the payload with 840 rows) is shown on the decision page, not here.
    rows = [r | {"req": row(r["req"], "source"),
                 "match": {k: v for k, v in row(r["match"]).items() if k != "evidence"} if r["match"] else None,
                 "assignments": [row(a) for a in r["assignments"]]} for r in t["rows"]]
    return t | {"opp": row(t["opp"]), "doc": row(t["doc"]) if t["doc"] else None, "rows": rows}
