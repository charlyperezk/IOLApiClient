from typing import Iterable, List


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