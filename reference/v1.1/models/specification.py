"""
models/specification.py

v1.1 enhancement: adds scenario_type, phase_number, and customer_segment
as optional fields on top of the v1.0 core switchgear spec fields.
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict


class ArcRating(BaseModel):
    standard: str
    accessibility: str
    arc_fault_current: str
    duration: str


class Specification(BaseModel):
    # --- Core fields (v1.0) ---
    voltage_rating: int = Field(..., description="Voltage rating in volts, e.g. 15000 for 15kV")
    current_rating: int = Field(..., description="Current rating in amps, e.g. 600")
    type: str = Field(..., description="Equipment type, e.g. 'metal-clad'")
    standards: Optional[List[str]] = Field(default_factory=list)
    arc_rating: Optional[ArcRating] = None
    short_circuit_rating: Optional[str] = None
    bil: Optional[str] = None
    busbar_material: Optional[str] = None
    busbar_thickness: Optional[Union[str, float]] = Field(
        default=None,
        description="Either a fraction string like '3/8 in' (as parsed from raw JSON) "
        "or a decimal number of inches (e.g. 0.375), as constructed directly in code/tests.",
    )

    # --- v1.1 additions ---
    scenario_type: Optional[str] = Field(
        default=None,
        description="e.g. 'bid_stage', 'commitment_stage', 'multi_customer_conflict'",
    )
    phase_number: Optional[int] = Field(
        default=None,
        description="Phase number for multi-phase orders (e.g. hyperscaler Phase 1/2)",
    )
    customer_segment: Optional[str] = Field(
        default=None,
        description="e.g. 'utility', 'hyperscaler', 'neocloud'",
    )

    # --- v1.1 orchestration additions (Checkpoint 5) ---
    case_id: Optional[str] = Field(
        default=None,
        description="Unique case identifier for state isolation across orchestrated runs",
    )
    quantity: Optional[int] = Field(default=None, description="Unit quantity for this opportunity")
    status: Optional[str] = Field(
        default=None,
        description="e.g. 'live_bid', 'pending', 'rfp_live', 'committed'",
    )

    model_config = ConfigDict(extra="allow")  # tolerate extra fields from raw JSON test data


if __name__ == "__main__":
    # quick smoke test
    spec = Specification(
        voltage_rating=15000,
        current_rating=600,
        type="metal-clad",
        scenario_type="bid_stage",
        customer_segment="utility",
    )
    print(spec.model_dump_json(indent=2))
