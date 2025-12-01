"""
Tenant dependency
tenant.py
"""

from typing import Annotated
from fastapi import Header
from app.core.exceptions import ValidationError


async def get_tenant_id(
    x_tenant_id: Annotated[str | None, Header()] = None
) -> str:
    """Extract tenant ID from X-Tenant-Id header."""
    if not x_tenant_id:
        raise ValidationError("X-Tenant-Id header is required")
    return x_tenant_id
