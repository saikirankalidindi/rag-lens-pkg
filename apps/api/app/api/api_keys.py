"""
API Keys router.

Routes:
  GET    /projects/{projectId}/api-keys            → list API keys for the project
  POST   /projects/{projectId}/api-keys            → create a new API key (returns raw key once)
  DELETE /projects/{projectId}/api-keys/{keyId}    → revoke an API key
"""
import hashlib
import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.api_key_repo import ApiKeyRepository
from app.schemas.ingestion import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse
from app.services.project_service import ProjectService

router = APIRouter()


def _get_project_svc(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


def _get_key_repo(db: AsyncSession = Depends(get_db)) -> ApiKeyRepository:
    return ApiKeyRepository(db)


@router.get(
    "/projects/{project_id}/api-keys",
    response_model=List[ApiKeyResponse],
    summary="List API keys for a project",
)
async def list_api_keys(
    project_id: str,
    current_user: User = Depends(get_current_user),
    project_svc: ProjectService = Depends(_get_project_svc),
    key_repo: ApiKeyRepository = Depends(_get_key_repo),
) -> List[ApiKeyResponse]:
    await project_svc.get(project_id, current_user.id)
    keys = await key_repo.list_for_project(project_id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.post(
    "/projects/{project_id}/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key (raw key shown once)",
)
async def create_api_key(
    project_id: str,
    body: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_svc: ProjectService = Depends(_get_project_svc),
    key_repo: ApiKeyRepository = Depends(_get_key_repo),
) -> ApiKeyCreateResponse:
    await project_svc.get(project_id, current_user.id)

    # Generate a cryptographically secure key: rgl_test_<48 random hex chars>
    raw_key = "rgl_test_" + secrets.token_hex(24)
    key_prefix = raw_key[:20]           # e.g. "rgl_test_abc123ef..." (first 20 chars)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        project_id=project_id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    api_key = await key_repo.create(api_key)
    await db.commit()

    return ApiKeyCreateResponse(
        api_key=ApiKeyResponse.model_validate(api_key),
        raw_key=raw_key,
    )


@router.delete(
    "/projects/{project_id}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
)
async def revoke_api_key(
    project_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_svc: ProjectService = Depends(_get_project_svc),
    key_repo: ApiKeyRepository = Depends(_get_key_repo),
) -> None:
    await project_svc.get(project_id, current_user.id)
    api_key = await key_repo.get_by_id(key_id, project_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "API_KEY_NOT_FOUND", "message": "API key not found"},
        )
    await key_repo.revoke(api_key)
    await db.commit()
