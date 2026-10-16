from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, actor, require, row

from app.modules.catalog import service

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog(q: str = ""):
    return {"units": service.units(include_pending=True), "products": service.products(), "items": service.items(),
            "results": service.search(q, k=10) if q else []}


@router.get("/catalog/search")
def search(q: str, k: int = Query(5, ge=1, le=50)):
    return service.search(q, k)


@router.get("/people")
def people():
    """Actors for the PoC user picker, with their business unit (None = bid manager)."""
    return [{"name": p, "bu": service.unit_of(p)} for p in service.people()]



@router.get("/catalog/published")
def published(db: Session = Depends(get_db)):
    """The catalog as read from the official Flex pages (P-34): products with earlier names, and the last runs."""
    out = service.published(db)
    return out | {"runs": [row(r) for r in out["runs"]]}


@router.get("/catalog/published/versions")
def versions(key: str, db: Session = Depends(get_db)):
    try:
        return [row(v) for v in service.versions(db, key)]
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.post("/catalog/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    """Refresh now instead of waiting for the daily run (bid manager; the administrator reads only)."""
    require(request, BID_MANAGER)
    return row(service.refresh(db, actor(request)))
