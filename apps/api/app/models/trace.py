"""
Trace model.

One user question → one Trace.
A Trace contains multiple Spans and zero or more Diagnostics.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class Trace(Base, TimestampMixin):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("trace"),
    )
    project_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Optional correlation IDs — useful for multi-turn or user-scoped queries
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # success | warning | error
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success", index=True)

    # Flexible JSONB fields for pipeline-specific data
    input: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="traces")  # noqa: F821
    spans: Mapped[List["Span"]] = relationship(  # noqa: F821
        "Span",
        back_populates="trace",
        cascade="all, delete-orphan",
        order_by="Span.started_at",
    )
    diagnostics: Mapped[List["Diagnostic"]] = relationship(  # noqa: F821
        "Diagnostic",
        back_populates="trace",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Trace id={self.id!r} name={self.name!r} status={self.status!r}>"
