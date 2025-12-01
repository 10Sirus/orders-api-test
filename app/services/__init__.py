"""
Service factory
services/__init__.py
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.order_repository import OrderRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.outbox_repository import OutboxRepository
from app.services.order_service import OrderService


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    """Dependency injection for OrderService."""
    db = db
    order_repo = OrderRepository(db)
    idempotency_repo = IdempotencyRepository(db)
    outbox_repo = OutboxRepository(db)
    return OrderService(db, order_repo, idempotency_repo, outbox_repo)


__all__ = ["OrderService", "get_order_service"]
