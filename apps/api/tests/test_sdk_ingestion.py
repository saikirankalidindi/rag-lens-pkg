"""SDK/API contract and ingestion persistence orchestration without a database."""
from unittest.mock import AsyncMock

import pytest
from raglens import RAGLens
from raglens.serializers import serialize_trace

from app.schemas.ingestion import TraceIngest
from app.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_sdk_payload_ingests_with_linked_diagnostics():
    with RAGLens(enabled=False).trace("integration") as trace:
        trace.log_retrieval(results=[{"chunk_id": "c", "document_id": "d", "document_name": "Doc",
                                     "content": "text", "score": .2, "selected": False}])
        trace.log_context(context="text", tokens=90, max_tokens=100)
    payload = TraceIngest.model_validate(serialize_trace(trace))
    db = AsyncMock()
    service = IngestionService(db)
    service.repo = AsyncMock()
    async def create(value):
        value.id = "trace_test"
        return value
    service.repo.create.side_effect = create
    result = await service.ingest("project", payload)
    assert result.trace_id == "trace_test"
    rows = service.repo.create_retrieval_results_bulk.call_args.args[0]
    assert rows[0].span_id == trace.spans[0].id
    diagnostics = service.repo.create_diagnostics_bulk.call_args.args[0]
    assert len(diagnostics) == 4
    assert all(d.trace_id == result.trace_id and d.span_id for d in diagnostics)
    db.commit.assert_not_called()  # The route owns the atomic commit.
