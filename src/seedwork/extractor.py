from dataclasses import dataclass

from .entities import Extraction, Request
from .enums import ExtractionStatus
from .interfaces import Extractor, AuthService, HttpClient


@dataclass
class StandardExtractor(Extractor):
    client: HttpClient
    auth_service: AuthService[str]

    def auth_extract(self, seller_id: str, request: Request) -> Extraction:
        return self.extract(request=self._apply_request_auth(seller_id, request))

    def _apply_request_auth(self, seller_id: str, request: Request) -> Request:
        token = self.auth_service.get(seller_id)
        return request.with_authorization(token)

    def extract(self, request: Request) -> Extraction:
        attempts = self.client.request(request=request)
        status = ExtractionStatus.SUCCESS if any(attempt.success for attempt in attempts) else ExtractionStatus.ERROR
        return Extraction(
            request=request,
            attempts=attempts,
            status=status,
        )
