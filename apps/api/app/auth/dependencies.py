"""
FastAPI dependency helpers for JWT user authentication.

Phase 3 design: for development/seeded data the dependency returns the
seed user without requiring a real login flow in the browser.  Full
authentication is enforced in Phase 5 when the login/register UI ships.
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from a Bearer token.

    Raises HTTP 401 when:
      - No token is provided
      - Token is invalid / expired
      - User is not found or inactive
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_AUTHENTICATED", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )
    return user
