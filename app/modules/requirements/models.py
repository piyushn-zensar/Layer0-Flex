from datetime import datetime

from sqlalchemy import JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

CATEGORIES = ["technical", "compliance", "commercial", "schedule", "submission", "legal", "staffing"]


class Requirement(Base):
    """One line item. Stored as versions: (req_id, version) is unique; nothing is edited after a freeze."""
    __tablename__ = "requirement"
    __table_args__ = (UniqueConstraint("req_id", "version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    req_id: Mapped[str] = mapped_column(String(20), index=True)       # REQ-0001-0042, unique across opportunities
    version: Mapped[int] = mapped_column(default=1)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    document_id: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)                             # short restatement for the line item
    quote: Mapped[str] = mapped_column(Text)                            # verbatim source text
    category: Mapped[str] = mapped_column(String(20), default="technical")
    section: Mapped[str] = mapped_column(String(200), default="")
    page: Mapped[int | None]
    line_start: Mapped[int | None]
    line_end: Mapped[int | None]
    bboxes: Mapped[list] = mapped_column(JSON, default=list)           # highlight boxes on the page, PDF points
    provenance: Mapped[str] = mapped_column(String(12), default="EXTRACTED")  # EXTRACTED | UNANCHORED
    status: Mapped[str] = mapped_column(String(12), default="proposed")  # proposed | approved | rejected | split | merged
    derived_from: Mapped[list] = mapped_column(JSON, default=list)       # req_ids this one was split from / merged from
    baseline: Mapped[int | None]                                        # frozen baseline number, None = draft
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    @property
    def source(self) -> str:
        if self.page is None:
            return "not found in source"
        lines = f"line {self.line_start}" if self.line_start == self.line_end else f"lines {self.line_start}-{self.line_end}"
        return f"p. {self.page}, {lines}"


class Baseline(Base):
    """A frozen requirement set. Later runs process only the delta against it (changes module)."""
    __tablename__ = "baseline"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    number: Mapped[int]
    count: Mapped[int]
    frozen_by: Mapped[str] = mapped_column(String(80))
    frozen_at: Mapped[datetime] = mapped_column(default=utcnow)
