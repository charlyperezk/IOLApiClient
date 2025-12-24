from typing import List
from .entities import Extraction
from .interfaces import ExtractionRepo


class InMemoryExtractionRepo(ExtractionRepo):
    saved: List[Extraction]

    def __init__(self) -> None:
        self.saved = []

    def save(self, extraction: Extraction) -> Extraction:
        self.saved.append(extraction)
        return extraction