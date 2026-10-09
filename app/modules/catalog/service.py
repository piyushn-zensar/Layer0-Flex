"""Catalog: business units, products, past responses and the retrieval (RAG) index.  Owner: Atharv.

Rules as data (rule R7): everything here is read from data/knowledge_base/*.json.

Public contract:
    units(include_pending=False) -> list[dict]
    unit(code) -> dict | None
    products(bu=None) -> list[dict]
    product(product_id) -> dict | None
    search(query, k=5, bu=None) -> list[dict]   ranked products and past responses, each with "score"
    bom(product_id) -> list[dict]               BOM lines from the BOM source system (stub: catalog JSON)
    layers() -> dict                            grid-to-chip layers, scope keywords, unit tiers (spinco_layers.json)
    engineering_rules() -> dict                 rules R-001..R-004 and generic NEC/IEC values (engineering_rules.json)
    go_no_go() -> dict                          go/no-go criteria and placeholder thresholds (go_no_go.json)
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


def layers() -> dict:
    return _load("spinco_layers")


def engineering_rules() -> dict:
    return _load("engineering_rules")


def go_no_go() -> dict:
    return _load("go_no_go")


def people() -> list[str]:
    return ["Bid Manager"] + [name for u in units() for name in (u["product_manager"], u["design_engineer"])]


def unit_of(actor: str) -> str | None:
    return next((u["code"] for u in units() if actor in (u["product_manager"], u["design_engineer"])), None)


if __name__ == "__main__":  # self-check: python -m app.modules.catalog.service
    def top(q: str) -> dict:
        return next(h for h in search(q, k=10) if h["kind"] == "product")

    # Syracuse demo items (data/seed) and spec lines: the product retrieval should rank first
    for q, want in [
        ("One (1) 15kV two (2) section Metal Clad Switchgear lineup.", "CROWN-ARMV"),
        ("Protective Relays and Controls.", "EP2-RPP"),
        ("Metal Clad Switchgear shall have eighteen (18) 15kV vacuum circuit breaker positions", "CROWN-ARMV"),
        ("Switchgear shall be Arc-resistant Type 2B", "CROWN-ARMV"),
        # by others: the documents give Syracuse to Crown (+ EP² relays only); scope is the matcher's call
        ("Metal Clad Switchgear shall be mounted within a fully enclosed Equipment Building (by others).", "CROWN-ARMV"),
        ("Separate utility incoming Cable termination compartment is required, that allows the utility to lock.", "CROWN-ACC"),
        ("Each phase shall have 1 inch diameter ground ball.", "CROWN-ACC"),
        ("The MANUFACTURER shall provide a NEMA four-hole pad and insulating boots", "CROWN-ACC"),
        ("Furnish two (2) bus Sections with tie breaker", "CROWN-ARMV"),
        ("Furnish relays, controls and associated accessories and hardware", "EP2-RPP"),
        ("The 13.2kV breakers shall be equipped with a SEL-751 (with touchscreen) overcurrent relay trip device.", "EP2-RPP"),
        ("Nominal voltage supplies: 125 volts DC for close and trip", "EP2-AUX"),
        # data/RFP/samples: data-centre wording
        ("Deployment preference: prefabricated / modular systems preferred to compress on-site schedule", "ANORD-POD"),
        ("Rack power: rack-mounted PDUs", "ANORD-PDU"),
        ("Branch circuits: twenty-four (24) 208V power whips", "ANORD-PDU"),
    ]:
        assert top(q)["id"] == want, (q, top(q)["id"], want)
    # unit only, where two products of the unit are both fair
    assert top("Rack density: minimum 120kW per rack, liquid cooling required at rack and chip level")["bu"] == "JETCOOL"
    assert top("Distribution: one dedicated power distribution cabinet")["bu"] == "ANORD"
    assert top("48 V DC rack power shelf with N+1 power supply units")["bu"] == "FPM"
    assert unit_of("EP² Design Engineer") == "EP2"
    print("catalog ok")
