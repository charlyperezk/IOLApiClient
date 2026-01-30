from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from .entities import Request, Snapshot


def chunked(items: Iterable[str], size: int) -> Iterable[List[str]]:
    """Genera listas de hasta `size` ids por llamada."""
    batch: List[str] = []
    for item_id in items:
        if not item_id:
            continue
        batch.append(item_id)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def split_date_range(start: date, end: date, max_span_days: int) -> Iterator[Tuple[date, date]]:
    """Divide un rango [start, end] en sub-rangos de hasta max_span_days."""
    if max_span_days <= 0:
        raise ValueError("max_span_days debe ser mayor que 0")

    current = start
    while current <= end:
        span_end = min(end, current + timedelta(days=max_span_days - 1))
        yield current, span_end
        current = span_end + timedelta(days=1)


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_paging(data: Any, path: str) -> Optional[Dict[str, Any]]:
    if not path or not isinstance(data, dict):
        return None
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return dict(current) if isinstance(current, dict) else None


def _resolve_current_offset(request: "Request", paging: Dict[str, Any]) -> int:
    offset = _coerce_int(paging.get("offset"))
    if offset is not None:
        return offset
    fallback = _coerce_int(request.params.get("offset"))
    return fallback if fallback is not None else 0


def _apply_paging(request: "Request", paging: Dict[str, Any]) -> Optional["Request"]:
    limit = _coerce_int(paging.get("limit"))
    if limit is None:
        limit = _coerce_int(request.params.get("limit"))

    current_offset = _resolve_current_offset(request, paging)
    next_offset = _coerce_int(paging.get("next_offset"))

    if next_offset is None:
        if limit is None:
            return None
        next_offset = current_offset + limit

    total = _coerce_int(paging.get("total"))
    if total is not None and current_offset >= total:
        return None

    if total is not None and next_offset >= total:
        return None

    params = dict(request.params)
    if limit is not None:
        params["limit"] = limit
    params["offset"] = next_offset

    return replace(request, params=params)