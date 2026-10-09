"""Shared API helpers: the acting user and row serialisation.

Views live in the Next.js app (web/). Controllers return JSON under /api.
"""
from urllib.parse import unquote

from fastapi import Request

DEFAULT_ACTOR = "Bid Manager"


def actor(request: Request) -> str:
    """Who is acting. PoC: picked in the web header and sent as X-Actor (URL-encoded); real sign-in before a pilot."""
    raw = request.headers.get("x-actor") or request.cookies.get("actor")
    name = "".join(ch for ch in unquote(raw or "") if ch.isprintable()).strip()[:80]  # fits the 80-char columns
    return name or DEFAULT_ACTOR


def row(obj, *extra: str) -> dict:
    """A table row as a dict, plus named properties (e.g. row(req, "source"))."""
    data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return data | {name: getattr(obj, name) for name in extra}
