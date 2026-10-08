from datetime import datetime

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

COMPLIANCE = ["met", "partial", "not_met", "exception"]
BID_DESK = "BID"  # pseudo-unit: requirements the bid manager answers (commercial, submission, legal)


class Assignment(Base):
    """One requirement assigned to one business unit, with that unit's checklist response.
    A requirement can have several assignments (one per unit). A work package = a unit's assignments."""
    __tablename__ = "assignment"
    __table_args__ = (UniqueConstraint("req_id", "bu"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    req_id: Mapped[str] = mapped_column(String(20), index=True)
    bu: Mapped[str] = mapped_column(String(20), index=True)
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(12), default="assigned")  # assigned | submitted | validated | returned
    compliance: Mapped[str | None] = mapped_column(String(12))           # met | partial | not_met | exception
    product_ref: Mapped[str | None] = mapped_column(String(80))          # what meets it (product / configuration)
    response: Mapped[str] = mapped_column(Text, default="")
    responded_by: Mapped[str | None] = mapped_column(String(80))
    responded_at: Mapped[datetime | None]
    validated_by: Mapped[str | None] = mapped_column(String(80))
    validation_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
