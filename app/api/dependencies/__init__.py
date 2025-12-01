"""API dependencies exports."""

from app.api.dependencies.tenant import get_tenant_id
from app.api.dependencies.idempotency import get_idempotency_key
from app.api.dependencies.optimistic_lock import get_if_match

__all__ = ["get_tenant_id", "get_idempotency_key", "get_if_match"]
