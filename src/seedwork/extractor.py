from dataclasses import dataclass
from typing import List

from .entities import Attempt, Extraction, Request
from .enums import ExtractionStatus
from .interfaces import Extractor, AuthService, HttpClient


@dataclass
class StandardExtractor(Extractor):
    client: HttpClient
    auth_service: AuthService[str]

    def extract(self, request: Request) -> Extraction:
        if request.identity:
            token = self.auth_service.get(request.identity)
            request = request.with_authorization(token)

        attempts = self.client.request(request=request)
        status = ExtractionStatus.SUCCESS if any(attempt.success for attempt in attempts) else ExtractionStatus.ERROR
        return Extraction(
            request=request,
            attempts=attempts,
            status=status,
        )