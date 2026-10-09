from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow


class Decision(Base):
    """A named person's decision with the evidence shown at the time. Layer 0 never decides."""
    __tablename__ = "decision"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    kind: Mapped[str] = mapped_column(String(20))            # participation | go_no_go
    outcome: Mapped[str] = mapped_column(String(20))         # participation: "units"; go_no_go: go | no_go
    units: Mapped[list] = mapped_column(JSON, default=list)  # participating business-unit codes
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    rationale: Mapped[str] = mapped_column(Text, default="")
    criteria: Mapped[list] = mapped_column(JSON, default=list)  # the person's judgement per criterion (A-12)
    decided_by: Mapped[str] = mapped_column(String(80))
    decided_at: Mapped[datetime] = mapped_column(default=utcnow)
