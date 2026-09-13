"""
User model.

Users own Projects. Authentication is separate from project API-key auth.
"""
from typing import List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.base import TimestampMixin, make_id


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: make_id("user"),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    # Stores a bcrypt hash — never the plain-text password
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    projects: Mapped[List["Project"]] = relationship(  # noqa: F821
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"
