"""
Orders router
orders.py
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_tenant_id, get_idempotency_key, get_if_match
from app.schemas.order import DraftOrderResponse, OrderResponse, ConfirmOrderRequest, PaginatedOrdersResponse, ClosedOrderResponse
from app.services import OrderService, get_order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=DraftOrderResponse)
async def create_order(
    response: Response,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    idempotency_key: Annotated[str, Depends(get_idempotency_key)],
    service: Annotated[OrderService, Depends(get_order_service)],
    body: dict = Body(default={}),
):
    """Create draft order with idempotency."""
    order_data, status_code = await service.create_order_idempotent(
        tenant_id=tenant_id,
        key=idempotency_key,
        body=body
    )
    
    
    response.status_code = status_code
    return order_data


@router.patch("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: str,
    request: ConfirmOrderRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    expected_version: Annotated[int, Depends(get_if_match)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Confirm order with optimistic locking."""
    result = await service.confirm_order(
        order_id=order_id,
        tenant_id=tenant_id,
        expected_version=expected_version,
        total_cents=request.totalCents
    )
   
    return result


@router.post("/{order_id}/close", response_model=ClosedOrderResponse)
async def close_order(
    order_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    """Close order and create outbox entry."""
    result = await service.close_order(
        order_id=order_id,
        tenant_id=tenant_id
    )
    return result


@router.get("", response_model=PaginatedOrdersResponse)
async def list_orders(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[OrderService, Depends(get_order_service)],
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = Query(default=None)
):
    """List orders with keyset pagination."""
    items, next_cursor = await service.list_orders(
        tenant_id=tenant_id,
        limit=limit,
        cursor=cursor
    )
    return PaginatedOrdersResponse(items=items, nextCursor=next_cursor)
