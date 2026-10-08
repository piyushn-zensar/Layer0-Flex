"""
SAP / Infor LN ERP connector.

Flex's IT landscape review found both SAP ERP and Infor LN in active
use — likely reflecting different constituent companies' pre-existing
systems from serial acquisitions (Anord Mardix, Crown, EP2 may each
have brought their own ERP instance). This connector is written against
SAP's general shape (OData/RFC-style) as the more common enterprise
pattern; an Infor LN variant would follow the same BaseCPQConnector
contract with different transport details.

To make this real:
  1. Confirm which ERP instance (SAP vs Infor LN) owns the relevant
     master data for a given SpinCo brand/layer — per the Portfolio
     Chart, this is likely fragmented across brands, not unified.
  2. Obtain the appropriate connection method (SAP: OData service or
     RFC/BAPI via a middleware layer; Infor LN: its own web services
     API) and credentials.
  3. Replace the placeholder payloads below with the real schema for
     purchase requisitions / BOM push / component master data.
"""
from connectors.base_connector import BaseCPQConnector
from config import settings


class SAPERPConnector(BaseCPQConnector):
    system_name = "SAP/Infor LN ERP"

    def __init__(self):
        self.enabled = settings.SAP_ERP_ENABLED
        self.base_url = settings.SAP_ERP_BASE_URL
        self.api_key = settings.SAP_ERP_API_KEY

    def push_configuration(self, run_id: str, design: dict) -> dict:
        if not self.enabled:
            return {
                "external_ref": None, "status": "not_connected",
                "note": "SAP/ERP integration disabled (SAP_ERP_ENABLED=false). Returning mock response.",
            }
        raise NotImplementedError(
            "SAP/ERP is enabled but the real integration has not been implemented. "
            "Confirm which ERP instance (SAP vs Infor LN) owns the relevant master data first."
        )

    def fetch_pricing(self, bom_items: list) -> dict:
        if not self.enabled:
            return {
                "lines": [{"item": i.get("name", "unknown"), "unit_cost": None, "qty": i.get("qty", 1), "extended_cost": None} for i in bom_items],
                "total_cost": None,
                "note": "ERP integration disabled. Pricing not available.",
            }
        raise NotImplementedError("Real ERP pricing integration not yet implemented.")

    def fetch_component_catalog(self, layer_n: int) -> list:
        if not self.enabled:
            return []
        raise NotImplementedError("Real ERP catalog integration not yet implemented.")

    def get_status(self, external_ref: str) -> dict:
        if not self.enabled:
            return {"external_ref": external_ref, "status": "not_connected"}
        raise NotImplementedError("Real ERP status integration not yet implemented.")
