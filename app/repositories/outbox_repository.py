"""
Outbox repository
outbox_repository.py
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import Outbox


class OutboxRepository:
    """Repository for outbox data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_event(
        self,
        event_type: str,
        order_id: uuid.UUID,
        tenant_id: str,
        payload: dict
    ) -> Outbox:
        """Create outbox event."""
        outbox = Outbox(
            id=uuid.uuid4(),
            event_type=event_type,
            order_id=order_id,
            tenant_id=tenant_id,
            payload=payload,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(outbox)
        await self.db.flush()
        return outbox
