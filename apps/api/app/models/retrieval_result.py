"""
RetrievalResult model.

A dedicated table for retrieved chunks attached to a retrieval Span.
Keeping this as a real table (not buried in JSONB) allows aggregate
analytics like "average top-1 score across all projects".
"""
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import make_id


class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("rr"),
    )
    span_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("spans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Retrieval rank (1-based, lower = better before reranking)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    chunk_id: Mapped[str] = mapped_column(String(255), nullable=False)
    document_id: Mapped[str] = mapped_column(String(255), nullable=False)
    document_name: Mapped[str] = mapped_column(String(512), nullable=False)

    # Full chunk text — stored here for detailed inspection in the UI
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Retrieval score — meaning depends on retrieval_method
    # (cosine similarity, BM25 score, hybrid score, etc.)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    retrieval_method: Mapped[str] = mapped_column(String(64), nullable=False, default="cosine")

    # Whether this chunk made it into the final context
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Reranking information (populated when a reranking span follows retrieval)
    reranked_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reranker_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Flexible metadata: page number, department, year, section, etc.
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    span: Mapped["Span"] = relationship("Span", back_populates="retrieval_results")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<RetrievalResult id={self.id!r} rank={self.rank} "
            f"score={self.score:.4f} doc={self.document_name!r}>"
        )
