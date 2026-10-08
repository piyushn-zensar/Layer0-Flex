"""Changes: addenda, Q&A and change requests processed as a delta against the frozen baseline.  Owner: Piyush.

Stage 5 (after the Monday demo). Planned contract (technical-architecture.md section 8):
    analyse(db, opp_id, doc_id, actor) -> list[dict]   added / modified / removed / unchanged vs. baseline (difflib)
    apply(db, change_id, actor)                        new requirement versions; affected assignments -> "returned"
Until then this endpoint says so, and the rest of the app runs without it.
"""
from fastapi import APIRouter

router = APIRouter(tags=["changes"])


@router.get("/opportunities/{opp_id}/changes")
def changes(opp_id: str):
    return {"available": False, "stage": 5, "changes": []}
