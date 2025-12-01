"""
Order repository
order_repository.py
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderStatus


class OrderRepository:
    """Repository for order data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_draft(self, tenant_id: str) -> Order:
        """Create a new draft order."""
        order = Order(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            status=OrderStatus.DRAFT,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(order)
        await self.db.flush()
        return order
    
    async def find_by_id(self, order_id: uuid.UUID, tenant_id: str) -> Optional[Order]:
        """Find order by ID and tenant."""
        stmt = select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_id_with_lock(self, order_id: uuid.UUID, tenant_id: str) -> Optional[Order]:
        """Find order by ID with row lock."""
        stmt = select(Order).where(
            and_(
                Order.id == order_id,
                Order.tenant_id == tenant_id
            )
        ).with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_to_confirmed(self, order: Order, total_cents: int) -> Order:
        """Update order to confirmed status."""
        order.status = OrderStatus.CONFIRMED
        order.total_cents = total_cents
        order.version += 1
        order.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return order
    
    async def update_to_closed(self, order: Order) -> Order:
        """Update order to closed status."""
        order.status = OrderStatus.CLOSED
        order.version += 1
        order.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return order
    
    async def list_orders(
        self,
        tenant_id: str,
        limit: int,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[uuid.UUID] = None
    ) -> List[Order]:
        """List orders with keyset pagination."""
        stmt = select(Order).where(Order.tenant_id == tenant_id)
        
        if cursor_created_at and cursor_id:
            stmt = stmt.where(
                or_(
                    Order.created_at < cursor_created_at,
                    and_(
                        Order.created_at == cursor_created_at,
                        Order.id < cursor_id
                    )
                )
            )
        
        stmt = stmt.order_by(Order.created_at.desc(), Order.id.desc()).limit(limit + 1)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
