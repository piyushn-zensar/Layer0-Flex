"""Layer 0 API - one FastAPI app; each module plugs in its controller under /api (modular monolith).

Views are the Next.js app in web/ (it proxies /api/* here).
Run:  .venv\\Scripts\\python -m uvicorn app.main:app --reload     (API docs: http://127.0.0.1:8000/docs)
"""
import importlib
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.core import audit, auth, config, db  # noqa: F401  (audit registers its table)

# Order = workflow order. Every module ships a working (possibly stub) controller, so the app runs at any stage.
MODULES = ["opportunities", "ingestion", "requirements", "catalog", "matching", "decisions",
           "workpackages", "consolidation", "knowledge", "changes", "trace", "configurator"]

@asynccontextmanager
async def lifespan(_app):
    """P-34: refresh the published catalog on start and every CATALOG_REFRESH_HOURS (0 = never), in a daemon thread,
    so start-up never waits for the network and a failed page never stops the API."""
    if config.CATALOG_REFRESH_HOURS > 0:
        from app.modules.catalog import service as catalog
        threading.Thread(target=catalog.refresh_forever, name="catalog-refresh", daemon=True).start()
    yield


app = FastAPI(title="Layer 0 API - opportunity workflow PoC", lifespan=lifespan)
app.include_router(auth.router, prefix="/api")  # sign-in; every module route below needs a valid token (401 otherwise)
for name in MODULES:
    app.include_router(importlib.import_module(f"app.modules.{name}.controller").router, prefix="/api",
                       dependencies=[Depends(auth.authenticated)])
db.init_db()
auth.init()
with db.SessionLocal() as _s:  # a background read stopped by a restart is read again on the next upload (19 Oct review)
    importlib.import_module("app.modules.opportunities.service").reset_interrupted_reads(_s)
