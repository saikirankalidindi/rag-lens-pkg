"""Pydantic schemas for Trace and Span responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Span ──────────────────────────────────────────────────────────────────────

class RetrievalResultResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    span_id: str
    rank: int
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    retrieval_method: str
    selected: bool
    reranked_rank: Optional[int]
    reranker_score: Optional[float]
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SpanResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    trace_id: str
    parent_span_id: Optional[str]
    type: str
    name: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: int
    status: str
    input: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    attributes: Optional[Dict[str, Any]]
    retrieval_results: List[RetrievalResultResponse] = []
    # children is populated from the flat list client-side or in the service layer
    children: List["SpanResponse"] = []


SpanResponse.model_rebuild()


# ── Trace ─────────────────────────────────────────────────────────────────────

class TraceMetrics(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0


class TraceListItem(BaseModel):
    """Lightweight trace row for the trace explorer table.
    Heavy payloads (spans, full prompt/context) are excluded.
    """
    model_config = {"from_attributes": True}

    id: str
    name: str
    status: str
    duration_ms: int
    input: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")
    started_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class TraceResponse(BaseModel):
    """Full trace detail including all spans and diagnostics."""
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: str
    project_id: str
    name: str
    session_id: Optional[str]
    user_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: int
    status: str
    input: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")
    spans: List[SpanResponse] = []
    diagnostics: List["DiagnosticResponse"] = []


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginatedTraces(BaseModel):
    items: List[TraceListItem]
    total: int
    page: int
    page_size: int
    has_next: bool


# Import here to avoid circular; DiagnosticResponse defined in diagnostic.py
from app.schemas.diagnostic import DiagnosticResponse  # noqa: E402

TraceResponse.model_rebuild()
