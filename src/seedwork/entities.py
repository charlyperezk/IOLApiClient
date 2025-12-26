from dataclasses import dataclass, field
from datetime import datetime
import os
from typing import Dict, Any, List, Optional

from .value_objects import APIResponse, AccessToken
from .enums import ExtractionStatus, ExtractionType, RequestMethod


@dataclass        
class Request:
    url: str
    method: RequestMethod
    identity: Optional[str] = None
    extraction_type: ExtractionType = ExtractionType.REGULAR
    retries: int = 3    
    headers: Dict[str, Any] = field(default_factory=dict)
    json: Optional[Dict[str, Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    backoff: Optional[float] = None

    @classmethod
    def create(
        cls,
        url: str,
        *,
        identity: Optional[str] = None,
        token: Optional[AccessToken] = None,
        method: RequestMethod = RequestMethod.GET,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        backoff: Optional[float] = None,
        extraction_type: ExtractionType = ExtractionType.REGULAR,
    ) -> "Request":
        headers = dict(headers) if headers else {}
        if token:
            headers.update(token.as_header())
        params = dict(params) if params else {}

        _identity = identity or os.getenv("DEFAULT_IDENTITY", None)

        return Request(
            url=url,
            identity=_identity,
            method=method,
            headers=headers,
            json=json,
            params=params,
            backoff=backoff,
            extraction_type=extraction_type
        )

    def with_authorization(self, token: AccessToken) -> "Request":
        headers = self.headers.copy()
        headers.update(token.as_header())
        
        return Request(
            url=self.url,
            identity=self.identity,
            method=self.method,
            headers=headers,
            json=self.json,
            params=self.params,
            backoff=self.backoff,
            extraction_type=self.extraction_type
        )


@dataclass(frozen=True)
class Attempt:
    fetched_at: datetime
    response: APIResponse

    @property
    def success(self) -> bool:
        return self.response.status_code == 200


@dataclass
class Extraction:
    request: Request
    status: ExtractionStatus
    attempts: List[Attempt]

    @property
    def success(self) -> bool:
        return self.status == ExtractionStatus.SUCCESS

    @property
    def retries(self) -> int:
        return len(self.attempts)

    @property
    def data(self) -> Dict[str, Any]:
        if not self.success:
            return {}
        return next((a.response.content for a in self.attempts if a.success))

    @property
    def fetched_at(self) -> datetime:
        return self.attempts[-1].fetched_at
