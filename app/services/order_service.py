"""
Order service
order_service.py
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Optional
from app.repositories.order_repository import OrderRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.outbox_repository import OutboxRepository
from app.models.order import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError, PreconditionFailedError, ValidationError, InternalServerError
from app.core.config import settings
from app.utils.idempotency import hash_body
from app.utils.pagination import encode_cursor, decode_cursor
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger

logger = get_logger(__name__)

class OrderService:
    """Service for order business logic."""
    
    def __init__(
        self,
        db: AsyncSession,
        order_repo: OrderRepository,
        idempotency_repo: IdempotencyRepository,
        outbox_repo: OutboxRepository
    ):
        """Initialize with repositories."""
        self.db = db
        self.order_repo = order_repo
        self.idempotency_repo = idempotency_repo
        self.outbox_repo = outbox_repo
    
    async def create_order_idempotent(
        self,
        tenant_id: str,
        key: str,
        body: dict
    ) -> Tuple[dict, int]:
        """Create draft order with idempotency."""
        logger.info("Creating draft order with idempotency")
        try:
            now = datetime.now(timezone.utc)
            body_hash = hash_body(body)
            
            # Check for existing idempotency key
            record = await self.idempotency_repo.find(tenant_id, key)
            
            if record:
                # Check if record is within 1-hour window
                record_time = record.created_at.replace(tzinfo=timezone.utc)
                ttl_cutoff = now - timedelta(hours=settings.idempotency_ttl_hours)

                # TTL still valid → attempt replay
                if record_time >= ttl_cutoff:
                    await self.idempotency_repo.delete(record)
                    stored_hash = record.response_json["body_hash"]

                    # Same body → replay
                    if stored_hash == body_hash:
                        return record.response_json["response"], 200

                    # Same key + different body → 409
                    raise ConflictError(
                        f"Idempotency key '{key}' already used with different request body"
                    )
                
            # Create new draft order
            order = await self.order_repo.create_draft(tenant_id)
            
            # Prepare response
            response = {
                "id": str(order.id),
                "tenantId": order.tenant_id,
                "status": order.status.value,
                "version": order.version,
                "createdAt": order.created_at.isoformat(),
            }
            
            # Store idempotency key
            await self.idempotency_repo.store(tenant_id, key, body_hash, response)
            
            await self.db.commit()
            
            return response, 201
        except (ConflictError, NotFoundError, PreconditionFailedError, ValidationError):
            raise
        except Exception as e:
            raise InternalServerError(f"Failed to create order: {str(e)}")
    
    async def confirm_order(
        self,
        order_id: str,
        tenant_id: str,
        expected_version: int,
        total_cents: int
    ) -> dict:
        """Confirm order with optimistic locking."""
        logger.info("Confirming order with optimistic locking")
        try:
            order = await self.order_repo.find_by_id(uuid.UUID(order_id), tenant_id)
            
            if not order:
                raise NotFoundError(f"Order {order_id} not found")
            
            if order.version != expected_version:
                raise ConflictError(
                    "Stale version"
                )
            
            order = await self.order_repo.update_to_confirmed(order, total_cents)

            await self.db.commit()
            
            return {
                "id": str(order.id),
                "status": order.status.value,
                "version": order.version,
                "totalCents": order.total_cents,
            }
        except (ConflictError, NotFoundError, PreconditionFailedError, ValidationError):
            raise
        except Exception as e:
            raise InternalServerError(f"Failed to confirm order: {str(e)}")
    
    async def close_order(
        self,
        order_id: str,
        tenant_id: str
    ) -> dict:
        """Close order and create outbox entry."""
        logger.info("Closing order and creating outbox entry")
        try:
            order = await self.order_repo.find_by_id_with_lock(uuid.UUID(order_id), tenant_id)
            
            if not order:
                raise NotFoundError(f"Order {order_id} not found")
            
            if order.status != OrderStatus.CONFIRMED:
                raise PreconditionFailedError(
                    f"Can only close confirmed orders, current status: {order.status.value}"
                )
            
            order = await self.order_repo.update_to_closed(order)
            
            # Create outbox entry
            await self.outbox_repo.create_event(
                event_type="orders.closed",
                order_id=order.id,
                tenant_id=tenant_id,
                payload={
                    "orderId": str(order.id),
                    "tenantId": tenant_id,
                    "totalCents": order.total_cents,
                    "closedAt": order.updated_at.isoformat()
                }
            )
            await self.db.commit()
            
            return {
                "id": str(order.id),
                "status": order.status.value,
                "version": order.version
            }
        except (ConflictError, NotFoundError, PreconditionFailedError, ValidationError):
            raise
        except Exception as e:
            raise InternalServerError(f"Failed to close order: {str(e)}")
    
    async def list_orders(
        self,
        tenant_id: str,
        limit: int,
        cursor: Optional[str] = None
    ) -> Tuple[List[dict], Optional[str]]:
        """List orders with keyset pagination."""
        logger.info("Listing orders with keyset pagination")
        try:
            cursor_data = decode_cursor(cursor)
            
            cursor_created_at = None
            cursor_id = None
            if cursor_data:
                cursor_created_at, cursor_id_str = cursor_data
                cursor_id = uuid.UUID(cursor_id_str)
            
            orders = await self.order_repo.list_orders(
                tenant_id, limit, cursor_created_at, cursor_id
            )
            
            has_more = len(orders) > limit
            if has_more:
                next_item = orders[limit - 1]
                next_cursor = encode_cursor(next_item.created_at, str(next_item.id))
                orders = orders[:limit]
            else:
                next_cursor = None

            items = [
                {
                    "id": str(order.id),
                    "tenantId": order.tenant_id,
                    "status": order.status.value,
                    "version": order.version,
                    "totalCents": order.total_cents,
                    "createdAt": order.created_at.isoformat(),
                    "updatedAt": order.updated_at.isoformat(),
                }
                for order in orders
            ]
            
            return items, next_cursor
        except (ConflictError, NotFoundError, PreconditionFailedError, ValidationError):
            raise
        except Exception as e:
            raise InternalServerError(f"Failed to list orders: {str(e)}")
