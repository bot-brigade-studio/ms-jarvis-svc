# app/utils/debug.py
from datetime import datetime
from decimal import Decimal
from typing import Any
import json

def serialize_for_debug(obj: Any) -> Any:
    """Serialize objects for debugging"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if hasattr(obj, '__dict__'):
        return {k: serialize_for_debug(v) 
                for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    return obj

def debug_print(obj: Any, label: str = "Debug") -> None:
    """Pretty print any object for debugging"""
    serialized = serialize_for_debug(obj)
    print(f"\n=== {label} ===")
    print(json.dumps(serialized, indent=2))
    print("=" * (len(label) + 8))