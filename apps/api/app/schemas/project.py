"""Pydantic schemas for Project and ProjectStats."""
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")


# ── Request schemas ────────────────────────────────────────────────────────────

class ProjectNameValidation(BaseModel):
    @field_validator("name", mode="before", check_fields=False)
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            value = " ".join(value.split())
        return value


class ProjectCreate(ProjectNameValidation):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ProjectUpdate(ProjectNameValidation):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    capture_query: bool | None = None
    capture_context: bool | None = None
    capture_prompt: bool | None = None
    capture_response: bool | None = None


# ── Response schemas ───────────────────────────────────────────────────────────

class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    owner_id: str
    name: str
    description: str | None
    slug: str
    is_active: bool
    capture_query: bool
    capture_context: bool
    capture_prompt: bool
    capture_response: bool
    created_at: datetime
    updated_at: datetime


class ProjectSummary(ProjectResponse):
    trace_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    avg_latency_ms: float = 0
    last_trace_at: datetime | None = None


class ProjectStats(BaseModel):
    """Aggregate statistics for the project overview page."""
    total_tokens: int = 0
    success_rate: float = 0
    activity: list[dict] = Field(default_factory=list)
    latency_buckets: list[dict] = Field(default_factory=list)
    total_traces: int = 0
    error_rate: float = 0.0          # 0.0–1.0
    avg_latency_ms: float = 0.0
    avg_tokens: float = 0.0
    traces_change_pct: float | None = None  # vs. previous period


class ProjectWithStats(ProjectResponse):
    stats: ProjectStats = Field(default_factory=ProjectStats)
