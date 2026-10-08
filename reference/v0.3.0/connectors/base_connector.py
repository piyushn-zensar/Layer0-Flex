"""
Abstract interface every external CPQ/ERP/costing connector implements.

Why this exists: SpinCo's constituent companies almost certainly already
run their own systems of record — the Draup account-intelligence review
identified QuoteWin (quoting) and SAP / Infor LN (ERP) in Flex's IT
landscape, plus aPriori for should-cost/DFM costing. This agentic
pipeline should never assume it is the only system of record. Instead,
it defines one clean contract every external system integrates against,
so adding, removing, or replacing a connector never touches pipeline
or agent code.

Each concrete connector below is a documented stub: it will not attempt
a real network call unless explicitly enabled in config (see
settings.QUOTEWIN_ENABLED etc.), and even then, the actual request/
response schema is a placeholder until SpinCo shares the real API
contract for that system. Enabling a connector without also filling in
its real schema will raise NotImplementedError with a clear message —
this is intentional, so a misconfiguration fails loudly rather than
silently pushing malformed data into a production system of record.
"""
from abc import ABC, abstractmethod


class BaseCPQConnector(ABC):
    system_name: str = "unnamed"

    @abstractmethod
    def push_configuration(self, run_id: str, design: dict) -> dict:
        """Push an approved layer design (Stage 2 output, post-approval)
        into the external system as a draft quote/configuration.
        Must return {"external_ref": "<id in the external system>",
        "status": "..."}"""
        raise NotImplementedError

    @abstractmethod
    def fetch_pricing(self, bom_items: list) -> dict:
        """Given a list of BOM line items, return pricing per item plus
        a total. Must return {"lines": [{"item": ..., "unit_cost": ...,
        "qty": ..., "extended_cost": ...}], "total_cost": ...}"""
        raise NotImplementedError

    @abstractmethod
    def fetch_component_catalog(self, layer_n: int) -> list:
        """Return the list of catalog part numbers available for a
        given stack layer, so the design agent could (in a future
        version) validate brand/spec choices against real, currently-
        orderable part numbers rather than the static knowledge base
        alone."""
        raise NotImplementedError

    @abstractmethod
    def get_status(self, external_ref: str) -> dict:
        """Check the status of a previously pushed configuration/quote
        in the external system."""
        raise NotImplementedError
