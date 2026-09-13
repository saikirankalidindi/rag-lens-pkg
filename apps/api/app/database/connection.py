"""
Async SQLAlchemy engine and session factory.

Usage in FastAPI routes via dependency injection:
    async def endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""
from collections.abc import AsyncGenerator
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# The engine is created once at import time.
# connect_args are passed to asyncpg; adjust pool sizes for production.
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
