"""
aPriori should-cost / DFM connector.

aPriori was identified in Flex's IT landscape (PLM category, alongside
Oracle PLM and Autodesk Vault) as an existing manufacturing-cost
simulation tool. Of the three connectors in this package, this is the
one most worth prioritizing for a real integration: aPriori already
does automated cost modeling, which is exactly the capability Stage 3's
"cost_margin" check currently approximates with a static heuristic
(see engineering_rules.json:cost_margin_notes). A real aPriori
connection would let that check return an actual should-cost figure
instead of a qualitative note.

To make this real:
  1. Confirm aPriori's deployment (on-prem vs aPriori Cloud) and its
     API surface (aPriori has historically exposed both a desktop
     client-driven workflow and, in newer versions, a REST API for
     cost analysis jobs).
  2. Map SpinCo's layer/brand/spec fields (this system's output) to
     whatever part/process input aPriori's cost model expects.
"""
from connectors.base_connector import BaseCPQConnector
from config import settings


class APrioriConnector(BaseCPQConnector):
    system_name = "aPriori"

    def __init__(self):
        self.enabled = settings.APRIORI_ENABLED
        self.base_url = settings.APRIORI_BASE_URL
        self.api_key = settings.APRIORI_API_KEY

    def push_configuration(self, run_id: str, design: dict) -> dict:
        if not self.enabled:
            return {
                "external_ref": None, "status": "not_connected",
                "note": "aPriori integration disabled (APRIORI_ENABLED=false). Returning mock response.",
            }
        raise NotImplementedError(
            "aPriori is enabled but the real integration has not been implemented. "
            "Confirm aPriori's deployment mode and API surface first (see module docstring)."
        )

    def fetch_pricing(self, bom_items: list) -> dict:
        if not self.enabled:
            return {
                "lines": [{"item": i.get("name", "unknown"), "unit_cost": None, "qty": i.get("qty", 1), "extended_cost": None} for i in bom_items],
                "total_cost": None,
                "note": "aPriori integration disabled. Should-cost figures not available.",
            }
        raise NotImplementedError("Real aPriori cost-model integration not yet implemented.")

    def fetch_component_catalog(self, layer_n: int) -> list:
        if not self.enabled:
            return []
        raise NotImplementedError("aPriori does not typically expose a component catalog — this method may not be applicable for this connector.")

    def get_status(self, external_ref: str) -> dict:
        if not self.enabled:
            return {"external_ref": external_ref, "status": "not_connected"}
        raise NotImplementedError("Real aPriori job-status integration not yet implemented.")
