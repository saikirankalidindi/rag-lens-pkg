"""
ApiKey model.

Project API keys are used by the RAGLens SDK to ingest traces.
The raw key is NEVER stored — only the prefix (for display) and the hash.
The full key is shown exactly once at creation time.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("apikey"),
    )
    project_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable label set by the user (e.g. "Production server")
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stored plaintext so we can display "rgl_test_Abc123..." in the UI
    # This prefix is NOT secret — it's the first ~16 chars of the key.
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # sha256(full_key) — never store the raw key
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="api_keys")  # noqa: F821

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def __repr__(self) -> str:
        return f"<ApiKey id={self.id!r} prefix={self.key_prefix!r}>"
