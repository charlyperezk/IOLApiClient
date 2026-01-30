import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import List

from .entities import Attempt, Extraction, Request
from .enums import ExtractionStatus
from .interfaces import Extractor, AuthService, HttpClient
from .logging import get_logger
from .value_objects import APIResponse

from src.seedwork.exceptions import EmptyTokenResponse

logger = get_logger(__name__)


@dataclass
class StandardExtractor(Extractor):
    client: HttpClient
    auth_service: AuthService[str]

    async def extract(self, request: Request) -> Extraction:
        if request.identity:
            try:
                token = await self.auth_service.get(request.identity)
            except EmptyTokenResponse as exc:
                logger.warning("Token refresh failed while authorizing %s: %s", request.identity, exc)
                failure_attempt = Attempt(
                    fetched_at=datetime.now(),
                    response=APIResponse(status_code=422, content={"error": str(exc)}),
                )
                return Extraction(request=request, attempts=[failure_attempt], status=ExtractionStatus.ERROR)
            request = request.with_authorization(token)

        if request.rate_limit_delay:
            await asyncio.sleep(request.rate_limit_delay)

        attempts = await asyncio.to_thread(self.client.request, request)
        status = ExtractionStatus.SUCCESS if any(attempt.success for attempt in attempts) else ExtractionStatus.ERROR
        return Extraction(
            request=request,
            attempts=attempts,
            status=status,
        )


@dataclass
class AsyncExtractor(Extractor):
    client: HttpClient
    auth_service: AuthService[str]

    async def extract(self, request: Request) -> Extraction:
        if request.identity:
            try:
                token = await self.auth_service.get(request.identity)
            except EmptyTokenResponse as exc:
                logger.warning("Token refresh failed while authorizing %s: %s", request.identity, exc)
                failure_attempt = Attempt(
                    fetched_at=datetime.now(),
                    response=APIResponse(status_code=422, content={"error": str(exc)}),
                )
                return Extraction(request=request, attempts=[failure_attempt], status=ExtractionStatus.ERROR)
            request = request.with_authorization(token)

        # Apply optional rate limiting delay before executing request
        if request.rate_limit_delay:
            await asyncio.sleep(request.rate_limit_delay)

        # Check if client has async request method
        if hasattr(self.client, 'request') and asyncio.iscoroutinefunction(self.client.request):
            attempts = await self.client.request(request)
        else:
            # Fallback to thread pool for sync clients
            attempts = await asyncio.to_thread(self.client.request, request)
        
        status = ExtractionStatus.SUCCESS if any(attempt.success for attempt in attempts) else ExtractionStatus.ERROR
        return Extraction(
            request=request,
            attempts=attempts,
            status=status,
        )
