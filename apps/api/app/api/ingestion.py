"""
Ingestion router — accepts traces from the RAGLens SDK.

Route:
  POST /v1/traces

Authentication:
  Authorization: Bearer <project_api_key>

The API key identifies both the caller and the target project.
This endpoint intentionally does NOT use the JWT user auth —
SDK keys are separate from browser session tokens.
"""
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.connection import get_db
from app.models.api_key import ApiKey
from app.repositories.api_key_repo import ApiKeyRepository
from app.schemas.ingestion import TraceIngest, TraceIngestResponse
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

_bearer = HTTPBearer(auto_error=False)


async def _resolve_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Validate the Bearer API key and return the corresponding ApiKey record."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "API_KEY_REQUIRED", "message": "API key required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    key_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    repo = ApiKeyRepository(db)
    api_key = await repo.get_by_hash(key_hash)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_API_KEY", "message": "Invalid or revoked API key"},
        )
    # Touch last_used_at in the background (non-blocking for the caller)
    await repo.update_last_used(api_key)
    return api_key


@router.post(
    "/traces",
    response_model=TraceIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a trace from the RAGLens SDK",
)
async def ingest_trace(
    request: Request,
    body: TraceIngest,
    api_key: ApiKey = Depends(_resolve_api_key),
    db: AsyncSession = Depends(get_db),
) -> TraceIngestResponse:
    # Guard against oversized payloads (Content-Length based check)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_trace_payload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Trace payload exceeds {settings.max_trace_payload_bytes} bytes",
            },
        )

    svc = IngestionService(db)
    result = await svc.ingest(api_key.project_id, body)
    await db.commit()
    return result
