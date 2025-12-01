"""
FastAPI application
main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.error_handler import domain_error_handler
from app.db.session import engine
from app.api.routers import orders_router
from app.core.middleware import correlation_id_middleware

# Create FastAPI app
app = FastAPI(
    title="Orders API",
    description="Production grade Orders API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(DomainError, domain_error_handler)

# Include routers
app.include_router(orders_router)

# Middleware
app.middleware("http")(correlation_id_middleware)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint with database connection check."""
    db_status = "unknown"
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
