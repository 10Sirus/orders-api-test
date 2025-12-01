"""
Idempotency utilities
idempotency.py
"""

import hashlib
import json


def hash_body(body: dict) -> str:
    """Create SHA-256 hash of request body."""
    body_json = json.dumps(body, sort_keys=True)
    return hashlib.sha256(body_json.encode()).hexdigest()


def bodies_match(body1_hash: str, body2: dict) -> bool:
    """Check if body hash matches the given body."""
    return body1_hash == hash_body(body2)
