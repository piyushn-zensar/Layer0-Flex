"""
Builds a lightweight retrieval index over the SpinCo knowledge base.

Deliberately uses TF-IDF (scikit-learn) rather than an embedding model:
it requires no model download, runs instantly on CPU, and is transparent
(the retrieval score is directly explainable — "these words matched"),
which matters for an explainability-first system. This can be swapped
for an embedding-based retriever later (see retriever.py docstring)
without changing any calling code, since both implement the same
`retrieve(query, k)` interface.
"""
import json
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import settings


@dataclass
class KBDocument:
    doc_id: str
    text: str
    metadata: dict


def _flatten_layers_to_documents(layers_json: dict) -> List[KBDocument]:
    """Turns the structured layers JSON into retrievable text chunks,
    one per layer, so retrieval can point back to a specific layer's
    rules and brands (needed for the evidence trace)."""
    docs = []
    for layer in layers_json["layers"]:
        # brands is now a list of {"name", "automation_tier", "tier_rationale"}
        # objects, not plain strings — include the tier in the indexed text
        # so retrieval can surface "why this brand is tiered this way"
        # directly, not just which brands exist.
        brand_summary = ", ".join(f"{b['name']} ({b['automation_tier']})" for b in layer["brands"])
        text = (
            f"Layer {layer['n']}: {layer['name']}. "
            f"Brands: {brand_summary}. "
            f"{layer['description']} "
            f"Selection rules: {' '.join(layer['selection_rules'])}"
        )
        docs.append(KBDocument(
            doc_id=f"layer-{layer['n']}",
            text=text,
            metadata={"type": "layer", "n": layer["n"], "name": layer["name"], "brands": layer["brands"]},
        ))
    return docs


def _flatten_rules_to_documents(rules_json: dict) -> List[KBDocument]:
    docs = []
    for rule in rules_json.get("per_layer_constraints", []):
        docs.append(KBDocument(
            doc_id=rule["id"],
            text=f"Rule {rule['id']} (applies to layers {rule['applies_to_layers']}, severity {rule['severity']}): {rule['rule']}",
            metadata={"type": "per_layer_rule", **rule},
        ))
    for rule in rules_json.get("cross_layer_compatibility", []):
        docs.append(KBDocument(
            doc_id=rule["id"],
            text=f"Cross-layer rule {rule['id']} (severity {rule['severity']}): {rule['rule']}",
            metadata={"type": "cross_layer_rule", **rule},
        ))
    return docs


class KnowledgeBaseIndex:
    """A minimal, fast, fully local TF-IDF index. Call .load() once,
    then .retrieve(query, k) as many times as needed."""

    def __init__(self):
        self.documents: List[KBDocument] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None

    def load(self):
        with open(settings.LAYERS_FILE) as f:
            layers_json = json.load(f)
        with open(settings.RULES_FILE) as f:
            rules_json = json.load(f)

        self.documents = (
            _flatten_layers_to_documents(layers_json)
            + _flatten_rules_to_documents(rules_json)
        )
        corpus = [d.text for d in self.documents]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)
        return self

    def retrieve(self, query: str, k: int = 5):
        if self._vectorizer is None:
            raise RuntimeError("KnowledgeBaseIndex.load() must be called before retrieve().")
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(zip(self.documents, scores), key=lambda x: x[1], reverse=True)
        return [
            {"doc_id": doc.doc_id, "text": doc.text, "metadata": doc.metadata, "score": float(score)}
            for doc, score in ranked[:k]
            if score > 0
        ]

    def get_layer_json(self):
        """Returns the raw layers JSON — used by agents that need the
        full structured stack, not just retrieved snippets."""
        with open(settings.LAYERS_FILE) as f:
            return json.load(f)

    def get_rules_json(self):
        with open(settings.RULES_FILE) as f:
            return json.load(f)
