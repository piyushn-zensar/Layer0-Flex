"""
The canonical requirement object — REQ-xxxx.

WHY THIS EXISTS
---------------
Until now the pipeline passed loose dicts between stages: extracted values
here, tiers there, coverage rows somewhere else. Nothing tied a single
customer requirement to its classification, its source location, and its
fate in one object.

The registry makes the requirement the atomic unit. Every extracted or
authored requirement becomes one REQ-xxxx with a stable id, a provenance
class, a classification, a governance status, and a coverage status. That
one object is the pivot the whole system turns on:

  - It is how you answer "did we miss anything?" (a requirement with no
    coverage is a visible gap, not a silent one).
  - It is how you diff an RFP against a proposal without O(N^2) fuzzy text
    matching: you match on requirement ids, not on prose.
  - It is where a human correction lands (governance.status), and where a
    later audit reads who changed what.

WHAT THIS DELIBERATELY IS NOT
-----------------------------
This is a data model, not a platform. It does not require a vector
database, a knowledge graph, or an event-sourced ledger to be useful.
Those may come later; the registry stands on its own and improves the
system that already runs. Human split/merge lifecycle is modelled here
(so the schema does not need to change when that capability is built) but
the mutating operations themselves are a later step.
"""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# --- provenance -------------------------------------------------------

class RegistryAnchor(BaseModel):
    """Where a value came from in a source document. Mirrors the runtime
    SpanAnchor in provenance/anchors.py; kept as a plain model here so the
    registry has no import cycle with the provenance module."""
    doc_id: str
    version: str = "as-received"
    page: int
    span: tuple[int, int]
    quote: str
    extractor: str = "inline-text"


class DerivedChain(BaseModel):
    """For DERIVED requirements: the rule that produced the value and the
    requirements it consumed. rule_version is carried so that, if a rule
    changes later, one can identify which requirements used the old one."""
    rule_id: str
    rule_version: str = "v1"
    parent_req_ids: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


# --- the classification / governance / coverage facets ----------------

class Classification(BaseModel):
    layer: Optional[int] = None
    layer_name: Optional[str] = None
    automation_tier: Optional[Literal[
        "CTO_AUTOMATE", "ETO_GUIDED", "ETO_EXCEPTION", "OUT_OF_SCOPE"]] = None
    tier_rationale: Optional[str] = None


class Governance(BaseModel):
    """Human-in-the-loop state. UNREVIEWED until a person acts on it."""
    status: Literal["UNREVIEWED", "HUMAN_CONFIRMED", "OVERRIDDEN"] = "UNREVIEWED"
    downward_override_pending: bool = False
    signoff_actor: Optional[str] = None
    signoff_note: Optional[str] = None


class Coverage(BaseModel):
    """Whether this requirement was addressed, and by what."""
    disposition: Literal[
        "EXTRACTED_AND_ROUTED", "CAPTURED_NOT_DESIGNED", "SOLVED",
        "OUT_OF_SCOPE_BY_DESIGN", "NOT_HANDLED", "UNREVIEWED"] = "UNREVIEWED"
    proposal_check_status: Optional[Literal[
        "APPEARS_ADDRESSED", "NOT_FOUND", "DEVIATION"]] = None
    detail: Optional[str] = None


class Lifecycle(BaseModel):
    """Supports human curation without the schema changing later. The
    mutating operations (split/merge/edit) are a future step; the shape
    is here now so nothing has to be migrated when they land."""
    version: int = 1
    origin: Literal[
        "SYSTEM_EXTRACTED", "SYSTEM_DERIVED", "HUMAN_ADDED",
        "HUMAN_EDITED", "SPLIT", "MERGED"] = "SYSTEM_EXTRACTED"
    parent_req_ids: List[str] = Field(default_factory=list)
    is_active: bool = True


# --- the object itself ------------------------------------------------

class Requirement(BaseModel):
    req_id: str = Field(description="Stable id, e.g. REQ-0007")
    case_id: str = "case-unbound"
    title: str
    raw_text: str
    normalized_value: Optional[str] = None   # e.g. "15.0 kV", "800VDC"

    provenance_class: Literal["EXTRACTED", "DERIVED", "UNANCHORED"]
    source_anchor: Optional[RegistryAnchor] = None
    derived_chain: Optional[DerivedChain] = None
    unanchored_reason: Optional[str] = None

    classification: Classification = Field(default_factory=Classification)
    governance: Governance = Field(default_factory=Governance)
    coverage: Coverage = Field(default_factory=Coverage)
    lifecycle: Lifecycle = Field(default_factory=Lifecycle)

    def model_post_init(self, __context) -> None:
        # Enforce the provenance contract: the whole point of the three
        # classes is that they cannot be faked. An EXTRACTED requirement
        # must carry an anchor; a DERIVED one must carry its rule chain;
        # an UNANCHORED one must say why it could not be located.
        if self.provenance_class == "EXTRACTED" and self.source_anchor is None:
            raise ValueError(f"{self.req_id}: EXTRACTED requires a source_anchor")
        if self.provenance_class == "DERIVED" and self.derived_chain is None:
            raise ValueError(f"{self.req_id}: DERIVED requires a derived_chain")
        if self.provenance_class == "UNANCHORED" and not self.unanchored_reason:
            raise ValueError(f"{self.req_id}: UNANCHORED requires unanchored_reason")


class RequirementRegistry(BaseModel):
    """The set of requirements for one bid case, plus honest roll-ups."""
    case_id: str
    requirements: List[Requirement] = Field(default_factory=list)
    unreviewed_regions: int = 0   # source text not segmented into any requirement

    def add(self, req: Requirement) -> None:
        self.requirements.append(req)

    def by_id(self, req_id: str) -> Optional[Requirement]:
        return next((r for r in self.requirements if r.req_id == req_id), None)

    def coverage_summary(self) -> dict:
        """Honest denominators. Coverage is claimed only over segmented
        requirements; unreviewed source regions are reported separately,
        never folded into a flattering percentage."""
        counts: dict = {}
        for r in self.requirements:
            counts[r.coverage.disposition] = counts.get(r.coverage.disposition, 0) + 1
        anchored = sum(1 for r in self.requirements if r.provenance_class == "EXTRACTED")
        return {
            "total_requirements": len(self.requirements),
            "by_disposition": counts,
            "anchored": anchored,
            "unanchored": sum(1 for r in self.requirements if r.provenance_class == "UNANCHORED"),
            "derived": sum(1 for r in self.requirements if r.provenance_class == "DERIVED"),
            "unreviewed_source_regions": self.unreviewed_regions,
            "note": ("Coverage is over segmented requirements only. "
                     f"{self.unreviewed_regions} source region(s) were not segmented "
                     "and are excluded from the denominator."),
        }
