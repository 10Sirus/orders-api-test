"""
Integration tests for Orders API
test_integration.py
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import text
from app.models.order import OrderStatus

# Test data
TENANT_ID = "test-tenant"
OTHER_TENANT_ID = "other-tenant"


@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient):
    """Test successful order creation."""
    key = f"key-{uuid.uuid4()}"
    response = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == OrderStatus.DRAFT.value
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_order_idempotent_replay(client: AsyncClient):
    """Test idempotency replay."""
    key = f"key-{uuid.uuid4()}"
    
    # First request
    await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    
    # Second request (replay)
    response = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    if response.status_code != 200:
        print(f"DEBUG FAILURE: {response.text}")
    assert response.status_code == 200
    assert response.json()["status"] == OrderStatus.DRAFT.value


@pytest.mark.asyncio
async def test_create_order_idempotent_conflict(client: AsyncClient):
    """Test idempotency conflict."""
    key = f"key-{uuid.uuid4()}"
    
    # First request
    await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    
    # Second request (different body)
    response = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={"foo": "bar"}
    )
    if response.status_code != 409:
        print(f"DEBUG FAILURE: {response.text}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirm_order_success(client: AsyncClient):
    """Test successful order confirmation."""
    key = f"key-{uuid.uuid4()}"
    create_res = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    order_id = create_res.json()["id"]
    
    response = await client.patch(
        f"/orders/{order_id}/confirm",
        headers={"X-Tenant-Id": TENANT_ID, "If-Match": "1"},
        json={"totalCents": 1000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == OrderStatus.CONFIRMED.value
    assert data["version"] == 2
    assert data["totalCents"] == 1000


@pytest.mark.asyncio
async def test_confirm_order_stale_version(client: AsyncClient):
    """Test optimistic locking failure."""
    key = f"key-{uuid.uuid4()}"
    create_res = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    order_id = create_res.json()["id"]
    
    response = await client.patch(
        f"/orders/{order_id}/confirm",
        headers={"X-Tenant-Id": TENANT_ID, "If-Match": "999"},
        json={"totalCents": 1000}
    )
    assert response.status_code == 409



@pytest.mark.asyncio
async def test_close_order_success(client: AsyncClient):
    """Test successful order closing."""
    key = f"key-{uuid.uuid4()}"
    create_res = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    order_id = create_res.json()["id"]
    
    await client.patch(
        f"/orders/{order_id}/confirm",
        headers={"X-Tenant-Id": TENANT_ID, "If-Match": "1"},
        json={"totalCents": 1000}
    )
    
    response = await client.post(
        f"/orders/{order_id}/close",
        headers={"X-Tenant-Id": TENANT_ID}
    )
    assert response.status_code == 200
    assert response.json()["status"] == OrderStatus.CLOSED.value


@pytest.mark.asyncio
async def test_close_order_outbox_entry(client: AsyncClient, db_session):
    """Test outbox entry creation."""
    key = f"key-{uuid.uuid4()}"
    create_res = await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    order_id = create_res.json()["id"]
    
    await client.patch(
        f"/orders/{order_id}/confirm",
        headers={"X-Tenant-Id": TENANT_ID, "If-Match": "1"},
        json={"totalCents": 1000}
    )
    
    await client.post(
        f"/orders/{order_id}/close",
        headers={"X-Tenant-Id": TENANT_ID}
    )
    
    result = await db_session.execute(
        text("SELECT * FROM outbox WHERE order_id = :oid"),
        {"oid": order_id}
    )
    row = result.fetchone()
    assert row is not None
    assert row.event_type == "orders.closed"
    

@pytest.mark.asyncio
async def test_list_orders_pagination(client: AsyncClient):
    """Test keyset pagination."""
    # Create 15 orders
    for i in range(15):
        await client.post(
            "/orders",
            headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": f"page-test-split-{i}"},
            json={}
        )
    
    response = await client.get(
        "/orders?limit=10",
        headers={"X-Tenant-Id": TENANT_ID}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 10
    assert response.json()["nextCursor"] is not None


@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient):
    """Test tenant isolation."""
    key = f"key-{uuid.uuid4()}"
    await client.post(
        "/orders",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": key},
        json={}
    )
    
    response = await client.get(
        "/orders",
        headers={"X-Tenant-Id": OTHER_TENANT_ID}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
