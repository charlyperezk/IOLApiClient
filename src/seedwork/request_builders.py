from dataclasses import dataclass, replace
from typing import Any, Dict, Optional

from .entities import Extraction, Request
from .interfaces import RequestBuilder


DEFAULT_PAGING_INDEX = "paging"
DEFAULT_SCROLL_ID_INDEX = "scroll_id"


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


def _resolve_current_offset(request: Request, paging: Dict[str, Any]) -> int:
    """Obtiene el offset actual, preferando el valor devuelto en el payload."""
    offset = _coerce_int(paging.get("offset"))
    if offset is not None:
        return offset
    fallback = _coerce_int(request.params.get("offset"))
    return fallback if fallback is not None else 0


def _apply_paging(request: Request, paging: Dict[str, Any]) -> Optional[Request]:
    """Ajusta los params `limit`/`offset` para avanzar a la siguiente página."""
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

    new_request = replace(request, params=params)
    return new_request


@dataclass
class PagingRequestBuilder(RequestBuilder):
    """Generaliza la lógica de iterar scroll/venedor con cualquier RequestGenerator."""
    paging_index: str = DEFAULT_PAGING_INDEX

    def build(
        self,
        last_extraction: Extraction,
    ) -> Optional[Request]:
        if not last_extraction.success:
            return

        paging = _read_paging(last_extraction.data, self.paging_index)
        if not paging:
            return

        return _apply_paging(last_extraction.request, paging)


def _apply_scroll_token(request: Request, key: str, token: str) -> Request:
    """Incluye el token de scroll en los params y en el JSON del request."""
    params = {**request.params, key: token}
    return replace(request, params=params)


def _read_scroll_token(data: Any, path: str) -> Optional[str]:
    if not path or not isinstance(data, dict):
        return None
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return str(current) if current is not None else None


@dataclass
class ScrollRequestBuilder(RequestBuilder):
    """Generaliza la lógica de iterar scroll/venedor con cualquier RequestGenerator."""
    scroll_id_index: str = DEFAULT_SCROLL_ID_INDEX
    
    
    def build(
        self,
        last_extraction: Extraction
    ) -> Optional[Request]:
        if not last_extraction.success:
            return

        scroll_token = _read_scroll_token(last_extraction.data, self.scroll_id_index)
        if not scroll_token:
            return

        return _apply_scroll_token(
            last_extraction.request, self.scroll_id_index, scroll_token
        )