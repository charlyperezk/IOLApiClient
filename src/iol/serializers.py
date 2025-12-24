from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Union


def to_json_safe(value: Any) -> Any:
    """Recursively convert objects to json-serializable primitives."""

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {key: to_json_safe(val) for key, val in value.items()}

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [to_json_safe(item) for item in value]

    return value
