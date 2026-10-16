from datetime import date, datetime

from sqlalchemy import JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

# Opportunity lifecycle. Other modules move it forward through service.set_status().
STATUSES = ["new", "reading", "review", "frozen", "go", "no_go", "dispatched", "consolidating", "submitted"]


class Opportunity(Base):
    """One engagement: one RFP, its own workspace, kept for the life of the project (warranty included)."""
    __tablename__ = "opportunity"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)        # OPP-0001
    title: Mapped[str] = mapped_column(String(200))
    customer: Mapped[str] = mapped_column(String(120), default="")
    customer_type: Mapped[str] = mapped_column(String(40), default="")    # utility, hyperscaler, neocloud, colocation, silicon
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Document(Base):
    """A received file in one opportunity. The bytes are stored once under their SHA-256 and never modified;
    the same file sent to two opportunities is two documents (rule R6)."""
    __tablename__ = "document"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)         # <opportunity>-<sha256[:12]>
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="main")         # main | addendum | qa | change | other
    path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="uploaded")   # uploaded | ingesting | ingested | failed | unsupported
    page_count: Mapped[int] = mapped_column(default=0)
    received_at: Mapped[datetime] = mapped_column(default=utcnow)


class DocumentIdentity(Base):
    """The Document ID and Document Instance ID of a received file (C-27), read from the file itself (core/fileid.py).
    A new table beside document, so existing databases need no reset."""
    __tablename__ = "document_identity"
    document_id: Mapped[str] = mapped_column(String(40), primary_key=True)   # document.id
    doc_ident: Mapped[str] = mapped_column(String(100), index=True)           # Document ID
    instance_ident: Mapped[str] = mapped_column(String(100), index=True)      # Document Instance ID
    id_source: Mapped[str] = mapped_column(String(12))                        # embedded | fingerprint


class BidSchedule(Base):
    """The bid's dates (C-24, P-33): the RFP's submission due date and the time the bid desk needs to consolidate after
    the last unit has finished. The planned submission date is computed, never typed."""
    __tablename__ = "bid_schedule"
    opportunity_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    due_date: Mapped[date | None]
    consolidation_days: Mapped[int] = mapped_column(default=5)
    updated_by: Mapped[str] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(default=utcnow)


class UnitSchedule(Base):
    """A participating unit's estimated completion date for its part of the response, set by its unit manager."""
    __tablename__ = "unit_schedule"
    __table_args__ = (UniqueConstraint("opportunity_id", "bu"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    bu: Mapped[str] = mapped_column(String(20))
    estimated_completion: Mapped[date]
    note: Mapped[str] = mapped_column(Text, default="")
    entered_by: Mapped[str] = mapped_column(String(80))
    entered_at: Mapped[datetime] = mapped_column(default=utcnow)


class BidApproval(Base):
    """The bid manager's approval of the overall schedule or the high-level compliance position (C-24), with the
    figures approved. An approval no longer matches when those figures change: it shows as reopened."""
    __tablename__ = "bid_approval"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    kind: Mapped[str] = mapped_column(String(12))                      # schedule | compliance
    snapshot: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[str] = mapped_column(String(80))
    approved_at: Mapped[datetime] = mapped_column(default=utcnow)
