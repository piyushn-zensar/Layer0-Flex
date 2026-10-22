from datetime import datetime

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

COMPLIANCE = ["met", "partial", "deviation", "not_met", "exception"]  # stored values; "exception" only on earlier answers
OFFERED = ["met", "partial", "deviation", "not_met"]  # what a unit answers (16.5, C-43)
NEEDS_REASON = ("partial", "deviation", "not_met")    # these need a reason: what is not met or what changes, and why
NEEDS_CHANGE = ("deviation",)  # also needs the proposed change (stored in workaround)
COMPLIANCE_LABELS = {"met": "Compliant", "partial": "Partially compliant", "deviation": "Compliant with changes",
                     "not_met": "Non-compliant", "exception": "Exception (earlier value)"}  # screen words; = web/lib/types.ts
EXTENDED = ("reason", "conditions", "workaround", "next_steps")  # the response fields beside the answer (C-12)
BID_DESK = "BID"  # pseudo-unit: requirements the bid manager answers (commercial, submission, legal)


COMMENT_KINDS = ["question", "comment"]  # an open question blocks completion; a comment is information (C-17)


class Comment(Base):
    """A question or comment on one requirement of a bid, optionally about one unit's assignment (C-17)."""
    __tablename__ = "comment"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    req_id: Mapped[str] = mapped_column(String(20), index=True)
    assignment_id: Mapped[int | None]
    author: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(10), default="comment")   # question | comment
    status: Mapped[str] = mapped_column(String(8), default="open")     # open | closed
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    closed_by: Mapped[str | None] = mapped_column(String(80))
    closed_at: Mapped[datetime | None]


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
    status: Mapped[str] = mapped_column(String(12), default="assigned")  # assigned | submitted | validated | returned | withdrawn
    compliance: Mapped[str | None] = mapped_column(String(12))           # met | partial | deviation | not_met | exception
    product_ref: Mapped[str | None] = mapped_column(String(80))          # what meets it (product / configuration)
    response: Mapped[str] = mapped_column(Text, default="")
    responded_by: Mapped[str | None] = mapped_column(String(80))
    responded_at: Mapped[datetime | None]
    validated_by: Mapped[str | None] = mapped_column(String(80))
    validation_note: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str | None] = mapped_column(Text)       # what is not met and why (required for partial, deviation, not_met)
    conditions: Mapped[str | None] = mapped_column(Text)   # under which conditions it is met
    workaround: Mapped[str | None] = mapped_column(Text)   # what the unit offers instead; for deviation the proposed change (required)
    next_steps: Mapped[str | None] = mapped_column(Text)   # what has to happen next, and by whom
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
