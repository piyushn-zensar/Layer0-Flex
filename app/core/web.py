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


def require(request: Request, *roles: str) -> dict:
    """The signed-in account if its role is one of `roles`, else 403, e.g. require(request, "bid_manager")."""
    u = user(request)
    if u["role"] not in roles:
        allowed = " or ".join(ROLES.get(r, r).lower() for r in roles)
        raise HTTPException(403, f"Only a {allowed} can do this; you are signed in as {u['name']}.")
    return u


def row(obj, *extra: str) -> dict:
    """A table row as a dict, plus named properties (e.g. row(req, "source"))."""
    data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return data | {name: getattr(obj, name) for name in extra}
