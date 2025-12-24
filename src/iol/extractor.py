from dataclasses import dataclass

from src.seedwork.entities import Extraction, Request
from src.seedwork.enums import ExtractionStatus
from src.seedwork.interfaces import Extractor, AuthService, HttpClient


@dataclass
class IOLExtractor(Extractor):
    client: HttpClient
    auth_service: AuthService[str]

    def auth_extract(self, identifier: str, request: Request) -> Extraction:
        return self.extract(request=self._apply_request_auth(identifier, request))

    def _apply_request_auth(self, identifier: str, request: Request) -> Request:
        token = self.auth_service.get(identifier)
        return request.with_authorization(token)

    def extract(self, request: Request) -> Extraction:
        attempts = self.client.request(request=request)
        status = ExtractionStatus.SUCCESS if any(attempt.success for attempt in attempts) else ExtractionStatus.ERROR
        return Extraction(
            request=request,
            attempts=attempts,
            status=status,
        )
