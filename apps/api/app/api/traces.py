"""
Traces router.

Routes:
  GET /projects/{projectId}/traces              → list traces (paginated, filtered)
  GET /projects/{projectId}/traces/{traceId}    → get full trace detail
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.trace import PaginatedTraces, TraceResponse
from app.services.project_service import ProjectService
from app.services.trace_service import TraceService

router = APIRouter()


def _get_trace_svc(db: AsyncSession = Depends(get_db)) -> TraceService:
    return TraceService(db)


def _get_project_svc(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get(
    "/projects/{project_id}/traces",
    response_model=PaginatedTraces,
    summary="List traces for a project",
)
async def list_traces(
    project_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = Query(None, pattern=r"^(success|warning|error)$"),
    search: str | None = Query(None, max_length=255),
    environment: str | None = Query(None, max_length=64),
    started_after: datetime | None = Query(None),
    started_before: datetime | None = Query(None),
    sort: str = Query("newest", pattern="^(newest|oldest|slowest|fastest)$"),
    current_user: User = Depends(get_current_user),
    project_svc: ProjectService = Depends(_get_project_svc),
    trace_svc: TraceService = Depends(_get_trace_svc),
) -> PaginatedTraces:
    # Verify the user owns this project (raises 404 otherwise)
    await project_svc.get(project_id, current_user.id)

    return await trace_svc.list_for_project(
        project_id,
        page=page,
        page_size=page_size,
        status=status,
        search=search,
        environment=environment,
        started_after=started_after, started_before=started_before, sort=sort,
    )


@router.get(
    "/projects/{project_id}/traces/{trace_id}",
    response_model=TraceResponse,
    summary="Get full trace detail with all spans and diagnostics",
)
async def get_trace(
    project_id: str,
    trace_id: str,
    current_user: User = Depends(get_current_user),
    project_svc: ProjectService = Depends(_get_project_svc),
    trace_svc: TraceService = Depends(_get_trace_svc),
) -> TraceResponse:
    # Verify ownership
    await project_svc.get(project_id, current_user.id)
    return await trace_svc.get(project_id, trace_id)
