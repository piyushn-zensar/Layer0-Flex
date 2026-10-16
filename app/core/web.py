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
UNIT_MANAGER = "product_manager"    # shown as "Unit manager" (C-25): the unit's manager validates its responses
UNIT_ENGINEER = "design_engineer"   # shown as "Unit designer / engineer": answers the unit's technical items
UNIT_ROLES = (UNIT_MANAGER, UNIT_ENGINEER)
CORRECTORS = (BID_MANAGER, *UNIT_ROLES)  # extraction corrections, exceptions


def same_unit(u: dict, bu: str | None) -> bool:
    """True when the signed-in account holds a unit role in business unit `bu` (role and unit from the token)."""
    return u["role"] in UNIT_ROLES and bool(bu) and u.get("bu") == bu


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
