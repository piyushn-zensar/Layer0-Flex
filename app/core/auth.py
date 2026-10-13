"""Sign-in (technical-architecture section 16.6): simple JWT, no refresh tokens, no token store.

Accounts are data (data/accounts.json: username, name, role, bu); the PoC password for all of them is DEMO_PASSWORD.
POST /api/auth/login returns an HS256 token (claims sub, name, role, bu, exp; 8 hours) and sets it in the HttpOnly
cookie layer0_token; the API also accepts it as "Authorization: Bearer <token>" (scripts, tests). Every other /api
route depends on `authenticated` (app/main.py): no valid token is a 401. Expired token: sign in again.
"""
import hmac
import json
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.core import config

COOKIE = "layer0_token"
TTL = 8 * 3600
ROLES = {"bid_manager": "Bid manager", "product_manager": "Product manager", "design_engineer": "Design engineer",
         "admin": "Administrator"}
ACCOUNTS = config.DATA / "accounts.json"

router = APIRouter(tags=["auth"])


def accounts() -> dict[str, dict]:
    return {a["username"]: a for a in json.loads(ACCOUNTS.read_text(encoding="utf-8"))}


def issue(account: dict) -> str:
    claims = {"sub": account["username"], "name": account["name"], "role": account["role"], "bu": account.get("bu"),
              "exp": int(time.time()) + TTL}
    return jwt.encode(claims, config.JWT_SECRET, algorithm="HS256")


def decode(token: str) -> dict | None:
    """The token's claims, or None when it is missing, forged, malformed or expired."""
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None


def authenticated(request: Request) -> dict:
    """Route dependency: the signed-in user's claims (also kept on request.state.user), else 401."""
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else request.cookies.get(COOKIE, "")
    claims = decode(token) if token else None
    if not claims:
        raise HTTPException(401, "Please sign in.", headers={"WWW-Authenticate": "Bearer"})
    request.state.user = claims
    return claims


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def login(body: LoginIn, response: Response):
    if not config.DEMO_PASSWORD:
        raise HTTPException(503, "Sign-in is not set up: set DEMO_PASSWORD in .env and restart the API.")
    account = accounts().get(body.username.strip().lower())
    if not account or not hmac.compare_digest(body.password.encode(), config.DEMO_PASSWORD.encode()):
        raise HTTPException(401, "Wrong username or password.")
    token = issue(account)
    # ponytail: secure=False because the demo runs on http://localhost; set secure=True when served over HTTPS
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite="lax", path="/")
    return {"token": token, "user": decode(token)}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(user: dict = Depends(authenticated)):
    return user | {"role_label": ROLES.get(user["role"], user["role"])}
