"""
Error schema
error.py
"""

from typing import Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    code: str
    message: str
    details: Optional[dict] = None
