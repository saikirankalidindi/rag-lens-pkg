"""
Diagnostic model.

Deterministic rule-based diagnostics attached to a Trace.
Each diagnostic points to the specific span that triggered it (optional).

Severity:  info | warning | error
Category:  retrieval | context | latency | tokens | generation
"""
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class Diagnostic(Base, TimestampMixin):
    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("diag"),
    )
    trace_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Which span triggered this diagnostic (null = trace-level)
    span_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("spans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured evidence that triggered the rule
    # e.g. {"score": 0.54, "threshold": 0.70}
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Actionable suggestions for the developer
    suggestions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    trace: Mapped["Trace"] = relationship("Trace", back_populates="diagnostics")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Diagnostic id={self.id!r} severity={self.severity!r} "
            f"title={self.title!r}>"
        )
