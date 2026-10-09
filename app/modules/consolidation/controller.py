import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import row
from app.modules.consolidation import service

router = APIRouter(tags=["consolidation"])


def _match(m) -> dict | None:
    return {k: v for k, v in row(m).items() if k != "evidence"} if m else None  # evidence is for the decision page


def _coverage(db: Session, opp_id: str) -> dict:
    try:
        return service.coverage(db, opp_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/opportunities/{opp_id}/consolidation")
def coverage(opp_id: str, db: Session = Depends(get_db)):
    cov = _coverage(db, opp_id)
    rows = [{"requirement": row(r["req"], "source"), "match": _match(r["match"]),
             "assignments": [row(a) for a in r["assignments"]], "state": r["state"]} for r in cov["rows"]]
    return cov | {"rows": rows}


@router.get("/opportunities/{opp_id}/compliance-matrix.csv")
def compliance_matrix(opp_id: str, db: Session = Depends(get_db)):
    _coverage(db, opp_id)  # 404 for an unknown opportunity
    name = re.sub(r"[^A-Za-z0-9-]", "_", opp_id)[:40]  # header-safe file name
    return Response(service.compliance_matrix_csv(db, opp_id), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{name}-compliance-matrix.csv"'})
