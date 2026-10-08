from datetime import datetime

from sqlalchemy import String
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
