"""
Trace repository — database access for Trace, Span, and RetrievalResult.
"""
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.diagnostic import Diagnostic
from app.models.retrieval_result import RetrievalResult
from app.models.span import Span
from app.models.trace import Trace


class TraceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Trace queries ──────────────────────────────────────────────────────

    async def get_by_id(self, trace_id: str, project_id: str) -> Trace | None:
        """Fetch a single trace with all spans and diagnostics loaded."""
        result = await self.db.execute(
            select(Trace)
            .where(Trace.id == trace_id, Trace.project_id == project_id)
            .options(
                selectinload(Trace.spans).selectinload(Span.retrieval_results),
                selectinload(Trace.spans).selectinload(Span.children),
                selectinload(Trace.diagnostics),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        search: str | None = None,
        environment: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
        sort: str = "newest",
    ) -> tuple[list[Trace], int]:
        """Return a paginated list of traces (lightweight — no spans loaded)."""
        query = select(Trace).where(Trace.project_id == project_id)

        if status:
            query = query.where(Trace.status == status)

        if search:
            # Search against the query text stored in input JSONB
            query = query.where(
                or_(
                    Trace.name.ilike(f"%{search}%"),
                    Trace.input["query"].astext.ilike(f"%{search}%"),
                )
            )

        if environment:
            query = query.where(
                Trace.metadata_["environment"].astext == environment
            )

        if started_after:
            query = query.where(Trace.started_at >= started_after)
        if started_before:
            query = query.where(Trace.started_at < started_before)

        # Count total before pagination
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one() or 0

        # Apply ordering and pagination
        query = (
            query
            .order_by({"newest": Trace.started_at.desc(), "oldest": Trace.started_at.asc(), "slowest": Trace.duration_ms.desc(), "fastest": Trace.duration_ms.asc()}[sort], Trace.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        traces = list(result.scalars().all())
        return traces, total

    async def create(self, trace: Trace) -> Trace:
        self.db.add(trace)
        await self.db.flush()
        await self.db.refresh(trace)
        return trace

    # ── Span queries ───────────────────────────────────────────────────────

    async def create_span(self, span: Span) -> Span:
        self.db.add(span)
        await self.db.flush()
        return span

    async def create_spans_bulk(self, spans: list[Span]) -> None:
        self.db.add_all(spans)
        await self.db.flush()

    # ── RetrievalResult queries ────────────────────────────────────────────

    async def create_retrieval_results_bulk(
        self, results: list[RetrievalResult]
    ) -> None:
        self.db.add_all(results)
        await self.db.flush()

    # ── Diagnostic queries ─────────────────────────────────────────────────

    async def create_diagnostics_bulk(self, diagnostics: list[Diagnostic]) -> None:
        self.db.add_all(diagnostics)
        await self.db.flush()
