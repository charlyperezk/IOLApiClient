from dataclasses import dataclass
from .entities import Extraction, Request
from .interfaces import ExtractionService, Extractor, ExtractionRepo


@dataclass
class StandardExtractionService(ExtractionService):
    extractor: Extractor
    extraction_repo: ExtractionRepo

    async def extract(self, request: Request) -> Extraction:
        extraction = self.extractor.extract(request)
        self.extraction_repo.save(extraction)
        return extraction