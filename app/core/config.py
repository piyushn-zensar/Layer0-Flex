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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")      # mock | azure
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
LLM_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")   # deployment name; part of the cache key

TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD", str(Path(os.getenv("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe")
)
