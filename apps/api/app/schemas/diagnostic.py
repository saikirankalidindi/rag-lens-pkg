"""Pydantic schemas for Diagnostic responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DiagnosticResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    trace_id: str
    span_id: Optional[str]
    severity: str    # info | warning | error
    category: str    # retrieval | context | latency | tokens | generation
    title: str
    description: str
    evidence: Dict[str, Any]
    suggestions: List[str]
    created_at: datetime
