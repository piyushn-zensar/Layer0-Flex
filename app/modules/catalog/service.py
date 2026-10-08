"""Catalog: business units, products, past responses and the retrieval (RAG) index.  Owner: Atharv.

Rules as data (rule R7): everything here is read from data/knowledge_base/*.json.

Public contract:
    units(include_pending=False) -> list[dict]
    unit(code) -> dict | None
    products(bu=None) -> list[dict]
    product(product_id) -> dict | None
    search(query, k=5, bu=None) -> list[dict]   ranked products and past responses, each with "score"
    bom(product_id) -> list[dict]               BOM lines from the BOM source system (stub: catalog JSON)
    people() -> list[str]                       actors for the PoC user picker
    unit_of(actor) -> str | None                business-unit code of a product manager / design engineer
"""
import json
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core import config


@lru_cache
def _load(name: str) -> dict:
    return json.loads((config.KB / f"{name}.json").read_text("utf-8"))


def units(include_pending: bool = False) -> list[dict]:
    return [u for u in _load("business_units")["units"] if include_pending or u["status"] == "active"]


def unit(code: str) -> dict | None:
    return next((u for u in units(include_pending=True) if u["code"] == code), None)


def products(bu: str | None = None) -> list[dict]:
    active = {u["code"] for u in units()}
    return [p for p in _load("products")["products"] if p["bu"] in active and (bu is None or p["bu"] == bu)]


def product(product_id: str) -> dict | None:
    return next((p for p in _load("products")["products"] if p["id"] == product_id), None)


@lru_cache
def _index():
    """TF-IDF over products and past responses (ported from v0.3.0 rag/indexer.py).
    ponytail: TF-IDF keyword retrieval; swap for embeddings when the catalog outgrows exact-word matching."""
    docs = [{"kind": "product", "id": p["id"], "bu": p["bu"], "offering_type": p["offering_type"],
             "text": f"{p['name']}. {p['description']} {p['keywords']}"} for p in products()]
    docs += [{"kind": "past_response", "id": r["id"], "bu": r["bu"],
              "text": f"{r['requirement']} {r['response']}"} for r in _load("past_responses")["responses"]]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    return docs, vectorizer, vectorizer.fit_transform([d["text"] for d in docs])


def search(query: str, k: int = 5, bu: str | None = None) -> list[dict]:
    docs, vectorizer, matrix = _index()
    scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [{**d, "score": round(float(s), 3)} for d, s in ranked if s > 0 and (bu is None or d["bu"] == bu)][:k]


def bom(product_id: str) -> list[dict]:
    """ponytail: reads the catalog JSON; replace with the real BOM system connector (Needs confirmation which one)."""
    p = product(product_id)
    return p["bom"] if p else []


def people() -> list[str]:
    return ["Bid Manager"] + [name for u in units() for name in (u["product_manager"], u["design_engineer"])]


def unit_of(actor: str) -> str | None:
    return next((u["code"] for u in units() if actor in (u["product_manager"], u["design_engineer"])), None)


if __name__ == "__main__":  # self-check: python -m app.modules.catalog.service
    first_product = lambda q: next(h for h in search(q) if h["kind"] == "product")["id"]
    assert first_product("Switchgear shall be Arc-resistant Type 2B") == "CROWN-ARMV"
    assert first_product("Furnish relays, controls and associated accessories and hardware") == "EP2-RPP"
    assert unit_of("EP² Design Engineer") == "EP2"
    print("catalog ok")
