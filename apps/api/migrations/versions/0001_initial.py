"""initial: users and projects tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-07 00:00:00.000000 UTC
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── projects ───────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "owner_id",
            sa.String(64),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        # Privacy flags
        sa.Column("capture_query", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capture_context", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capture_prompt", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capture_response", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_projects_slug", "projects", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_projects_slug", table_name="projects")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
