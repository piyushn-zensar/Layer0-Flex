from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class ComponentRun(Base):
    """One configurator run over a bid's register (P-56): what was grouped, on which catalog import, by whom."""
    __tablename__ = "component_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    catalog_import: Mapped[str] = mapped_column(String(10))       # power_modules.json last_import the run used
    ungrouped: Mapped[list] = mapped_column(JSON, default=list)   # items in no component (nothing a product answers)
    unassigned: Mapped[list] = mapped_column(JSON, default=list)  # items the model gave no answer for
    run_by: Mapped[str] = mapped_column(String(80))
    run_at: Mapped[datetime] = mapped_column(default=utcnow)


class ComponentMatch(Base):
    """One requested component of a run and its outcome, explained (C-57, C-58, C-61). Agents propose: an outcome
    is the configurator's result, pending engineering review, never a decision."""
    __tablename__ = "component_match"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("component_run.id"), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    seq: Mapped[int] = mapped_column(default=0)
    name: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(10))                 # dc_dc | system | other
    req_ids: Mapped[list] = mapped_column(JSON, default=list)
    outcome: Mapped[str] = mapped_column(String(24))              # see explain.OUTCOMES
    reason: Mapped[str] = mapped_column(Text, default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)      # requirements, candidates, assumptions, checks, inputs
