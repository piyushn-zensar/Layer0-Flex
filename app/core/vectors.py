"""Vector indexes for retrieval (RAG). Two kinds are used:

- long-term:  the knowledge base the system learns into (products, past responses); catalog module.
- short-term: one RFP, split into passages with page and line numbers; rebuilt whenever that RFP is loaded
              (ingestion module). Lives with the opportunity, never mixed with another one (rule R6).

Embeddings come from the model gateway (app/core/llm.embed). Like model answers they are frozen: the vectors of a
set of texts are stored in data/vector_cache/<hash>.npy, keyed by the embedding model, its size and the texts, and
committed for the sample RFPs and the knowledge base. Rebuilding an index over unchanged text therefore costs
nothing. Without an embedding provider and without frozen vectors, an index falls back to keyword (TF-IDF) search
and reports mode "keywords", so everything keeps working offline.

ponytail: numpy cosine search over a few thousand vectors is instant; move to a vector database (pgvector, Chroma)
when an index reaches hundreds of thousands of passages.
"""
import hashlib
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core import config, llm


class Index:
    def __init__(self, items: list[dict], text_key: str = "text"):
        self.items = items
        self.texts = [it[text_key] for it in items]
        self.vectors = _vectors(self.texts)
        self.mode = "embeddings" if self.vectors is not None else "keywords"
        self._tfidf = None

    def search(self, query: str, k: int = 5, where=None) -> list[dict]:
        """Top-k items as {**item, "score"}; `where` filters items (e.g. one business unit)."""
        if not query.strip() or not self.items:
            return []
        scores = None
        if self.vectors is not None:
            q = llm.embed([query])  # None offline: then keyword scoring for this query
            if q is not None:
                v = np.asarray(q[0], dtype=np.float32)
                scores = self.vectors @ (v / (np.linalg.norm(v) or 1.0))
        if scores is None:
            if self._tfidf is None:
                vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
                self._tfidf = (vectorizer, vectorizer.fit_transform(self.texts))
            vectorizer, matrix = self._tfidf
            scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
        order = np.argsort(-scores, kind="stable")
        out = []
        for i in order:
            if scores[i] <= 0 or (where and not where(self.items[i])):
                continue
            out.append({**self.items[i], "score": round(float(scores[i]), 3)})
            if len(out) == k:
                break
        return out


def _vectors(texts: list[str]) -> np.ndarray | None:
    """Unit-length vectors for the texts: frozen file, else the embedding provider, else None."""
    if not texts:
        return None
    key = hashlib.sha256(json.dumps([config.EMBEDDING_MODEL, config.EMBEDDING_DIMS, texts]).encode()).hexdigest()[:24]
    path = config.VECTOR_CACHE / f"{key}.npy"
    if path.exists():
        return np.load(path).astype(np.float32)
    raw = llm.embed(texts)
    if raw is None:
        return None
    m = np.asarray(raw, dtype=np.float32)
    m /= np.linalg.norm(m, axis=1, keepdims=True).clip(min=1e-12)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, m.astype(np.float16))  # half precision: a few hundred KB per RFP, plenty for ranking
    return m


if __name__ == "__main__":  # self-check (offline): python -m app.core.vectors
    idx = Index([{"id": 1, "text": "Arc-resistant metal-clad switchgear, 15 kV"},
                 {"id": 2, "text": "Commercial general liability insurance limits"},
                 {"id": 3, "text": "Direct-to-chip liquid cooling for racks"}])
    hits = idx.search("switchgear rated 15 kV", k=2)
    assert hits[0]["id"] == 1, hits
    assert idx.search("insurance", where=lambda it: it["id"] != 2) == []
    print("vectors ok, mode:", idx.mode)
