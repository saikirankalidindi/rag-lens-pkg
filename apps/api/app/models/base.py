"""
Shared base class and helpers for all ORM models.

All primary keys use prefixed ULID strings for readability in logs.
All tables get created_at / updated_at automatically.
"""
import secrets
import string
import time
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base

# ── ULID-like ID generation ───────────────────────────────────────────────────
# We use a simple sortable random ID rather than a full ULID library to keep
# dependencies minimal. Format: <prefix>_<timestamp_ms_base32><random_16>
_ALPHABET = string.ascii_lowercase + string.digits


def _generate_id(prefix: str) -> str:
    """Generate a sortable, prefixed, URL-safe ID.

    Format: ``<prefix>_<10 timestamp chars><16 random chars>``
    """
    # 10-char base-36 timestamp (milliseconds since epoch, sortable)
    ts = int(time.time() * 1000)
    ts_str = ""
    for _ in range(10):
        ts_str = _ALPHABET[ts % 36] + ts_str
        ts //= 36
    random_part = "".join(secrets.choice(_ALPHABET) for _ in range(16))
    return f"{prefix}_{ts_str}{random_part}"


def make_id(prefix: str) -> str:
    """Public helper used in model ``default=`` callables."""
    return _generate_id(prefix)


# ── Timestamp mixin ───────────────────────────────────────────────────────────

class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
