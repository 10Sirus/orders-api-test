"""
Idempotency repository
idempotency_repository.py
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.idempotency import IdempotencyKey


class IdempotencyRepository:
    """Repository for idempotency key data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def find(self, tenant_id: str, key: str) -> Optional[IdempotencyKey]:
        """Find idempotency key record."""
        stmt = select(IdempotencyKey).where(
            and_(
                IdempotencyKey.tenant_id == tenant_id,
                IdempotencyKey.key == key
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def store(self, tenant_id: str, key: str, body_hash: str, response: dict) -> IdempotencyKey:
        """Store idempotency key with response."""
        record = IdempotencyKey(
            tenant_id=tenant_id,
            key=key,
            response_json={
                "response": response,
                "body_hash": body_hash
            },
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def delete(self, record: IdempotencyKey) -> None:
        """Delete idempotency key record."""
        await self.db.delete(record)
        await self.db.flush()   
