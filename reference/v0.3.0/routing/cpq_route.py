"""
Route A — CTO_AUTOMATE → commercial CPQ (Logik.io / Salesforce).

Purpose: hand the configurator a pre-populated, validated STARTING
POINT so a sales engineer opens a partially-configured quote rather
than a blank one.

The distinction that carries the entire Layer 0 positioning is encoded
in this schema: the payload contains a `configuration_seed`, not a
completed configuration, and an explicit `unresolved_attributes` list.
Layer 0 seeds the configurator. It does not configure.
"""
from routing.base_route import BaseRouteAdapter


class CPQRouteAdapter(BaseRouteAdapter):
    tier = "CTO_AUTOMATE"
    route = "CTO_AUTOMATE"
    target_system = "logik_io"
    display_name = "Commercial CPQ (Logik.io / Salesforce)"

    # Requirement fields a configurator would need but that Layer 0
    # cannot reliably supply from an RFP alone.
    _SEED_FIELDS = ("voltage_class_kv", "voltage_arch", "redundancy",
                    "rack_density_kw", "deployment_preference")
    _COMMONLY_UNRESOLVED = ("site", "timeline")

    def build(self, run_id, requirements, layers, tiers, validation, approvals):
        selected = self.select_layers(layers, tiers)
        if not selected:
            return None

        tier_by_n = {t["n"]: t for t in tiers}
        line_items = []
        for layer in selected:
            seed = {
                f: requirements.get(f)
                for f in self._SEED_FIELDS
                if requirements.get(f) is not None
            }
            line_items.append({
                "layer": layer["n"],
                "layer_name": layer["name"],
                "brand": layer["brand"],
                "configuration_seed": seed,
                "confidence": self._confidence_for(layer["n"], validation),
                "tier_reason": tier_by_n.get(layer["n"], {}).get("reason"),
                "evidence_ref": f"run/{run_id}/stage2/layer{layer['n']}",
            })

        unresolved = [
            f for f in self._COMMONLY_UNRESOLVED if not requirements.get(f)
        ]
        unresolved += [
            f for f in requirements.get("missing_fields", [])
            if f not in unresolved
        ]

        payload = self.envelope(run_id, requirements, approvals)
        payload.update({
            "line_items": line_items,
            "unresolved_attributes": unresolved,
            "note": ("Configuration seed only. Layer 0 has not produced a "
                     "complete or valid configuration; the target CPQ owns "
                     "constraint solving and pricing."),
        })
        return payload

    @staticmethod
    def _confidence_for(layer_n: int, validation: dict) -> str:
        for c in validation.get("confidence", []):
            if c.get("n") == layer_n:
                return c.get("level", "unknown")
        return "unknown"
