"""
Route B — ETO_GUIDED → design automation + basis of design.

Purpose: split a bespoke line into (a) the standard sub-components that
can be auto-priced from catalogue, and (b) the genuinely bespoke
remainder, captured as a basis-of-design brief so an engineer receives
a scoped requirement rather than the whole RFP.

`spec_claimed: False` is the single most important field this system
emits. It is an explicit, machine-readable assertion that Layer 0 has
CAPTURED requirements but has NOT produced a design. Without it, a
downstream system or a reviewer could reasonably infer that the
bespoke_scope block represents engineering work, which it does not.
"""
from routing.base_route import BaseRouteAdapter
from rag.retriever import get_full_layer_stack


class DesignAutomationRouteAdapter(BaseRouteAdapter):
    tier = "ETO_GUIDED"
    route = "ETO_GUIDED"
    target_system = "design_automation"
    display_name = "Design Automation + Basis of Design"

    # Component keywords whose per-component override marks them
    # auto-priceable even inside an otherwise bespoke line. Sourced from
    # the knowledge base rather than hardcoded, so SpinCo can extend the
    # catalogue-item list without touching this adapter.
    _AUTO_PRICEABLE_TIER = "CTO_AUTOMATE"

    def _catalogue_overrides(self, layer_n: int) -> list:
        stack = get_full_layer_stack()
        out = []
        for o in stack.get("component_overrides", []):
            if o.get("override_tier") != self._AUTO_PRICEABLE_TIER:
                continue
            applies = o.get("applies_to_layers", [])
            if applies and layer_n not in applies:
                continue
            out.append({
                "type": o["keyword"].replace("standard ", "").strip(),
                "spec": "standard",
                "auto_priceable": True,
                "basis": o.get("reason"),
            })
        return out

    def build(self, run_id, requirements, layers, tiers, validation, approvals):
        selected = self.select_layers(layers, tiers)
        if not selected:
            return None

        stack = get_full_layer_stack()
        team_map = stack["team_routing"]
        tier_by_n = {t["n"]: t for t in tiers}

        line_items = []
        for layer in selected:
            n = layer["n"]
            basis = {
                k: requirements.get(k) for k in
                ("voltage_class_kv", "voltage_arch", "redundancy",
                 "breaker_positions", "arc_resistant", "capacity_mw")
                if requirements.get(k) is not None
            }
            if requirements.get("compliance"):
                basis["standards"] = [
                    s.strip() for s in str(requirements["compliance"]).split(",")
                ][:8]

            line_items.append({
                "layer": n,
                "layer_name": layer["name"],
                "brand": layer["brand"],
                "standard_components": self._catalogue_overrides(n),
                "bespoke_scope": {
                    "basis_of_design": basis,
                    "spec_claimed": False,
                    "note": ("Layer 0 has NOT designed this. Captured "
                             "requirements only \u2014 engineering design is "
                             "required and has not been attempted."),
                },
                "tier_reason": tier_by_n.get(n, {}).get("reason"),
                "assigned_team": team_map[str(n)],
                "evidence_ref": f"run/{run_id}/stage2/layer{n}",
            })

        payload = self.envelope(run_id, requirements, approvals)
        payload.update({
            "line_items": line_items,
            "note": ("Standard sub-components are auto-priceable. The "
                     "bespoke remainder is a captured brief for a design "
                     "engineer, not a design."),
        })
        return payload
