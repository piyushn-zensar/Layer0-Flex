from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

KINDS = ["requirement", "response", "decision"]


class KnowledgeItem(Base):
    """Something a person sent to the knowledge base, waiting for the curator (A-11). Approved items join the
    long-term retrieval index; the record keeps who sent it, from where, and who approved or rejected it."""
    __tablename__ = "knowledge_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    kb_id: Mapped[str] = mapped_column(String(20), unique=True)            # KB-0001, never reused
    kind: Mapped[str] = mapped_column(String(12))                           # requirement | response | decision
    source_ref: Mapped[str] = mapped_column(String(40), index=True)         # req_id, assignment id or decision id
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    bu: Mapped[str] = mapped_column(String(20), default="BID")
    requirement: Mapped[str] = mapped_column(Text)                          # what was asked
    response: Mapped[str] = mapped_column(Text, default="")                 # how it was answered (curator may edit)
    source: Mapped[str] = mapped_column(String(80), default="")             # e.g. "OPP-0001, p. 55, lines 7-65"
    note: Mapped[str] = mapped_column(Text, default="")                     # why the sender thinks it is worth keeping
    status: Mapped[str] = mapped_column(String(12), default="queued")       # queued | approved | rejected
    sent_by: Mapped[str] = mapped_column(String(80))
    sent_at: Mapped[datetime] = mapped_column(default=utcnow)
    reviewed_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_at: Mapped[datetime | None]
    review_note: Mapped[str] = mapped_column(Text, default="")
