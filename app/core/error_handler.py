"""
Global error handler
error_handler.py
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DomainError


async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message
        }
    )
