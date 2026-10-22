from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import row, user
from app.modules.matching import service as matching
from app.modules.trace import service

router = APIRouter(tags=["trace"])


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db)):
    return [i | {"opp": row(i["opp"])} for i in service.portfolio(db)]


@router.get("/bids/{opp_id}/trace")
def trace(opp_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        t = service.trace(db, opp_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    # The match's retrieval evidence (about half the payload with 840 rows) is shown on the decision page, not here.
    # "bboxes" is the view's highlight (a group's comes from its current sub-requirements): it replaces the stored one.
    u = user(request)  # can_change (P-44): may this account accept, reject or change the row's match (C-41)
    rows = [{k: v for k, v in r.items() if k != "bboxes"}
            | {"req": row(r["req"], "source") | {"bboxes": r["bboxes"]},
               "match": {k: v for k, v in row(r["match"]).items() if k != "evidence"} if r["match"] else None,
               "assignments": [row(a) for a in r["assignments"]],
               "children": [{"req_id": k.req_id, "text": k.text, "source": k.source, "document_id": k.document_id}
                            for k in r["children"]],
               "can_change": matching.may_change(u, r["req"].category, r["match"])}
            for r in t["rows"]]
    return t | {"opp": row(t["opp"]), "doc": row(t["doc"]) if t["doc"] else None, "rows": rows}
