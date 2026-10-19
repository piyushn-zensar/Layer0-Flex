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
    def __init__(self, items: list[dict], text_key: str = "text", embed: bool = True):
        self.items = items
        self.texts = [it[text_key] for it in items]
        self.vectors = _vectors(self.texts) if embed else None  # embed=False: a keyword-only index (no model call)
        self.mode = "embeddings" if self.vectors is not None else "keywords"
        self._tfidf = None

    def search(self, query: str, k: int = 5, where=None) -> list[dict]:
        """Top-k items as {**item, "score"}; `where` filters items (e.g. one business unit)."""
        return self.search_many([query], k, where)[0]

    def search_many(self, queries: list[str], k: int = 5, where=None) -> list[list[dict]]:
        """search() for many queries with one embedding call (one request instead of one per requirement)."""
        if not self.items:
            return [[] for _ in queries]
        qv = llm.embed([q or " " for q in queries]) if self.vectors is not None else None  # None offline
        out = []
        for i, query in enumerate(queries):
            if not query.strip():
                out.append([])
                continue
            if qv is not None:
                v = np.asarray(qv[i], dtype=np.float32)
                scores = self.vectors @ (v / (np.linalg.norm(v) or 1.0))
            else:
                scores = self._keyword_scores(query)
            out.append(self._top(scores, k, where))
        return out

    def hybrid(self, query: str, k: int = 5, where=None, depth: int = 50, min_keyword: float = 0.0) -> list[dict]:
        """Semantic and keyword results combined by reciprocal rank fusion (P-37, C-29 point 5): an exact term (a
        standard number, a rating) and a paraphrase both rank. Offline (no vectors) it is the keyword ranking.
        score = sum of 1 / (60 + rank) over the two rankings; it orders results and is never a probability."""
        if not query.strip() or not self.items:
            return []
        keyword = self._keyword_scores(query)
        keyword[keyword < min_keyword] = 0  # min_keyword: below it a shared word is no evidence (e.g. only "shall")
        rankings = [self._ranked(keyword, depth, where)]
        if self.vectors is not None and (qv := llm.embed([query])) is not None:
            v = np.asarray(qv[0], dtype=np.float32)
            rankings.append(self._ranked(self.vectors @ (v / (np.linalg.norm(v) or 1.0)), depth, where))
        fused: dict[int, float] = {}
        for ranked in rankings:
            for rank, i in enumerate(ranked):
                fused[i] = fused.get(i, 0.0) + 1.0 / (60 + rank)
        return [{**self.items[i], "score": round(fused[i], 4)} for i in sorted(fused, key=lambda i: (-fused[i], i))[:k]]

    def _keyword_scores(self, query: str) -> np.ndarray:
        if self._tfidf is None:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self._tfidf = (vectorizer, vectorizer.fit_transform(self.texts))
        vectorizer, matrix = self._tfidf
        return cosine_similarity(vectorizer.transform([query]), matrix)[0]

    def _ranked(self, scores, k: int, where) -> list[int]:
        out = []
        for i in np.argsort(-scores, kind="stable"):
            if scores[i] <= 0 or (where and not where(self.items[i])):
                continue
            out.append(int(i))
            if len(out) == k:
                break
        return out

    def _top(self, scores, k: int, where) -> list[dict]:
        return [{**self.items[i], "score": round(float(scores[i]), 3)} for i in self._ranked(scores, k, where)]


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
    fused = idx.hybrid("liability insurance", k=3)
    assert [h["id"] for h in fused] == [2] and 0 < fused[0]["score"] < 1, fused  # keyword ranking offline
    print("vectors ok, mode:", idx.mode)
