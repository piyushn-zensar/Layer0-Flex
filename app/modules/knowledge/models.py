from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

KINDS = ["requirement", "response", "decision", "correction"]
# What a reviewed example teaches (C-29 point 6).
EXAMPLE_TYPES = ["requirement", "preference", "background", "partial_compliance", "insufficient_evidence", "other"]


class KbItem(Base):
    """A reviewed example (P-36, C-29 points 3 and 6): something a person nominated from a bid (a requirement, a
    validated answer, a decision rationale or an extraction correction), kept with its conditions and limits and
    reusable only once a qualified reviewer approved it. Replaces the A-11 queue (table knowledge_item) and the
    knowledge_learned.json file. A change to an approved item is a new version (supersedes); approving it retires
    the earlier one. Status: queued -> approved | rejected; approved -> retired."""
    __tablename__ = "kb_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    kb_id: Mapped[str] = mapped_column(String(20), unique=True)            # KB-0001, never reused
    kind: Mapped[str] = mapped_column(String(12))                           # KINDS
    example_type: Mapped[str] = mapped_column(String(24), default="other")  # EXAMPLE_TYPES
    source_ref: Mapped[str] = mapped_column(String(40), index=True)         # req_id, assignment id or decision id
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    bu: Mapped[str] = mapped_column(String(20), default="BID")              # whose specialists review it
    requirement: Mapped[str] = mapped_column(Text)                          # what was asked
    response: Mapped[str] = mapped_column(Text, default="")                 # how it was answered (reviewer may tidy)
    source: Mapped[str] = mapped_column(String(200), default="")            # e.g. "REQ-0001-0055, p. 55, lines 7-65"
    conditions: Mapped[str] = mapped_column(Text, default="")               # when the example holds
    limits: Mapped[str] = mapped_column(Text, default="")                   # when it does not, what it does not show
    note: Mapped[str] = mapped_column(Text, default="")                     # why the nominator thinks it is worth keeping
    illustrative: Mapped[bool] = mapped_column(default=False)               # never verified evidence when true
    status: Mapped[str] = mapped_column(String(12), default="queued")       # queued | approved | rejected | retired
    version: Mapped[int] = mapped_column(default=1)
    supersedes: Mapped[str | None] = mapped_column(String(20))              # kb_id of the version this one replaces
    sent_by: Mapped[str] = mapped_column(String(80))
    sent_at: Mapped[datetime] = mapped_column(default=utcnow)
    reviewed_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_at: Mapped[datetime | None]
    review_note: Mapped[str] = mapped_column(Text, default="")


class KbSource(Base):
    """A registered source document of the knowledge base (P-35, C-29 points 1-4): one row per instance of a document.
    A new revision of the same document (same document_id) is a new row with the next version; publishing it retires
    the earlier one. Evidence only after review: draft -> published | rejected; published -> retired."""
    __tablename__ = "kb_source"
    id: Mapped[int] = mapped_column(primary_key=True)
    ks_id: Mapped[str] = mapped_column(String(20), unique=True)                  # KS-0001, never reused
    collection: Mapped[str] = mapped_column(String(30), index=True)              # sources.COLLECTIONS
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(300), default="")
    revision: Mapped[str] = mapped_column(String(120), default="")
    scope: Mapped[str] = mapped_column(Text, default="")                         # what the source covers / applies to
    permissions: Mapped[str] = mapped_column(String(120), default="public")      # who may see or cite it
    url: Mapped[str] = mapped_column(String(500), default="")
    file_name: Mapped[str] = mapped_column(String(300))
    path: Mapped[str] = mapped_column(String(500))                               # where the bytes are (never served raw)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(100), index=True)            # embedded in the file, else sha256 (C-27)
    instance_id: Mapped[str] = mapped_column(String(100), index=True)
    id_source: Mapped[str] = mapped_column(String(12))                           # embedded | fingerprint
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(12), default="draft")             # draft | published | rejected | retired
    opportunity_id: Mapped[str | None] = mapped_column(String(20), index=True)   # bid evidence only: the bid it belongs to
    pages: Mapped[int] = mapped_column(default=0)
    pipeline_version: Mapped[str] = mapped_column(String(200), default="")
    registered_by: Mapped[str] = mapped_column(String(80))
    registered_at: Mapped[datetime] = mapped_column(default=utcnow)
    reviewed_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_at: Mapped[datetime | None]
    review_note: Mapped[str] = mapped_column(Text, default="")


class KbPassage(Base):
    """A passage of a source with its exact location; the text is the source's own words, never a summary.
    Model annotations (topics, attributes, applicability, ambiguities) sit beside it and never replace it."""
    __tablename__ = "kb_passage"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("kb_source.id"), index=True)
    page: Mapped[int]
    line_start: Mapped[int]
    line_end: Mapped[int]
    heading: Mapped[str] = mapped_column(Text, default="")                       # heading path, " > " separated
    table: Mapped[str | None] = mapped_column(String(40))                        # layout table id when the passage is a table
    text: Mapped[str] = mapped_column(Text)
    annotations: Mapped[dict | None] = mapped_column(JSON)
