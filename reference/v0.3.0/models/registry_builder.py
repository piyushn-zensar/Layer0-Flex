"""
Builds a RequirementRegistry from the pipeline's existing stage outputs.

This is the keystone step: it takes the coverage map (M14), the tier
classification (M2) and the provenance anchors (M11) that the pipeline
ALREADY produces, and folds them into one REQ-xxxx object per clause.

Nothing upstream changes. The registry is a projection over existing
outputs, which is exactly why it is safe to add: it cannot regress the
pipeline because it only reads what the pipeline already emits.
"""
from __future__ import annotations

from models.registry import (
    Requirement, RequirementRegistry, RegistryAnchor,
    Classification, Governance, Coverage, Lifecycle,
)


def _anchor_from_dict(a: dict | None) -> RegistryAnchor | None:
    if not a:
        return None
    return RegistryAnchor(
        doc_id=a.get("doc_id", "rfp"),
        version=a.get("version", "as-received"),
        page=a.get("page", 1),
        span=tuple(a.get("span", (0, 0))),
        quote=a.get("quote", ""),
        extractor=a.get("extractor", "inline-text"),
    )


def _tier_for_disposition(cov_row: dict, tiers_by_layer: dict) -> Classification:
    """A coverage row records a tier only implicitly; recover it from the
    tier classification keyed by the layer the row maps to."""
    # coverage rows do not always carry a layer; infer from tier note if present
    layer = cov_row.get("layer")
    t = tiers_by_layer.get(layer) if layer is not None else None
    if t:
        return Classification(
            layer=t.get("n"), layer_name=t.get("name"),
            automation_tier=t.get("tier"), tier_rationale=t.get("reason"),
        )
    return Classification()


def build_registry(case_id: str,
                   coverage_map: dict,
                   tier_output: dict) -> RequirementRegistry:
    """Assemble the registry.

    coverage_map : output of agents.coverage.build_coverage_map (Stage 6)
    tier_output  : output of agents.tier_classifier.run (Stage 2)
    """
    tiers_by_layer = {t["n"]: t for t in tier_output.get("tiers", [])}

    reg = RequirementRegistry(
        case_id=case_id,
        unreviewed_regions=coverage_map.get("unreviewed_regions", 0),
    )

    for i, row in enumerate(coverage_map.get("rows", []), start=1):
        req_id = f"REQ-{i:04d}"
        anchor = _anchor_from_dict(row.get("source_anchor"))
        disposition = row.get("disposition", "UNREVIEWED")

        # Provenance class follows from whether the clause anchored to source.
        if anchor is not None:
            prov_class, unresolved = "EXTRACTED", None
        else:
            prov_class = "UNANCHORED"
            unresolved = ("Clause identified but its text span could not be "
                          "located verbatim in the source document.")

        req = Requirement(
            req_id=req_id,
            case_id=case_id,
            title=f"Clause {row.get('clause_id', req_id)}",
            raw_text=row.get("requirement", ""),
            normalized_value=row.get("extracted"),
            provenance_class=prov_class,
            source_anchor=anchor,
            unanchored_reason=unresolved,
            classification=_tier_for_disposition(row, tiers_by_layer),
            governance=Governance(status="UNREVIEWED"),
            coverage=Coverage(disposition=disposition, detail=row.get("detail")),
            lifecycle=Lifecycle(origin="SYSTEM_EXTRACTED"),
        )
        reg.add(req)

    return reg


def diff_against_proposal(registry: RequirementRegistry, checker_output: dict) -> RequirementRegistry:
    """Fold proposal-checker findings (M15) back onto the registry, so each
    requirement carries how the returned proposal treated it. This is the
    REQ-xxxx pivot in action: the RFP-vs-proposal diff happens on
    requirement ids, never on raw prose."""
    findings_by_clause = {}
    for f in checker_output.get("findings", []):
        findings_by_clause[f.get("clause_id")] = f

    for req in registry.requirements:
        clause_id = req.title.replace("Clause ", "")
        f = findings_by_clause.get(clause_id)
        if f:
            req.coverage.proposal_check_status = f.get("status")
            if f.get("status") in ("NOT_FOUND", "DEVIATION"):
                req.coverage.detail = (req.coverage.detail or "") + \
                    f" | proposal check: {f.get('note', '')}"
    return registry
