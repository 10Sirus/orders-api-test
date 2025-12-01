"""
Order model
order.py
"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class OrderStatus(str, enum.Enum):
    """Order status enum."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CLOSED = "closed"


class Order(Base):
    """Order model."""
    
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DRAFT)
    version = Column(Integer, nullable=False, default=1)
    total_cents = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_orders_tenant_created_id', 'tenant_id', 'created_at', 'id'),
        Index('ix_orders_tenant_id', 'tenant_id', 'id'),
    )
