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
    # every source span [{document_id, page, line_start, line_end, bboxes}] (C-03): a quote across a page break, or
    # stitched from a lead-in and its item; page, line_start, line_end and bboxes above repeat the first span
    spans: Mapped[list] = mapped_column(JSON, default=list)
    # an exception only: where the reader says the quote is, when that page holds most of its words
    # {page, line_start, line_end, share}; where to look, never a source (anchoring.hint)
    location_hint: Mapped[dict | None] = mapped_column(JSON)
    provenance: Mapped[str] = mapped_column(String(12), default="EXTRACTED")  # EXTRACTED | UNANCHORED
    status: Mapped[str] = mapped_column(String(12), default="proposed")  # proposed | approved | rejected | split | merged | duplicate | removed
    derived_from: Mapped[list] = mapped_column(JSON, default=list)       # req_ids this one was split / merged from, or duplicates
    kind: Mapped[str] = mapped_column(String(8), default="item")         # item | group (a requirement made of sub-requirements)
    parent_id: Mapped[str | None] = mapped_column(String(20), index=True)  # the group a sub-requirement belongs to
    baseline: Mapped[int | None]                                        # frozen baseline number, None = draft
    origin: Mapped[str | None] = mapped_column(String(16))             # extraction | correction | customer_change
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    @property
    def source(self) -> str:
        if self.page is None:
            return "not found in source"
        spans = self.spans if len(self.spans or []) > 1 else [{"page": self.page, "line_start": self.line_start,
                                                                "line_end": self.line_end}]
        return "; ".join(f"p. {s['page']}, " + (f"line {s['line_start']}" if s["line_start"] == s["line_end"]
                                                 else f"lines {s['line_start']}-{s['line_end']}") for s in spans)


class ExtractionSnapshot(Base):
    """What one reading of a document proposed (E1, E2, ...): every candidate as the agents left it. Never updated or
    deleted (database triggers, as for the audit log); the working register starts from it."""
    __tablename__ = "extraction_snapshot"
    __table_args__ = (UniqueConstraint("opportunity_id", "number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    document_id: Mapped[str] = mapped_column(String(64))
    number: Mapped[int]                                                 # 1 = E1
    reason: Mapped[str] = mapped_column(Text, default="")              # why it was read again ("" for E1)
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    model: Mapped[str] = mapped_column(String(80))
    pipeline_version: Mapped[str] = mapped_column(String(40))
    coverage: Mapped[dict] = mapped_column(JSON, default=dict)
    items: Mapped[list] = mapped_column(JSON, default=list)


class Baseline(Base):
    """A frozen requirement set. Later runs process only the delta against it (changes module)."""
    __tablename__ = "baseline"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    number: Mapped[int]
    count: Mapped[int]
    frozen_by: Mapped[str] = mapped_column(String(80))
    frozen_at: Mapped[datetime] = mapped_column(default=utcnow)
