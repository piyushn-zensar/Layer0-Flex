from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

OFFERING_TYPES = ["CTO", "SEMI_CUSTOM", "ETO", "NONE"]  # NONE: not a product item (bid manager answers it)


class Match(Base):
    """Proposed business unit, product and offering type for one requirement (screen 3)."""
    __tablename__ = "match"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    req_id: Mapped[str] = mapped_column(String(20), index=True)
    bu: Mapped[str | None] = mapped_column(String(20))          # main unit; None = handled by the bid manager
    product_id: Mapped[str | None] = mapped_column(String(40))
    offering_type: Mapped[str] = mapped_column(String(12), default="NONE")
    units: Mapped[list] = mapped_column(JSON, default=list)     # every unit: [{bu, product_id, offering_type}], main first
    confidence: Mapped[float] = mapped_column(default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[list] = mapped_column(JSON, default=list)   # retrieved catalog / past-response hits
    method: Mapped[str] = mapped_column(String(20), default="agent")  # agent | retrieval_only | manual
    status: Mapped[str] = mapped_column(String(12), default="proposed")  # proposed | accepted | rejected
    decided_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
