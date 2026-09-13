"""
Project service — business logic for project management.
"""
import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectStats, ProjectUpdate


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def get(self, project_id: str, owner_id: str) -> Project:
        project = await self.repo.get_by_id(project_id)
        if not project or project.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROJECT_NOT_FOUND", "message": "Project not found"},
            )
        return project

    async def list_for_owner(self, owner_id: str) -> list[Project]:
        return await self.repo.list_by_owner(owner_id)

    async def list_summaries(self, owner_id: str) -> list[dict]:
        return await self.repo.list_with_activity(owner_id)

    async def ensure_unique_name(self, owner_id: str, name: str, exclude_id: str | None = None):
        if await self.repo.name_exists(owner_id, name, exclude_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                detail={"code": "PROJECT_NAME_EXISTS", "message": "A project with this name already exists. Choose a different name."})

    async def create(self, data: ProjectCreate, owner_id: str) -> Project:
        await self.repo.lock_owner(owner_id)
        await self.ensure_unique_name(owner_id, data.name)
        slug = _slugify(data.name)
        # Ensure slug uniqueness within the owner's projects
        base_slug = slug or "project"
        slug = base_slug
        suffix = 2
        while await self.repo.get_by_slug(owner_id, slug):
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        project = Project(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            slug=slug,
        )
        return await self.repo.create(project)

    async def update(
        self, project_id: str, owner_id: str, data: ProjectUpdate
    ) -> Project:
        await self.repo.lock_owner(owner_id)
        project = await self.get(project_id, owner_id)
        if data.name is not None and data.name != project.name:
            await self.ensure_unique_name(owner_id, data.name, exclude_id=project_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(project, field, value)
        return await self.repo.update(project)

    async def get_stats(self, project_id: str, owner_id: str) -> ProjectStats:
        await self.get(project_id, owner_id)  # verify ownership
        raw = await self.repo.get_trace_stats(project_id)
        return ProjectStats(**raw)
