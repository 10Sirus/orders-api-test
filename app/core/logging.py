"""
Structured logging
logging.py
"""

import logging
import sys
from contextvars import ContextVar
from typing import Optional

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""  
    return correlation_id_var.get()

def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    correlation_id_var.set(correlation_id)

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    def filter(self, record):
        record.correlation_id = get_correlation_id() or "none"
        return True

def setup_logging() -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger().addFilter(CorrelationIdFilter())

def get_logger(name: str) -> logging.Logger:
    """Get logger instance with correlation ID support."""
    return logging.getLogger(name)
