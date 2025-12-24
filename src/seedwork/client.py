from dataclasses import dataclass
from datetime import datetime
import time
from typing import Dict, Any, List

import httpx

from .entities import Attempt, Request
from .interfaces import HttpClient
from .value_objects import APIResponse


@dataclass
class HttpxClientAdapter(HttpClient):
    """Adaptador que conecta httpx con HttpClient del seedwork."""
    client: httpx.Client

    def _safe_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}

    def _request(self, request: Request) -> APIResponse:  # type: ignore[override]
        response = self.client.request(
            request.method.value,
            request.url,
            headers=request.headers,
            json=request.json,
            params=request.params,
        )
        return APIResponse(
            status_code=response.status_code,
            content=self._safe_json(response),
        )


    def request(self, request: Request) -> List[Attempt]:
        attempts: List[Attempt] = []

        for attempt in range(request.retries):
            fetched_at = datetime.now()    
            response = self._request(request)
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
