"""
Pydantic schemas for the trace ingestion endpoint (POST /v1/traces).

These are the shapes the RAGLens SDK submits. Keep them lenient enough
to accept real-world RAG pipelines without requiring every field.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Span ingestion ─────────────────────────────────────────────────────────────

class RetrievalResultIngest(BaseModel):
    rank: int = Field(..., ge=1)
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    retrieval_method: str = "cosine"
    selected: bool = False
    reranked_rank: Optional[int] = None
    reranker_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SpanIngest(BaseModel):
    id: Optional[str] = None          # SDK may pre-generate; we accept or create
    parent_span_id: Optional[str] = None
    type: str = Field(..., pattern=r"^(query|query_rewrite|retrieval|reranking|context|prompt|llm|response|custom)$")
    name: str = Field(..., min_length=1, max_length=255)
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None  # computed from timestamps if omitted
    status: str = Field(default="success", pattern=r"^(success|warning|error)$")
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None
    # Only populated for retrieval spans
    retrieval_results: Optional[List[RetrievalResultIngest]] = None


# ── Trace ingestion ────────────────────────────────────────────────────────────

class TraceIngest(BaseModel):
    """
    Payload accepted by POST /v1/traces.
    The project is identified by the API key in the Authorization header.
    """
    name: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    user_id: Optional[str] = Field(None, max_length=255)

    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None  # computed if omitted

    status: str = Field(default="success", pattern=r"^(success|warning|error)$")

    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    spans: List[SpanIngest] = Field(default_factory=list)


class TraceIngestResponse(BaseModel):
    trace_id: str


# ── API key schemas ────────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    project_id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]
    revoked_at: Optional[datetime]
    is_active: bool


class ApiKeyCreateResponse(BaseModel):
    """Returned once at key creation — includes the raw key which is never stored."""
    api_key: ApiKeyResponse
    raw_key: str = Field(..., description="Full API key shown exactly once. Store it securely.")
