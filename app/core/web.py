"""Shared API helpers: the signed-in user and row serialisation.

Views live in the Next.js app (web/). Controllers return JSON under /api.
"""
from fastapi import HTTPException, Request

from app.core.auth import ROLES


def user(request: Request) -> dict:
    """The signed-in account: token claims sub (username), name, role, bu. Set by auth.authenticated on every /api route."""
    return request.state.user


def actor(request: Request) -> str:
    """Who is acting: the signed-in account's name (stored as the actor in audit events and records)."""
    return user(request)["name"]


# Default permissions (technical-architecture section 16.6), checked on every write route.
BID_MANAGER = "bid_manager"
CORRECTORS = ("bid_manager", "product_manager", "design_engineer")  # extraction corrections, exceptions
# Unit roles (C-25, P-30): the unit manager is the unit's product manager (decided 15 Oct 2026), the stored role value
# stays; designers and engineers keep design_engineer. Shown as ROLES labels ("Unit manager", "Unit designer / engineer").
UNIT_MANAGER = "product_manager"
UNIT_ENGINEER = "design_engineer"
UNIT_ROLES = (UNIT_MANAGER, UNIT_ENGINEER)


def same_unit(u: dict, bu: str) -> bool:
    """A unit role acting on its own unit's item."""
    return u.get("role") in UNIT_ROLES and u.get("bu") == bu


def require(request: Request, *roles: str) -> dict:
    """The signed-in account if its role is one of `roles`, else 403, e.g. require(request, BID_MANAGER)."""
    u = user(request)
    if u["role"] not in roles:
        names = [ROLES.get(r, r).lower() for r in roles]
        allowed = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} or {names[-1]}"
        raise HTTPException(403, f"Only a {allowed} can do this; you are signed in as {u['name']} "
                                 f"({ROLES.get(u['role'], u['role']).lower()}).")
    return u


def row(obj, *extra: str) -> dict:
    """A table row as a dict, plus named properties (e.g. row(req, "source"))."""
    data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return data | {name: getattr(obj, name) for name in extra}
