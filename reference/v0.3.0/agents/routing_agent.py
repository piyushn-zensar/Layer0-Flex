"""
Stage 4 — Parallel Team Routing.

Deliberately makes NO model call. Which engineering team owns which
layer is a fixed organizational fact (see team_routing in
spinco_layers.json), not something requiring interpretation. Routing
happens in parallel across teams (all work packages are produced in
one pass here), not sequentially — a sequential hand-off would
recreate the exact quote-churn delay the whole system exists to
eliminate.
"""
from rag.retriever import get_full_layer_stack


def run(layers: list) -> dict:
    layer_stack = get_full_layer_stack()
    team_map = layer_stack["team_routing"]

    packages = {}
    for l in layers:
        team = team_map[str(l["n"])]
        packages.setdefault(team, []).append({
            "n": l["n"], "name": l["name"], "brand": l["brand"], "spec": l["spec"],
        })

    return {
        "work_packages": packages,
        "explanation": (
            f"Routed {len(layers)} layers to {len(packages)} engineering team(s) in parallel, "
            f"using SpinCo's fixed layer-to-team ownership map — no model judgment involved in this step."
        ),
        "evidence": [{"source": "spinco_layers.json:team_routing", "mapping": team_map}],
    }
