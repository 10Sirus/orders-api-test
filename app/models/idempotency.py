"""
Idempotency key model
idempotency.py
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base


class IdempotencyKey(Base):
    """Idempotency key model."""
    
    __tablename__ = "idempotency_keys"
    
    tenant_id = Column(String(255), primary_key=True, nullable=False)
    key = Column(String(255), primary_key=True, nullable=False)
    response_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'key', name='uq_idempotency_tenant_key'),
        Index('ix_idempotency_created_at', 'created_at'),
    )
