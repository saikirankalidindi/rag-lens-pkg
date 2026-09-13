"""
Projects router.

Routes:
  GET    /projects                     → list all projects for the current user
  POST   /projects                     → create a new project
  GET    /projects/{projectId}         → get project detail
  PATCH  /projects/{projectId}         → update project settings
  GET    /projects/{projectId}/stats   → aggregate stats for overview page
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectStats,
    ProjectSummary,
    ProjectUpdate,
    ProjectWithStats,
)
from app.services.project_service import ProjectService

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get(
    "",
    response_model=list[ProjectSummary],
    summary="List all projects owned by the current user",
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    svc: ProjectService = Depends(_get_service),
) -> list[ProjectSummary]:
    projects = await svc.list_summaries(current_user.id)
    return [ProjectSummary.model_validate(p) for p in projects]


@router.post(
    "",
    response_model=ProjectWithStats,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    svc: ProjectService = Depends(_get_service),
) -> ProjectWithStats:
    project = await svc.create(body, current_user.id)
    return ProjectWithStats.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectWithStats,
    summary="Get a project by ID",
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    svc: ProjectService = Depends(_get_service),
) -> ProjectWithStats:
    project = await svc.get(project_id, current_user.id)
    return ProjectWithStats.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project settings",
)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    svc: ProjectService = Depends(_get_service),
) -> ProjectResponse:
    project = await svc.update(project_id, current_user.id, body)
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}/stats",
    response_model=ProjectStats,
    summary="Aggregate stats for the project overview page",
)
async def get_project_stats(
    project_id: str,
    current_user: User = Depends(get_current_user),
    svc: ProjectService = Depends(_get_service),
) -> ProjectStats:
    return await svc.get_stats(project_id, current_user.id)
