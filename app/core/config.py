"""
Configuration settings
config.py
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    database_url: str = "postgresql+asyncpg://orders_user:orders_pass@localhost:5434/orders_db"
    idempotency_ttl_hours: int = 1
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
