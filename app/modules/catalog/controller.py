from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.web import BID_MANAGER, UNIT_ENGINEER, UNIT_MANAGER, actor, require, row

from app.modules.catalog import service

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog(q: str = ""):
    return {"units": service.units(include_pending=True), "products": service.products(), "items": service.items(),
            "results": service.search(q, k=10) if q else []}


@router.get("/catalog/search")
def search(q: str, k: int = Query(5, ge=1, le=50)):
    return service.search(q, k)


@router.get("/catalog/products")
def products(q: str = "", type: str | None = None, family: str | None = None, status: str | None = None,
             interface: str | None = None, application: str | None = None, sort: str = "part_number",
             dir: Literal["asc", "desc"] = "asc", page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    """All products (P-53, C-60): spreadsheet parts and the web catalog, one row each; contract in PLAN 12.3."""
    try:
        return service.product_rows(q, type, family, status, interface, application, sort, dir, page, size)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/catalog/product")
def product(part: str, db: Session = Depends(get_db)):
    """One product by part number or catalog ID (a query parameter: part numbers contain "/"), with its family's
    extracted ratings ("specs", unverified until the unit confirms them)."""
    p = service.product_detail(part, db)
    if p is None:
        raise HTTPException(404, f"no product {part!r}")
    return p


@router.get("/catalog/file")
def product_file(path: str):
    """A product document, fetched page or image listed in the manifests (J-20: open a datasheet at its page; J-19 images)."""
    try:
        full, media = service.product_file(path)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return FileResponse(full, media_type=media, headers={"Cache-Control": "private, max-age=3600"})


@router.get("/catalog/specs")
def specs(family: str | None = None, db: Session = Depends(get_db)):
    """Ratings read from the product documents and official pages, with the unit's review (C-52 follow-up)."""
    return service.specs(db, family)


class SpecReviewIn(BaseModel):
    status: Literal["confirmed", "rejected"]
    note: str = Field("", max_length=2000)


@router.post("/catalog/specs/{spec_id}/review")
def review_spec(spec_id: str, body: SpecReviewIn, request: Request, db: Session = Depends(get_db)):
    """The family's unit (manager or designer / engineer) confirms or rejects an extracted spec item."""
    u = require(request, UNIT_MANAGER, UNIT_ENGINEER)
    try:
        return row(service.review_spec(db, spec_id, body.status, body.note, u))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))


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
