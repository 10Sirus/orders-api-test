"""
Outbox model
outbox.py
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class Outbox(Base):
    """Outbox model."""
    
    __tablename__ = "outbox"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(255), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    tenant_id = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_outbox_published_at', 'published_at'),
    )
