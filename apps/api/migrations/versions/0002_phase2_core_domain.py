"""phase2: api_keys, traces, spans, retrieval_results, diagnostics

Revision ID: 0002_phase2_core_domain
Revises: 0001_initial
Create Date: 2026-09-07 00:01:00.000000 UTC
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2_core_domain"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── api_keys ───────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.String(64),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(32), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
    )
    op.create_index("ix_api_keys_project_id", "api_keys", ["project_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # ── traces ─────────────────────────────────────────────────────────────
    op.create_table(
        "traces",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.String(64),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="success"),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_traces_project_id", "traces", ["project_id"])
    op.create_index("ix_traces_started_at", "traces", ["started_at"])
    op.create_index("ix_traces_status", "traces", ["status"])
    op.create_index("ix_traces_session_id", "traces", ["session_id"])

    # ── spans ──────────────────────────────────────────────────────────────
    op.create_table(
        "spans",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "trace_id",
            sa.String(64),
            sa.ForeignKey("traces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_span_id",
            sa.String(64),
            sa.ForeignKey("spans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="success"),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_spans_trace_id", "spans", ["trace_id"])
    op.create_index("ix_spans_type", "spans", ["type"])
    op.create_index("ix_spans_parent_span_id", "spans", ["parent_span_id"])

    # ── retrieval_results ──────────────────────────────────────────────────
    op.create_table(
        "retrieval_results",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "span_id",
            sa.String(64),
            sa.ForeignKey("spans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(255), nullable=False),
        sa.Column("document_id", sa.String(255), nullable=False),
        sa.Column("document_name", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("retrieval_method", sa.String(64), nullable=False, server_default="cosine"),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reranked_rank", sa.Integer(), nullable=True),
        sa.Column("reranker_score", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_retrieval_results_span_id", "retrieval_results", ["span_id"])

    # ── diagnostics ────────────────────────────────────────────────────────
    op.create_table(
        "diagnostics",
        sa.Column("id", sa.String(64), primary_key=True, nullable=False),
        sa.Column(
            "trace_id",
            sa.String(64),
            sa.ForeignKey("traces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "span_id",
            sa.String(64),
            sa.ForeignKey("spans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "suggestions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
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
    op.create_index("ix_diagnostics_trace_id", "diagnostics", ["trace_id"])
    op.create_index("ix_diagnostics_severity", "diagnostics", ["severity"])
    op.create_index("ix_diagnostics_span_id", "diagnostics", ["span_id"])


def downgrade() -> None:
    op.drop_index("ix_diagnostics_span_id", table_name="diagnostics")
    op.drop_index("ix_diagnostics_severity", table_name="diagnostics")
    op.drop_index("ix_diagnostics_trace_id", table_name="diagnostics")
    op.drop_table("diagnostics")

    op.drop_index("ix_retrieval_results_span_id", table_name="retrieval_results")
    op.drop_table("retrieval_results")

    op.drop_index("ix_spans_parent_span_id", table_name="spans")
    op.drop_index("ix_spans_type", table_name="spans")
    op.drop_index("ix_spans_trace_id", table_name="spans")
    op.drop_table("spans")

    op.drop_index("ix_traces_session_id", table_name="traces")
    op.drop_index("ix_traces_status", table_name="traces")
    op.drop_index("ix_traces_started_at", table_name="traces")
    op.drop_index("ix_traces_project_id", table_name="traces")
    op.drop_table("traces")

    op.drop_index("ix_api_keys_key_prefix", table_name="api_keys")
    op.drop_index("ix_api_keys_project_id", table_name="api_keys")
    op.drop_table("api_keys")
