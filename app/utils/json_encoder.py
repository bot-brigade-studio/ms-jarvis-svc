from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

def serialize_object(obj: Any) -> Any:
    """Custom serializer for objects that aren't JSON serializable by default"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if hasattr(obj, 'model_dump'):  # For Pydantic models
        return obj.model_dump()
    if hasattr(obj, '__dict__'):  # For SQLAlchemy models
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return str(obj)