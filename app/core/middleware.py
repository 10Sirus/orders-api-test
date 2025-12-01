"""
Middleware for correlation ID
"""
from fastapi import Request
from app.core.logging import set_correlation_id
import uuid

async def correlation_id_middleware(request: Request, call_next):
    """Middleware for correlation ID"""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
