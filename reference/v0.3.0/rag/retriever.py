"""
Retriever interface used by agents.

Today this wraps the TF-IDF KnowledgeBaseIndex (indexer.py). If SpinCo
later wants embedding-based semantic retrieval (e.g., over a much larger
corpus of historical BOMs and project documents, where TF-IDF's exact-word
matching becomes too brittle), swap the implementation of `retrieve()`
below for one backed by a vector store (e.g., FAISS + a local embedding
model served through llama.cpp's embedding endpoint). No agent code needs
to change, since all agents depend only on this module's `retrieve(query, k)`
function signature, not on how it's implemented.
"""
from functools import lru_cache

from rag.indexer import KnowledgeBaseIndex

_index: KnowledgeBaseIndex | None = None


def get_index() -> KnowledgeBaseIndex:
    global _index
    if _index is None:
        _index = KnowledgeBaseIndex().load()
    return _index


def retrieve(query: str, k: int = 5):
    """Returns the top-k knowledge base snippets relevant to `query`,
    each with its source doc_id and metadata — used to build the
    evidence trace shown to human approvers."""
    return get_index().retrieve(query, k=k)


def get_full_layer_stack():
    return get_index().get_layer_json()


def get_full_rules():
    return get_index().get_rules_json()
