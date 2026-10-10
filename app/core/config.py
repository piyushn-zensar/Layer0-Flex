"""Every setting in one place, read from the environment (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
KB = DATA / "knowledge_base"          # rules as data: business units, products, past responses
SEED = DATA / "seed"                  # demo data loaded by scripts/seed_demo.py
LLM_CACHE = DATA / "llm_cache"        # committed: frozen model answers (rule R2)
STORE = Path(os.getenv("STORE_DIR", DATA / "store"))  # gitignored: uploads, layouts, page images, DB
STORE.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(STORE / 'layer0.db').as_posix()}")

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

TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD", str(Path(os.getenv("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe")
)
