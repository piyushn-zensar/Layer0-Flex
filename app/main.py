"""Layer 0 API - one FastAPI app; each module plugs in its controller under /api (modular monolith).

Views are the Next.js app in web/ (it proxies /api/* here).
Run:  .venv\\Scripts\\python -m uvicorn app.main:app --reload     (API docs: http://127.0.0.1:8000/docs)
"""
import importlib

from fastapi import FastAPI

from app.core import audit, db  # noqa: F401  (audit registers its table)

# Order = workflow order. Every module ships a working (possibly stub) controller, so the app runs at any stage.
MODULES = ["opportunities", "ingestion", "requirements", "catalog", "matching", "decisions",
           "workpackages", "consolidation", "changes", "trace"]

app = FastAPI(title="Layer 0 API - opportunity workflow PoC")
for name in MODULES:
    app.include_router(importlib.import_module(f"app.modules.{name}.controller").router, prefix="/api")
db.init_db()
