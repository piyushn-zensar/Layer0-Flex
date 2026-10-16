"""Sign-in (technical-architecture section 16.6): simple JWT, no refresh tokens, no token store.

Accounts live in the table user_account (username, name, role, bu, password_hash) of AUTH_DATABASE_URL: MySQL when
MYSQL_HOST is set, else the local SQLite store. init() creates the table and adds every account of data/accounts.json
it does not hold yet, with DEMO_PASSWORD as its starting password; scripts.set_password changes one. Passwords are kept
only as salted PBKDF2-SHA256 hashes (standard library).
POST /api/auth/login returns an HS256 token (claims sub, name, role, bu, exp; 8 hours) and sets it in the HttpOnly
cookie layer0_token; the API also accepts it as "Authorization: Bearer <token>" (scripts, tests). Every other /api
route depends on `authenticated` (app/main.py): no valid token is a 401. Expired token: sign in again.
Sign-up (P-31, C-26): POST /api/auth/signup creates an account with the role the person chooses (bid manager, unit
manager, unit designer / engineer; never administrator, which only the roster seeds) and signs it in; GET
/api/auth/units lists the units to choose from. Roster usernames cannot be signed up; init() only touches roster
accounts. Repeated failed sign-ins (per username) and sign-ups (per address) are refused for a while (429). The
administrator reads only: `authenticated` refuses its writes on every module route (403).
"""
import hashlib
import hmac
import json
import os
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import String, create_engine, func, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.core import config, db

COOKIE = "layer0_token"
TTL = 8 * 3600
# Stored role values stay; the unit roles are shown as Unit manager and Unit designer / engineer (C-25, P-30; the unit
# manager is the unit's product manager, decided 15 Oct 2026).
ROLES = {"bid_manager": "Bid manager", "product_manager": "Unit manager", "design_engineer": "Unit designer / engineer",
         "admin": "Administrator"}
ACCOUNTS = config.DATA / "accounts.json"   # the roster seeded into the accounts table
ROUNDS = 600_000                           # PBKDF2-SHA256 iterations (OWASP 2023); about 0.4 s per hash
SIGNUP_ROLES = ("bid_manager", "product_manager", "design_engineer")  # never admin: seeded by the server (C-26)
MIN_PASSWORD = 10
MAX_FAILURES, WINDOW = 5, 300              # failed attempts per key within WINDOW seconds, then 429 until they age out
_failures: dict[str, list[float]] = {}     # ponytail: in this process only; one API process in the PoC, a shared store when scaled

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


def _limited(key: str) -> None:
    """429 while `key` has MAX_FAILURES failed attempts within the last WINDOW seconds."""
    now = time.time()
    recent = _failures[key] = [t for t in _failures.get(key, []) if now - t < WINDOW]
    if len(recent) >= MAX_FAILURES:
        raise HTTPException(429, f"Too many failed attempts. Try again in {int(WINDOW - (now - recent[0])) + 1} seconds.")


def _failed(key: str, status: int, detail: str) -> HTTPException:
    _failures.setdefault(key, []).append(time.time())
    return HTTPException(status, detail)


def _units() -> dict[str, str]:
    """Active business units, code -> name, for sign-up."""
    # ponytail: read from the catalog's data file (core does not import modules); switch when P-34 moves units to tables
    data = json.loads((config.DATA / "knowledge_base" / "business_units.json").read_text(encoding="utf-8"))
    return {u["code"]: u["name"] for u in data["units"] if u.get("status") == "active"}


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
    if claims["role"] == "admin" and request.method not in ("GET", "HEAD", "OPTIONS"):  # 16.6: the administrator reads only
        raise HTTPException(403, "The administrator reads only; sign in with a bid or unit role to make changes.")
    request.state.user = claims
    return claims


class LoginIn(BaseModel):
    username: str
    password: str


def _signed_in(account: Account, response: Response) -> dict:
    token = issue(account.profile())
    # ponytail: secure=False because the demo runs on http://localhost; set secure=True when served over HTTPS
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite="lax", path="/")
    return {"token": token, "user": decode(token)}


@router.post("/auth/login")
def login(body: LoginIn, response: Response):
    username = body.username.strip().lower()
    key = f"login:{username}"
    _limited(key)
    with Session(engine) as s:
        account = s.get(Account, username)
    if account and not account.password_hash:
        raise HTTPException(503, f"No password is set for {account.username}: set DEMO_PASSWORD in .env and restart "
                                 "the API, or run '.venv\\Scripts\\python -m scripts.set_password <username>'.")
    if not account or not verify_password(body.password, account.password_hash):
        raise _failed(key, 401, "Wrong username or password.")
    _failures.pop(key, None)
    return _signed_in(account, response)


class SignupIn(BaseModel):
    username: str
    name: str
    password: str
    role: str
    bu: str | None = None


@router.get("/auth/units")
def units():
    """The business units a unit manager or unit designer / engineer can sign up for (public: used before sign-in)."""
    return [{"code": code, "name": name} for code, name in _units().items()]


@router.post("/auth/signup")
def signup(body: SignupIn, request: Request, response: Response):
    key = f"signup:{request.client.host if request.client else ''}"
    _limited(key)
    username, name = body.username.strip().lower(), " ".join(body.name.split())
    unit_role = body.role in ("product_manager", "design_engineer")
    roster = {a["username"] for a in json.loads(ACCOUNTS.read_text(encoding="utf-8"))}
    if not (3 <= len(username) <= 64) or not all(c.isalnum() or c in "._-" for c in username):
        raise _failed(key, 422, "Choose a username of 3 to 64 letters, digits, dots, dashes or underscores.")
    if not (2 <= len(name) <= 128):
        raise _failed(key, 422, "Enter the name to show on your records (2 to 128 characters).")
    if len(body.password) < MIN_PASSWORD:
        raise _failed(key, 422, f"Choose a password of at least {MIN_PASSWORD} characters.")
    if body.role not in SIGNUP_ROLES:
        raise _failed(key, 422, "Choose bid manager, unit manager or unit designer / engineer; the administrator "
                                "account is set up by the server.")
    if unit_role and body.bu not in _units():
        raise _failed(key, 422, "Choose your business unit.")
    with Session(engine) as s, s.begin():
        if username in roster or s.get(Account, username):
            raise _failed(key, 409, f"The username {username} is taken; choose another.")
        if s.scalar(select(Account).where(func.lower(Account.name) == name.lower())):
            raise _failed(key, 409, f"Someone already uses the name {name}; add an initial or your unit.")
        account = Account(username=username, name=name, role=body.role, bu=body.bu if unit_role else None,
                          password_hash=hash_password(body.password))
        s.add(account)
        s.flush()
        s.expunge(account)
    return _signed_in(account, response)


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(user: dict = Depends(authenticated)):
    return user | {"role_label": ROLES.get(user["role"], user["role"])}
