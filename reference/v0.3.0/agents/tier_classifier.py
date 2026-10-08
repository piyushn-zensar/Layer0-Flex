"""
Tier Classification — runs before Stage 2 drafts anything.

Determines, per layer, which of SpinCo's three automation tiers applies
(CTO_AUTOMATE, ETO_GUIDED, or ETO_EXCEPTION), so design_agent.py — to be
updated in the next agreed step — knows which of its three execution
paths to take for that layer, rather than uniformly drafting a full
spec for every layer regardless of how bespoke it actually is. This is
the direct fix for the expert panel's "Conditional Pass" gap: without
this module, the codebase produces identical behavior for an Anord
Mardix layer and an EP2 layer even though the architecture document
claims otherwise.

Deterministic by design, for the same reason routing_agent.py is
deterministic: which tier a brand defaults to is closer to an
organizational/engineering fact than a judgment call, and a demo
audience validating this system needs a classification trace that is
reproducible, not subject to model variance. No LLM call is made here.

KNOWN, TEMPORARY DUPLICATION (intentional, and scoped to be resolved
in the very next step): `hint_brand_for_layer()` below mirrors
design_agent.py's existing per-layer brand-selection conditionals
(voltage_arch, redundancy, rack_density_kw), because tier
classification must run BEFORE design_agent drafts anything, and
therefore cannot simply reuse design_agent's own post-hoc brand
choice. When design_agent.py is updated next to branch by tier, its
inline brand-selection logic will be replaced with a call into this
module, so the two stop duplicating the same conditionals. Until that
change lands, treat any drift between this file's hints and
design_agent.py's current (still-uniform) mock logic as expected, not
a bug.
"""
from rag.retriever import get_full_layer_stack

TIER_RANK = {"CTO_AUTOMATE": 0, "ETO_GUIDED": 1, "ETO_EXCEPTION": 2}


def _strip_brand_suffix(raw: str) -> str:
    """KB brand names are sometimes suffixed, e.g. 'EPC Power (pending close)'.
    Strip parenthetical suffixes for name-matching purposes."""
    return raw.split(" (")[0].strip()


def hint_brand_for_layer(layer_n: int, req: dict, kb_layer: dict) -> list:
    """Lightweight, deterministic hint at which brand(s) from this
    layer's KB entry are most likely to apply, given the Stage 1
    requirements. Returns a list (not a single brand), since a layer
    can resolve to more than one brand — e.g. Layer 4 combining EPC
    Power and Flex Power Modules under an 800VDC requirement.
    See module docstring re: temporary duplication with design_agent.py.
    """
    brands = kb_layer["brands"]
    voltage = (req.get("voltage_arch") or "").upper()
    redundancy = (req.get("redundancy") or "").upper()

    def by_name(*names):
        wanted = {n.upper() for n in names}
        matched = [b for b in brands if _strip_brand_suffix(b["name"]).upper() in wanted]
        return matched or brands  # fall back to all brands if nothing matched

    if layer_n == 2:
        # Arc-resistant / E-House / substation-control signals point to the
        # utility-grade brands regardless of stated redundancy class. Added
        # after the real Syracuse RFP (arc-resistant Type 2B, IEEE C37.20.7,
        # but no stated N-class) was incorrectly routed to Anord Mardix /
        # CTO_AUTOMATE, when the KB's own selection rules call for Crown.
        text_blob = " ".join(str(v) for v in req.values() if v is not None).lower()
        if req.get("arc_resistant") or "arc-resistant" in text_blob or "arc resistant" in text_blob:
            return by_name("Crown Technical Systems")
        if any(k in text_blob for k in ("substation control", "protection panel", "relay panel")):
            return by_name("EP2")
        if "2N" in redundancy:
            return by_name("EP2", "Crown Technical Systems")
        return by_name("Anord Mardix")
    if layer_n == 4:
        if "800" in voltage:
            return brands  # both EPC Power and Flex Power Modules apply
        return by_name("Flex Power Modules")
    # Layers 1, 3, 5, 6 each have exactly one brand in the KB today.
    return brands


def _match_component_override(text: str, layer_n: int, overrides: list):
    text_lower = (text or "").lower()
    for o in overrides:
        applies = o.get("applies_to_layers", [])
        if applies and layer_n not in applies:
            continue
        if o["keyword"].lower() in text_lower:
            return o
    return None


OUT_OF_SCOPE = "OUT_OF_SCOPE"


def classify_layer(layer_n: int, req: dict, requirement_text: str = "") -> dict:
    """Classify a single layer.

    `requirement_text` is free text checked against component_overrides
    (in this step, pass the raw RFP text or any available requirement
    notes; once design_agent.py is updated, it will also pass the
    drafted spec text through here for finer-grained matching).
    """
    stack = get_full_layer_stack()
    kb_layer = next(l for l in stack["layers"] if l["n"] == layer_n)
    overrides = stack.get("component_overrides", [])

    # A layer the RFP never asked about must not be presented as automatable
    # work. Assigning it a tier implies it is in the bid; it is not. Surfaced
    # by testing against the real 101-page Syracuse RFP, where Thermal
    # Management was reported CTO_AUTOMATE on a pure switchgear procurement.
    scope = req.get("layers_in_scope")
    if scope is not None and layer_n not in scope:
        ev = (req.get("scope_evidence") or {}).get(layer_n, {})
        return {
            "n": layer_n,
            "name": kb_layer["name"],
            "hinted_brands": [],
            "tier": OUT_OF_SCOPE,
            "reason": (f"Layer {layer_n} is not in scope for this bid "
                       f"({ev.get('basis', 'no supporting evidence in the document')}). "
                       f"No automation tier assigned."),
            "source": "scope_detection",
            "matched_override_keyword": None,
            "pending_suggestion": None,
        }

    hinted_brands = hint_brand_for_layer(layer_n, req, kb_layer)

    # Most conservative (highest-rank) tier among the hinted brands wins:
    # a layer that could involve an ETO_EXCEPTION brand is not treated as
    # CTO_AUTOMATE just because another brand at the same layer is routine.
    worst = max(hinted_brands, key=lambda b: TIER_RANK[b["automation_tier"]])
    tier = worst["automation_tier"]
    reason = f"Brand default: {worst['name']} is tiered {tier} ({worst['tier_rationale']})"
    source = "brand_default"
    matched_keyword = None

    override = _match_component_override(requirement_text, layer_n, overrides)
    suggestion = None
    if override:
        proposed = override["override_tier"]
        # OPTION B — human-gated downward overrides.
        #
        # A downward demotion (e.g. ETO_GUIDED -> CTO_AUTOMATE) triggered by
        # a keyword appearing anywhere in RFP prose is a false-CTO generator:
        # it can route bespoke engineering into an automated configurator.
        # In HV infrastructure that means un-engineered gear reaching
        # manufacturing. So downward moves are never applied automatically —
        # they are emitted as a SUGGESTION and the safer tier holds until a
        # human confirms. Upward moves (toward more human involvement) are
        # fail-safe and apply immediately.
        if TIER_RANK[proposed] < TIER_RANK[tier]:
            suggestion = {
                "suggested_tier": proposed,
                "status": "PENDING_HUMAN_CONFIRMATION",
                "matched_keyword": override["keyword"],
                "rationale": override["reason"],
                "held_tier": tier,
                "note": ("Downward override withheld. The safer tier applies "
                         "until an engineer confirms this component is genuinely "
                         "standard."),
            }
        else:
            tier = proposed
            reason = (f"Component override matched keyword '{override['keyword']}': "
                      f"{override['reason']}")
            source = "component_override"
            matched_keyword = override["keyword"]

    return {
        "n": layer_n,
        "name": kb_layer["name"],
        "hinted_brands": [b["name"] for b in hinted_brands],
        "tier": tier,
        "reason": reason,
        "source": source,
        "matched_override_keyword": matched_keyword,
        "pending_suggestion": suggestion,
    }


def run(req: dict, requirement_text: str = "") -> dict:
    """Classifies all six layers ahead of Stage 2 drafting.

    `req` is Stage 1's output. `requirement_text` is optionally the raw
    RFP text (pass it for the most complete override matching — a
    component override keyword like "standard enclosure" is far more
    likely to appear in the original RFP prose than in the structured
    requirement fields alone).
    """
    stack = get_full_layer_stack()
    results = [classify_layer(l["n"], req, requirement_text) for l in stack["layers"]]

    out_of_scope = [r for r in results if r["tier"] == OUT_OF_SCOPE]
    auto_count = sum(1 for r in results if r["tier"] == "CTO_AUTOMATE")
    guided_count = sum(1 for r in results if r["tier"] == "ETO_GUIDED")
    exception_count = sum(1 for r in results if r["tier"] == "ETO_EXCEPTION")
    pending = [r for r in results if r.get("pending_suggestion")]

    pending_note = ""
    if pending:
        pending_note = (
            f" {len(pending)} downward override(s) are held pending human confirmation "
            f"(layers {', '.join(str(r['n']) for r in pending)}) — the safer tier applies until confirmed."
        )

    return {
        "tiers": results,
        "pending_confirmations": [
            {"n": r["n"], "name": r["name"], **r["pending_suggestion"]} for r in pending
        ],
        "explanation": (
            f"Classified {len(results) - len(out_of_scope)} in-scope layer(s) "
            f"({len(out_of_scope)} out of scope, no tier assigned): {auto_count} CTO_AUTOMATE, "
            f"{guided_count} ETO_GUIDED, {exception_count} ETO_EXCEPTION. This determines which "
            f"downstream destination each layer routes to.{pending_note}"
        ),
        "evidence": [{
            "source": "spinco_layers.json: automation_tier (per brand) + component_overrides",
            "layers_classified": len(results),
            "fail_safe_rule": "ETO_EXCEPTION > ETO_GUIDED > CTO_AUTOMATE; downward overrides are human-gated",
        }],
    }
