"""
Idempotency dependency
idempotency.py
"""

from typing import Annotated
from fastapi import Header
from app.core.exceptions import ValidationError


async def get_idempotency_key(
    idempotency_key: Annotated[str | None, Header()] = None
) -> str:
    """Extract idempotency key from Idempotency-Key header."""
    if not idempotency_key:
        raise ValidationError("Idempotency-Key header is required")
    return idempotency_key
