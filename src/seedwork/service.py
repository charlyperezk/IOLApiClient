from dataclasses import dataclass
from .entities import Extraction, Request
from .interfaces import ExtractionService, Extractor, ExtractionRepo


@dataclass
class StandardExtractionService(ExtractionService):
    extractor: Extractor
    extraction_repo: ExtractionRepo

    async def extract(self, identifier: str, request: Request) -> Extraction:
        extraction = self.extractor.auth_extract(identifier, request)
        self.extraction_repo.save(extraction)
        return extraction