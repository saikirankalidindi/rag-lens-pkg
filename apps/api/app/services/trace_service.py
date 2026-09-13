"""
Trace service — business logic for trace listing and retrieval.
Ingestion logic lives in ingestion_service.py (Phase 5).
"""
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.trace_repo import TraceRepository
from app.schemas.trace import PaginatedTraces, TraceListItem, TraceResponse


class TraceService:
    def __init__(self, db: AsyncSession):
        self.repo = TraceRepository(db)

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
    ) -> PaginatedTraces:
        page = max(1, page)
        page_size = min(max(1, page_size), 200)

        traces, total = await self.repo.list_for_project(
            project_id,
            page=page,
            page_size=page_size,
            status=status,
            search=search,
            environment=environment,
            started_after=started_after, started_before=started_before, sort=sort,
        )

        items = [TraceListItem.model_validate(t) for t in traces]
        return PaginatedTraces(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )

    async def get(self, project_id: str, trace_id: str) -> TraceResponse:
        trace = await self.repo.get_by_id(trace_id, project_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TRACE_NOT_FOUND", "message": "Trace not found"},
            )
        return TraceResponse.model_validate(trace)
