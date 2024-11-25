# app/utils/debug.py
from datetime import datetime
from decimal import Decimal
from typing import Any
import json

def serialize_for_debug(obj: Any) -> Any:
    """Serialize objects for debugging"""
    # ... existing code ...
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    if isinstance(obj, (list, tuple)):
        return [serialize_for_debug(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): serialize_for_debug(v) for k, v in obj.items()}
    if hasattr(obj, '__dict__'):
        return {k: serialize_for_debug(v) 
                for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    # Handle non-serializable objects
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        return str(obj)

def debug_print(label: str = "DEBUG", obj: Any = None,) -> None:
    """Pretty print any object for debugging"""
    try:
        serialized = serialize_for_debug(obj)
        print(f"\n=== {label} ===")
        print(json.dumps(serialized, indent=2, ensure_ascii=False))
        print("=" * (len(label) + 8))
    except Exception as e:
        print(f"\n=== ERROR in debug_print: {label} ===")
        print(f"Error: {str(e)}")
        print(f"Object type: {type(obj)}")
        print("=" * (len(label) + 8))