"""
Pagination utilities
pagination.py
"""

import base64
import json
from datetime import datetime
from typing import Optional, Tuple
from app.core.exceptions import ValidationError


def encode_cursor(created_at: datetime, order_id: str) -> str:
    """Encode pagination cursor from timestamp and ID."""
    cursor_data = {
        "ts": created_at.isoformat(),
        "id": order_id
    }
    cursor_json = json.dumps(cursor_data)
    cursor_bytes = cursor_json.encode('utf-8')
    return base64.b64encode(cursor_bytes).decode('utf-8')


def decode_cursor(cursor: Optional[str]) -> Optional[Tuple[datetime, str]]:
    """Decode pagination cursor to timestamp and ID."""
    if not cursor:
        return None
    
    try:
        cursor_bytes = base64.b64decode(cursor.encode('utf-8'))
        cursor_json = cursor_bytes.decode('utf-8')
        cursor_data = json.loads(cursor_json)
        
        created_at = datetime.fromisoformat(cursor_data['ts'])
        order_id = cursor_data['id']
        
        return (created_at, order_id)
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise ValidationError(f"Invalid cursor format: {str(e)}")
