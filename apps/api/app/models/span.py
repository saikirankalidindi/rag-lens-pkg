"""
Span model.

Every meaningful operation inside a Trace is a Span.
Spans support parent-child nesting via parent_span_id.

Supported types:
  query | query_rewrite | retrieval | reranking | context | prompt | llm | response | custom
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class Span(Base, TimestampMixin):
    __tablename__ = "spans"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("span"),
    )
    trace_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_span_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("spans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # span type — indexed for filtering in the diagnostics engine
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # success | warning | error
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")

    # span-type-specific data lives in JSONB
    input: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # attributes carries provider-specific extras: retrieval config, LLM params, etc.
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    trace: Mapped["Trace"] = relationship("Trace", back_populates="spans")  # noqa: F821

    # Self-referential: children of this span
    children: Mapped[List["Span"]] = relationship(
        "Span",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped[Optional["Span"]] = relationship(
        "Span",
        back_populates="children",
        remote_side="Span.id",
    )

    retrieval_results: Mapped[List["RetrievalResult"]] = relationship(  # noqa: F821
        "RetrievalResult",
        back_populates="span",
        cascade="all, delete-orphan",
        order_by="RetrievalResult.rank",
    )

    def __repr__(self) -> str:
        return f"<Span id={self.id!r} type={self.type!r} name={self.name!r}>"
