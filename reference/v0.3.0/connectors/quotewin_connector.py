"""
QuoteWin connector.

QuoteWin was identified in Flex's IT landscape (Draup account-
intelligence review) as an existing quoting tool. This connector is a
documented stub, not a real integration: the actual QuoteWin API
contract (auth method, endpoint paths, payload schema) is not public
and must be obtained from SpinCo/Flex IT before this can push real
data. Until then, `QUOTEWIN_ENABLED=false` (the default) keeps this
connector in safe, mock-response mode.

To make this real, a SpinCo integration engineer would need to:
  1. Confirm whether QuoteWin exposes a REST API, a SOAP endpoint, or
     only a file-based/batch interface (common for older on-prem
     quoting tools).
  2. Obtain API credentials/auth scheme (API key, OAuth, or a service
     account) and populate QUOTEWIN_BASE_URL / QUOTEWIN_API_KEY in
     .env.
  3. Replace the request bodies below with QuoteWin's actual expected
     schema (this stub's shape is a reasonable placeholder, not a
     confirmed contract).
"""
from connectors.base_connector import BaseCPQConnector
from config import settings


class QuoteWinConnector(BaseCPQConnector):
    system_name = "QuoteWin"

    def __init__(self):
        self.enabled = settings.QUOTEWIN_ENABLED
        self.base_url = settings.QUOTEWIN_BASE_URL
        self.api_key = settings.QUOTEWIN_API_KEY

    def push_configuration(self, run_id: str, design: dict) -> dict:
        if not self.enabled:
            return {
                "external_ref": None, "status": "not_connected",
                "note": "QuoteWin integration disabled (QUOTEWIN_ENABLED=false). Returning mock response.",
            }
        raise NotImplementedError(
            "QuoteWin is enabled but the real API contract has not been implemented. "
            "See this file's module docstring for what SpinCo IT needs to provide first."
        )

    def fetch_pricing(self, bom_items: list) -> dict:
        if not self.enabled:
            return {
                "lines": [{"item": i.get("name", "unknown"), "unit_cost": None, "qty": i.get("qty", 1), "extended_cost": None} for i in bom_items],
                "total_cost": None,
                "note": "QuoteWin integration disabled. Pricing not available — connect aPriori or QuoteWin for real figures.",
            }
        raise NotImplementedError("Real QuoteWin pricing integration not yet implemented.")

    def fetch_component_catalog(self, layer_n: int) -> list:
        if not self.enabled:
            return []
        raise NotImplementedError("Real QuoteWin catalog integration not yet implemented.")

    def get_status(self, external_ref: str) -> dict:
        if not self.enabled:
            return {"external_ref": external_ref, "status": "not_connected"}
        raise NotImplementedError("Real QuoteWin status integration not yet implemented.")
