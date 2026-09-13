"""
ApiKey repository — database access for the ApiKey model.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, key_id: str, project_id: str) -> Optional[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Look up an active key by its SHA-256 hash."""
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: str) -> List[ApiKey]:
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.project_id == project_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def update_last_used(self, api_key: ApiKey) -> None:
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def revoke(self, api_key: ApiKey) -> ApiKey:
        api_key.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key
