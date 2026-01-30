from dataclasses import dataclass
from datetime import datetime
import time
import asyncio
from typing import Dict, Any, List, Optional

import httpx

from .entities import Attempt, Request
from .endpoint_lock_registry import EndpointLockRegistry, build_endpoint_key
from .interfaces import HttpClient
from .logging import get_logger
from .value_objects import APIResponse


logger = get_logger(__name__)


@dataclass
class HttpxClientAdapter(HttpClient):
    """Adaptador que conecta httpx con HttpClient del seedwork."""
    client: httpx.Client
    endpoint_lock_registry: EndpointLockRegistry | None = None

    def _safe_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}

    def _request(self, request: Request) -> APIResponse:  # type: ignore[override]
        request_kwargs = {
            "method": request.method.value,
            "url": request.url,
            "headers": request.headers,
            "json": request.json,
            "params": request.params,
        }
        if request.timeout is not None:
            request_kwargs["timeout"] = request.timeout
        response = self.client.request(**request_kwargs)
        return APIResponse(
            status_code=response.status_code,
            content=self._safe_json(response),
        )

    def request(self, request: Request) -> List[Attempt]:
        attempts: List[Attempt] = []

        for attempt in range(request.retries):
            attempt_number = attempt + 1
            logger.debug(
                "Starting HTTP request to %s attempt %d/%d",
                request.url,
                attempt_number,
                request.retries,
            )
            start = time.perf_counter()
            fetched_at = datetime.now()
            response = self._request(request)
            duration = time.perf_counter() - start
            logger.debug(
                "Finished HTTP request to %s attempt %d/%d status=%s duration=%.3f",
                request.url,
                attempt_number,
                request.retries,
                response.status_code,
                duration,
            )
            attempt = Attempt(
                fetched_at=fetched_at,
                response=response,
            )
            attempts.append(attempt)

            if attempt.success:
                break

            backoff = request.backoff
            if backoff:
                time.sleep(backoff)

        return attempts


@dataclass
class HttpxAsyncClientAdapter(HttpClient):
    """Async adapter that connects httpx.AsyncClient with HttpClient interface."""
    client: httpx.AsyncClient
    endpoint_lock_registry: EndpointLockRegistry | None = None

    def _safe_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}

    async def _request(self, request: Request) -> APIResponse:  # type: ignore[override]
        try:
            request_kwargs = {
                "method": request.method.value,
                "url": request.url,
                "headers": request.headers,
                "json": request.json,
                "params": request.params,
            }
            if request.timeout is not None:
                request_kwargs["timeout"] = request.timeout

            if self.endpoint_lock_registry:
                endpoint_key = build_endpoint_key(str(request.url))
                lock = await self.endpoint_lock_registry.lock_for(endpoint_key)
                waiting = lock.locked()
                if waiting:
                    logger.info("Waiting for lock on endpoint %s", endpoint_key)
                async with lock:
                    if waiting:
                        logger.info("Acquired lock on endpoint %s", endpoint_key)
                    response = await self.client.request(**request_kwargs)
            else:
                response = await self.client.request(**request_kwargs)

            return APIResponse(
                status_code=response.status_code,
                content=self._safe_json(response),
            )
        except httpx.TimeoutException as e:
            logger.warning(f"Request timeout for {request.url}: {e}")
            return APIResponse(
                status_code=408,  # Request Timeout
                content={"error": "Request timeout", "detail": str(e)},
            )
        except httpx.ConnectError as e:
            logger.warning(f"Connection error for {request.url}: {e}")
            return APIResponse(
                status_code=503,  # Service Unavailable
                content={"error": "Connection error", "detail": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error for {request.url}: {e}")
            return APIResponse(
                status_code=500,  # Internal Server Error
                content={"error": "Unexpected error", "detail": str(e)},
            )

    async def request(self, request: Request) -> List[Attempt]:
        attempts: List[Attempt] = []

        for attempt_index in range(request.retries):
            attempt_number = attempt_index + 1
            logger.debug(
                "Starting async HTTP request to %s attempt %d/%d",
                request.url,
                attempt_number,
                request.retries,
            )
            start = time.perf_counter()
            fetched_at = datetime.now()
            response = await self._request(request)
            duration = time.perf_counter() - start
            logger.debug(
                "Finished async HTTP request to %s attempt %d/%d status=%s duration=%.3f",
                request.url,
                attempt_number,
                request.retries,
                response.status_code,
                duration,
            )
            attempt = Attempt(
                fetched_at=fetched_at,
                response=response,
            )
            attempts.append(attempt)

            if attempt.success:
                break

            # Exponential backoff with jitter for better retry behavior
            if attempt_index < request.retries - 1:  # Don't sleep on last attempt
                base_backoff = request.backoff or 1.0
                exponential_backoff = base_backoff * (2 ** attempt_index)
                # Add jitter to prevent thundering herd
                jitter = 0.1 * exponential_backoff
                import random
                final_backoff = exponential_backoff + random.uniform(-jitter, jitter)
                final_backoff = max(0.1, min(final_backoff, 30.0))  # Clamp between 0.1s and 30s
                
                logger.debug(f"Retrying in {final_backoff:.2f}s (attempt {attempt_number + 1})")
                await asyncio.sleep(final_backoff)

        return attempts


@dataclass
class EnhancedAsyncClientAdapter(HttpClient):
    """Enhanced async client with circuit breaker and improved error handling."""
    client: httpx.AsyncClient
    circuit_breaker: Optional[Any] = None  # CircuitBreaker instance

    def _safe_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}

    async def _request(self, request: Request) -> APIResponse:  # type: ignore[override]
        try:
            request_kwargs = {
                "method": request.method.value,
                "url": request.url,
                "headers": request.headers,
                "json": request.json,
                "params": request.params,
            }
            if request.timeout is not None:
                request_kwargs["timeout"] = request.timeout
            response = await self.client.request(**request_kwargs)
            return APIResponse(
                status_code=response.status_code,
                content=self._safe_json(response),
            )
        except httpx.TimeoutException as e:
            logger.warning(f"Request timeout for {request.url}: {e}")
            return APIResponse(
                status_code=408,  # Request Timeout
                content={"error": "Request timeout", "detail": str(e)},
            )
        except httpx.ConnectError as e:
            logger.warning(f"Connection error for {request.url}: {e}")
            return APIResponse(
                status_code=503,  # Service Unavailable
                content={"error": "Connection error", "detail": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error for {request.url}: {e}")
            return APIResponse(
                status_code=500,  # Internal Server Error
                content={"error": "Unexpected error", "detail": str(e)},
            )

    async def request(self, request: Request) -> List[Attempt]:
        if self.circuit_breaker:
            # Use circuit breaker if configured
            breaker_func = self.circuit_breaker(self._make_request_with_retries)
            return await breaker_func(request)
        else:
            return await self._make_request_with_retries(request)

    async def _make_request_with_retries(self, request: Request) -> List[Attempt]:
        """Make request with retry logic and exponential backoff."""
        attempts: List[Attempt] = []

        for attempt_index in range(request.retries):
            attempt_number = attempt_index + 1
            logger.debug(
                "Starting enhanced async HTTP request to %s attempt %d/%d",
                request.url,
                attempt_number,
                request.retries,
            )
            start = time.perf_counter()
            fetched_at = datetime.now()
            response = await self._request(request)
            duration = time.perf_counter() - start
            logger.debug(
                "Finished enhanced async HTTP request to %s attempt %d/%d status=%s duration=%.3f",
                request.url,
                attempt_number,
                request.retries,
                response.status_code,
                duration,
            )
            attempt = Attempt(
                fetched_at=fetched_at,
                response=response,
            )
            attempts.append(attempt)

            if attempt.success:
                break

            # Exponential backoff with jitter for better retry behavior
            if attempt_index < request.retries - 1:  # Don't sleep on last attempt
                base_backoff = request.backoff or 1.0
                exponential_backoff = base_backoff * (2 ** attempt_index)
                # Add jitter to prevent thundering herd
                jitter = 0.1 * exponential_backoff
                import random
                final_backoff = exponential_backoff + random.uniform(-jitter, jitter)
                final_backoff = max(0.1, min(final_backoff, 30.0))  # Clamp between 0.1s and 30s
                
                logger.debug(f"Retrying in {final_backoff:.2f}s (attempt {attempt_number + 1})")
                await asyncio.sleep(final_backoff)

        return attempts
