from typing import Iterable, List
from .entities import Extraction


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


def _build_fingerprint(seller_id: str, item_id: str, run: Extraction) -> str:
    return f"seedwork_v2:items:{seller_id}:{item_id}:{run.fetched_at}"
