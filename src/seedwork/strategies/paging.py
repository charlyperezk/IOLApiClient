from dataclasses import dataclass, replace
from typing import Any, AsyncGenerator, Dict, Optional

from ..entities import Extraction, Request
from ..interfaces import ExtractionService, RequestBuilder


DEFAULT_PAGING_INDEX = "paging"


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


class PagingRequestBuilder(RequestBuilder):
    """Generaliza la lógica de iterar scroll/venedor con cualquier RequestGenerator."""
    def build(
        self,
        last_extraction: Extraction,
        paging_index: str = DEFAULT_PAGING_INDEX,
    ) -> Optional[Request]:
        if not last_extraction.success:
            return

        paging = _read_paging(last_extraction.data, paging_index)
        if not paging:
            return

        return _apply_paging(last_extraction.request, paging)


@dataclass
class GeneratedPagingExtraction:
    req_builder: RequestBuilder

    async def paginate(
        self,
        service: ExtractionService,
        seller_id: str,
        request: Request,
        paging_index: str,
    ) -> AsyncGenerator[Extraction, None]:
        current_run = await service.extract(seller_id, request)
        yield current_run

        while True:
            next_request = self.req_builder.build(
                last_extraction=current_run,
                paging_index=paging_index,
            )
            if not next_request:
                break

            current_run = await service.extract(seller_id, next_request)
            yield current_run
