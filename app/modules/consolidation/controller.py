from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import row
from app.modules.consolidation import service

router = APIRouter(tags=["consolidation"])


@router.get("/opportunities/{opp_id}/consolidation")
def coverage(opp_id: str, db: Session = Depends(get_db)):
    cov = service.coverage(db, opp_id)
    rows = [{"requirement": row(r["req"], "source"), "match": row(r["match"]) if r["match"] else None,
             "assignments": [row(a) for a in r["assignments"]], "state": r["state"]} for r in cov["rows"]]
    return cov | {"rows": rows}


@router.get("/opportunities/{opp_id}/compliance-matrix.csv")
def compliance_matrix(opp_id: str, db: Session = Depends(get_db)):
    return Response(service.compliance_matrix_csv(db, opp_id), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{opp_id}-compliance-matrix.csv"'})
