"""Every setting in one place, read from the environment (.env)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
KB = DATA / "knowledge_base"          # rules as data: business units, products, past responses
SEED = DATA / "seed"                  # demo data loaded by scripts/seed_demo.py
LLM_CACHE = DATA / "llm_cache"        # committed: frozen model answers (rule R2)
STORE = Path(os.getenv("STORE_DIR", DATA / "store"))  # gitignored: uploads, layouts, page images, DB
STORE.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(STORE / 'layer0.db').as_posix()}")

# Sign-in accounts live in MySQL when MYSQL_HOST is set (the database is created on first start), else in DATABASE_URL.
# Kept apart from the workflow data, so a demo reset never touches users or their passwords.
AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL") or (
    URL.create("mysql+pymysql", username=os.getenv("MYSQL_USER") or None, password=os.getenv("MYSQL_PASSWORD") or None,
               host=os.getenv("MYSQL_HOST"), port=int(os.getenv("MYSQL_PORT") or 3306),
               database=os.getenv("MYSQL_DB") or "layer0", query={"charset": "utf8mb4"})
    if os.getenv("MYSQL_HOST") else DATABASE_URL)

# Azure OpenAI. The second name of each pair is the team's shared .env naming.
LLM_PROVIDER = os.getenv("LLM_PROVIDER") or os.getenv("MODEL_PROVIDER") or "mock"   # mock | azure
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("ENDPOINT_URL") or ""
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("API_VERSION") or "2024-10-21"
LLM_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("DEPLOYMENT_NAME") or "gpt-4o"  # part of the cache key
EMBEDDING_MODEL = os.getenv("EMBEDDING_DEPLOYMENT_NAME") or "text-embedding-3-small"   # Azure deployment name
EMBEDDING_API_VERSION = os.getenv("EMBEDDING_API_VERSION") or "2024-02-01"
EMBEDDING_DIMS = 256                                   # text-embedding-3 can shorten its vectors; plenty for retrieval
VECTOR_CACHE = DATA / "vector_cache"                   # committed: frozen embeddings of sample RFPs and the knowledge base

# Sign-in (technical-architecture 16.6). Without JWT_SECRET a random one is made once per machine and kept in the
# store (gitignored), so tokens survive restarts. DEMO_PASSWORD is the starting password of every account seeded from
# data/accounts.json; empty = seeded accounts get no password and cannot sign in until scripts.set_password.
_SECRET_FILE = STORE / "jwt_secret"
if not os.getenv("JWT_SECRET") and not _SECRET_FILE.exists():
    _SECRET_FILE.write_text(secrets.token_urlsafe(32), encoding="utf-8")
JWT_SECRET = os.getenv("JWT_SECRET") or _SECRET_FILE.read_text(encoding="utf-8").strip()
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")

TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD", str(Path(os.getenv("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe")
)
