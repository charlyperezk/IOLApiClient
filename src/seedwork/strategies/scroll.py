from dataclasses import dataclass, replace
from typing import Any, AsyncGenerator, List, Optional

from ..entities import Extraction, Request
from ..interfaces import ExtractionService, RequestBuilder


DEFAULT_SCROLL_ID_INDEX = "scroll_id"


def _apply_scroll_token(request: Request, key: str, token: str) -> Request:
    """Incluye el token de scroll en los params y en el JSON del request."""
    headers = {**request.headers, key: token}
    return replace(request, headers=headers)


def _read_scroll_token(data: Any, path: str) -> Optional[str]:
    if not path or not isinstance(data, dict):
        return None
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return str(current) if current is not None else None


class ScrollRequestBuilder(RequestBuilder):
    """Generaliza la lógica de iterar scroll/venedor con cualquier RequestGenerator."""
    def build(
        self,
        last_extraction: Extraction,
        scroll_id_index: str = DEFAULT_SCROLL_ID_INDEX,
    ) -> Optional[Request]:
        if not last_extraction.success:
            return

        scroll_token = _read_scroll_token(last_extraction.data, scroll_id_index)
        if not scroll_token:
            return

        return _apply_scroll_token(
            last_extraction.request, scroll_id_index, scroll_token
        )


@dataclass
class GeneratedScrolledExtraction:
    req_builder: RequestBuilder

    async def scroll(
        self,
        service: ExtractionService,
        seller_id: str,
        request: Request,
        scroll_id_index: str,
    ) -> AsyncGenerator[Extraction, None]:
        current_run = await service.extract(seller_id, request)
        yield current_run

        while True:
            next_request = self.req_builder.build(
                last_extraction=current_run,
                scroll_id_index=scroll_id_index,
            )
            if not next_request:
                break

            current_run = await service.extract(seller_id, next_request)
            yield current_run
