"""
Ingestion service — persists a submitted trace payload to the database.

Responsible for:
  1. Materialising Trace / Span / RetrievalResult ORM objects from ingest schemas.
  2. Computing duration_ms when not provided by the SDK.
  3. Running the diagnostics engine after persisting.
  4. Committing the transaction atomically.

Ingestion is separated from the trace-read service to keep responsibilities
clear and make it easy to add a queue / background worker later.
"""
import logging
from datetime import timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.diagnostics.engine import run_diagnostics
from app.models.diagnostic import Diagnostic
from app.models.retrieval_result import RetrievalResult
from app.models.span import Span
from app.models.trace import Trace
from app.repositories.trace_repo import TraceRepository
from app.schemas.ingestion import SpanIngest, TraceIngest, TraceIngestResponse

logger = logging.getLogger(__name__)


def _duration(ingest) -> int:
    """Compute duration_ms from timestamps when the SDK didn't supply it."""
    if ingest.duration_ms is not None:
        return ingest.duration_ms
    if ingest.started_at and ingest.ended_at:
        delta = ingest.ended_at - ingest.started_at
        return max(0, int(delta.total_seconds() * 1000))
    return 0


def _build_span(span_in: SpanIngest, trace_id: str) -> tuple[Span, list[RetrievalResult]]:
    """Convert a SpanIngest into a Span ORM object + any RetrievalResult objects."""
    span = Span(
        id=span_in.id or None,   # let make_id default fire when None
        trace_id=trace_id,
        parent_span_id=span_in.parent_span_id,
        type=span_in.type,
        name=span_in.name,
        started_at=span_in.started_at.replace(tzinfo=timezone.utc)
        if span_in.started_at.tzinfo is None
        else span_in.started_at,
        ended_at=span_in.ended_at.replace(tzinfo=timezone.utc)
        if span_in.ended_at and span_in.ended_at.tzinfo is None
        else span_in.ended_at,
        duration_ms=_duration(span_in),
        status=span_in.status,
        input=span_in.input,
        output=span_in.output,
        attributes=span_in.attributes,
    )
    if span_in.id:
        # SDK pre-assigned an ID — honour it so parent-child references work.
        span.id = span_in.id

    retrieval_results: list[RetrievalResult] = []
    if span_in.retrieval_results:
        for rr_in in span_in.retrieval_results:
            rr = RetrievalResult(
                span_id="__placeholder__",   # filled after span.id is known
                rank=rr_in.rank,
                chunk_id=rr_in.chunk_id,
                document_id=rr_in.document_id,
                document_name=rr_in.document_name,
                content=rr_in.content,
                score=rr_in.score,
                retrieval_method=rr_in.retrieval_method,
                selected=rr_in.selected,
                reranked_rank=rr_in.reranked_rank,
                reranker_score=rr_in.reranker_score,
                metadata_=rr_in.metadata,
            )
            retrieval_results.append(rr)

    return span, retrieval_results


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TraceRepository(db)

    async def ingest(self, project_id: str, payload: TraceIngest) -> TraceIngestResponse:
        """
        Persist a complete trace and return its ID.

        The entire operation runs inside a single unit of work.
        The caller (route handler) commits the session.
        """
        trace = Trace(
            project_id=project_id,
            name=payload.name,
            session_id=payload.session_id,
            user_id=payload.user_id,
            started_at=payload.started_at.replace(tzinfo=timezone.utc)
            if payload.started_at.tzinfo is None
            else payload.started_at,
            ended_at=payload.ended_at.replace(tzinfo=timezone.utc)
            if payload.ended_at and payload.ended_at.tzinfo is None
            else payload.ended_at,
            duration_ms=_duration(payload),
            status=payload.status,
            input=payload.input,
            output=payload.output,
            metrics=payload.metrics,
            metadata_=payload.metadata,
        )
        trace = await self.repo.create(trace)

        spans_orm: list[Span] = []
        all_retrieval: list[RetrievalResult] = []

        for span_in in payload.spans:
            span, retrieval_results = _build_span(span_in, trace.id)
            spans_orm.append(span)
            # We need the span flushed to know its ID before linking retrieval results
            # — handled in bulk after all spans are added.
            all_retrieval.extend(retrieval_results)

        if spans_orm:
            await self.repo.create_spans_bulk(spans_orm)
            # Now spans have IDs — patch retrieval_result.span_id
            ri = 0
            for span_in, span_orm in zip(payload.spans, spans_orm):
                n = len(span_in.retrieval_results or [])
                for rr in all_retrieval[ri: ri + n]:
                    rr.span_id = span_orm.id
                ri += n

            if all_retrieval:
                await self.repo.create_retrieval_results_bulk(all_retrieval)

        # Run diagnostics synchronously (deterministic, fast)
        diagnostics = run_diagnostics(trace, spans_orm, all_retrieval)
        if diagnostics:
            await self.repo.create_diagnostics_bulk(diagnostics)

        logger.info("Ingested trace %s for project %s", trace.id, project_id)
        return TraceIngestResponse(trace_id=trace.id)
