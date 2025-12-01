"""
Order schemas
order.py
"""

from typing import Optional
from pydantic import BaseModel, Field


class DraftOrderResponse(BaseModel):
    """Draft order response schema"""
    
    id: str
    tenantId: str
    status: str
    version: int
    createdAt: str
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema"""
    
    id: str
    status: str
    version: int
    totalCents: Optional[int] = None
 
    class Config:
        from_attributes = True

class ClosedOrderResponse(BaseModel):
    """Closed order response schema"""
    
    id: str
    status: str
    version: int
 
    class Config:
        from_attributes = True


class ConfirmOrderRequest(BaseModel):
    """Confirm order request."""
    
    totalCents: int = Field(..., gt=0, description="Total amount in cents")


class PaginatedOrdersResponse(BaseModel):
    """Paginated orders response."""
    
    items: list[OrderResponse]
    nextCursor: Optional[str] = None
