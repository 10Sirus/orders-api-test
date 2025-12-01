"""
Optimistic lock dependency
optimistic_lock.py
"""

from typing import Annotated
from fastapi import Header
from app.core.exceptions import ValidationError


async def get_if_match(
    if_match: Annotated[str | None, Header()] = None
) -> int:
    """Extract version from If-Match header."""
    if not if_match:
        raise ValidationError("If-Match header is required")
    
    version_str = if_match.strip('"')
    
    try:
        version = int(version_str)
        if version < 1:
            raise ValueError("Version must be positive")
        return version
    except ValueError:
        raise ValidationError(f"If-Match header must be a positive integer, got: {if_match}")
