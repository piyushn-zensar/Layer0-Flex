from fastapi import APIRouter

from app.modules.catalog import service

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog(q: str = ""):
    return {"units": service.units(include_pending=True), "products": service.products(),
            "results": service.search(q, k=10) if q else []}


@router.get("/catalog/search")
def search(q: str, k: int = 5):
    return service.search(q, k)


@router.get("/people")
def people():
    """Actors for the PoC user picker, with their business unit (None = bid manager)."""
    return [{"name": p, "bu": service.unit_of(p)} for p in service.people()]
