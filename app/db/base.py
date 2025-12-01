"""
Database base
base.py
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.order import Order 
from app.models.idempotency import IdempotencyKey 
from app.models.outbox import Outbox 
