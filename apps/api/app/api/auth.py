"""
Auth router — user registration and login.

Routes:
  POST /auth/register   → create account, return token
  POST /auth/login      → verify credentials, return token
  GET  /auth/me         → current user profile
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.connection import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = UserRepository(db)
    if await repo.get_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_TAKEN", "message": "An account with this email already exists"},
        )
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
        is_verified=False,
    )
    user = await repo.create(user)
    await db.commit()
    token = create_access_token(subject=user.id)
    logger.info("Registered new user %s", user.id)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT",
)
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email.lower())
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account is disabled"},
        )
    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the current authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
