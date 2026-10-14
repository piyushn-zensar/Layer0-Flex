"""Sign-in (technical-architecture section 16.6): simple JWT, no refresh tokens, no token store.

Accounts live in the table user_account (username, name, role, bu, password_hash) of AUTH_DATABASE_URL: MySQL when
MYSQL_HOST is set, else the local SQLite store. init() creates the table and adds every account of data/accounts.json
it does not hold yet, with DEMO_PASSWORD as its starting password; scripts.set_password changes one. Passwords are kept
only as salted PBKDF2-SHA256 hashes (standard library).
POST /api/auth/login returns an HS256 token (claims sub, name, role, bu, exp; 8 hours) and sets it in the HttpOnly
cookie layer0_token; the API also accepts it as "Authorization: Bearer <token>" (scripts, tests). Every other /api
route depends on `authenticated` (app/main.py): no valid token is a 401. Expired token: sign in again.
"""
import hashlib
import hmac
import json
import os
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.core import config, db

COOKIE = "layer0_token"
TTL = 8 * 3600
ROLES = {"bid_manager": "Bid manager", "product_manager": "Product manager", "design_engineer": "Design engineer",
         "admin": "Administrator"}
ACCOUNTS = config.DATA / "accounts.json"   # the roster seeded into the accounts table
ROUNDS = 600_000                           # PBKDF2-SHA256 iterations (OWASP 2023); about 0.4 s per hash

router = APIRouter(tags=["auth"])

# Own engine and metadata: the accounts are not workflow data (db.init_db and a demo reset never touch them)
engine = db.engine if config.AUTH_DATABASE_URL == config.DATABASE_URL else create_engine(
    config.AUTH_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)


class _Base(DeclarativeBase):
    pass


class Account(_Base):
    __tablename__ = "user_account"
    username: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32))
    bu: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str | None] = mapped_column(String(255))

    def profile(self) -> dict:
        return {"username": self.username, "name": self.name, "role": self.role, "bu": self.bu}


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ROUNDS)
    return f"pbkdf2_sha256${ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    try:
        scheme, rounds, salt, digest = (stored or "").split("$")
    except ValueError:
        return False
    found = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
    return scheme == "pbkdf2_sha256" and hmac.compare_digest(found, digest)


def init() -> None:
    """Create the accounts database and table, and bring them in step with data/accounts.json: missing accounts are
    added, name, role and bu follow the file, a password is never overwritten (only a missing one gets DEMO_PASSWORD)."""
    if engine.dialect.name == "mysql":
        server = create_engine(engine.url.set(database="information_schema"))   # the one database that always exists
        with server.begin() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{engine.url.database}` CHARACTER SET utf8mb4"))
        server.dispose()
    _Base.metadata.create_all(engine)
    seeded = None   # one hash for every seeded account: they share DEMO_PASSWORD anyway, and 18 hashes take 7 s
    with Session(engine) as s, s.begin():
        for a in json.loads(ACCOUNTS.read_text(encoding="utf-8")):
            row = s.get(Account, a["username"]) or Account(username=a["username"])
            row.name, row.role, row.bu = a["name"], a["role"], a.get("bu")
            if not row.password_hash and config.DEMO_PASSWORD:
                row.password_hash = seeded = seeded or hash_password(config.DEMO_PASSWORD)
            s.add(row)


def accounts() -> dict[str, dict]:
    with Session(engine) as s:
        return {a.username: a.profile() for a in s.scalars(select(Account))}


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
    with Session(engine) as s:
        account = s.get(Account, body.username.strip().lower())
    if account and not account.password_hash:
        raise HTTPException(503, f"No password is set for {account.username}: set DEMO_PASSWORD in .env and restart "
                                 "the API, or run '.venv\\Scripts\\python -m scripts.set_password <username>'.")
    if not account or not verify_password(body.password, account.password_hash):
        raise HTTPException(401, "Wrong username or password.")
    token = issue(account.profile())
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
