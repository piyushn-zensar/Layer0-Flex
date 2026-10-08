"""
Routing destination adapters (Module M8).

This package replaces the PoC's former Stage 5 "Consolidated Proposal".
That stage produced a prose proposal summary, which structurally
trespassed into CPQ territory and invited exactly the benchmarking the
Layer 0 positioning is designed to avoid. Stage 5 now emits machine-
readable HANDOFF PAYLOADS instead: one per downstream destination.

Design rules enforced across every adapter here:

  1. Layer 0 never emits a finished commercial artefact. Every outbound
     payload carries requires_human_completion = True.
  2. Layer 0 never claims to have produced a design. Route B carries
     spec_claimed = False and Route C carries design_attempted = False,
     as explicit machine-readable assertions.
  3. Adding a destination means adding one file in this package. The
     pipeline does not change, and no agent module changes.

Schemas are defined in Document A section 6 and are authoritative;
this code implements them, not the other way round.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone


from _version import __version__
LAYER0_VERSION = __version__


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseRouteAdapter(ABC):
    """One adapter per downstream destination.

    Each adapter receives the SAME inputs (the full approved pipeline
    state) and is responsible for selecting only the layers belonging
    to its own tier. This keeps tier-to-destination mapping in one
    obvious place per destination rather than scattered through a
    dispatcher.
    """

    #: the automation tier this adapter is responsible for
    tier: str = ""
    #: value written to payload["route"]
    route: str = ""
    #: value written to payload["target_system"]
    target_system: str = ""
    #: human-readable label used in the UI's Payload Inspector
    display_name: str = ""

    def select_layers(self, layers: list, tiers: list) -> list:
        """Returns the drafted layers whose classified tier matches this
        adapter's tier. Layers are matched by layer number `n`, because
        the tier list (Stage 2 classification) and the layer list
        (Stage 2 draft) are separate structures keyed on the same index."""
        tier_by_n = {t["n"]: t for t in tiers}
        return [
            layer for layer in layers
            if tier_by_n.get(layer["n"], {}).get("tier") == self.tier
        ]

    def envelope(self, run_id: str, requirements: dict, approvals: dict) -> dict:
        """Fields common to every route payload."""
        approver = None
        approved_at = None
        if approvals:
            last = sorted(approvals.items(), key=lambda kv: int(kv[0]))[-1][1]
            approver = last.get("approver")
            approved_at = last.get("timestamp")
        return {
            "route": self.route,
            "target_system": self.target_system,
            "run_id": run_id,
            "layer0_version": LAYER0_VERSION,
            "generated_at": utc_now(),
            "source_document": {
                "site": requirements.get("site"),
                "capacity_mw": requirements.get("capacity_mw"),
                "completeness_score": requirements.get("completeness_score"),
            },
            "human_approved_by": approver,
            "approved_at": approved_at,
            "requires_human_completion": True,
        }

    @abstractmethod
    def build(self, run_id: str, requirements: dict, layers: list,
              tiers: list, validation: dict, approvals: dict) -> dict | None:
        """Returns the payload dict, or None if no layers route here."""
        raise NotImplementedError
