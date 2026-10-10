from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, utcnow

KINDS = ["added", "modified", "removed", "unchanged", "not_a_requirement"]
NEEDS_TARGET = {"modified", "removed", "unchanged"}  # these name the baseline requirement they are about
ACTIONS = ["add", "modify", "delete", "clarify", "info"]  # what the change document says it does (reader agent)


class ChangeSet(Base):
    """One change document (addendum, Q&A answers, change request) read against the frozen baseline. A person
    confirms every classification; applying it creates the next baseline. One set per opportunity is in review."""
    __tablename__ = "change_set"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(20), index=True)
    document_id: Mapped[str] = mapped_column(String(40))                 # the change document (role "change")
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(12), default="review")    # review | applied | discarded
    baseline_from: Mapped[int]                                          # the baseline it was compared with
    baseline_count: Mapped[int]                                         # its requirements (share of change)
    baseline_to: Mapped[int | None]                                     # the baseline it created
    result: Mapped[dict | None] = mapped_column(JSON)                   # what applying it did
    created_by: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    applied_by: Mapped[str | None] = mapped_column(String(80))           # applied or discarded by
    applied_at: Mapped[datetime | None]


class ChangeItem(Base):
    """One change statement: where it is in the change document, the agent's classification against the baseline,
    and the person's decision. The agent's proposal is kept beside the decision."""
    __tablename__ = "change_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    set_id: Mapped[int] = mapped_column(index=True)
    n: Mapped[int]                                                      # document order, from 1
    page: Mapped[int | None]                                            # anchor in the change document
    line_start: Mapped[int | None]
    line_end: Mapped[int | None]
    bboxes: Mapped[list] = mapped_column(JSON, default=list)
    quote: Mapped[str] = mapped_column(Text)                            # verbatim from the change document
    text: Mapped[str] = mapped_column(Text)                             # the requirement after the change
    category: Mapped[str] = mapped_column(String(20), default="technical")
    action: Mapped[str] = mapped_column(String(10))                     # add | modify | delete | clarify | info
    candidates: Mapped[list] = mapped_column(JSON, default=list)        # [{req_id, text, source}] shown to the agent
    proposed_kind: Mapped[str] = mapped_column(String(20))
    proposed_target: Mapped[str | None] = mapped_column(String(20))
    rationale: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(default=0.0)
    kind: Mapped[str | None] = mapped_column(String(20))                 # the person's decision
    target: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(12), default="proposed")  # proposed | confirmed
    decided_by: Mapped[str | None] = mapped_column(String(80))

    @property
    def source(self) -> str:
        if self.page is None:
            return "not found in source"
        lines = f"line {self.line_start}" if self.line_start == self.line_end else f"lines {self.line_start}-{self.line_end}"
        return f"p. {self.page}, {lines}"
