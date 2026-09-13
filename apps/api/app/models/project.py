"""
Project model.

A Project is the top-level container for Traces and API Keys.
One User can own many Projects.
"""
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("project"),
    )
    owner_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Privacy flags — Phase 2+ will enforce these during ingestion
    capture_query: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capture_context: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capture_prompt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capture_response: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")  # noqa: F821

    api_keys: Mapped[List["ApiKey"]] = relationship(  # noqa: F821
        "ApiKey",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    traces: Mapped[List["Trace"]] = relationship(  # noqa: F821
        "Trace",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id!r} name={self.name!r}>"
