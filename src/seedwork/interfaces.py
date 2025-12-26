from typing import Generator, List, Optional, Protocol, Generic, TypeVar

import httpx

from .value_objects import AccessToken, APIResponse
from .entities import Attempt, Request, Extraction


T = TypeVar("T")


class AccessTokenProvider(Generic[T], Protocol):
    def auth(self, identifier: T) -> AccessToken: ...
    def refresh(self, identifier: T, refresh_token: str) -> AccessToken: ...


class AccessTokenRepo(Generic[T], Protocol):
    def get(self, identifier: T) -> Optional[AccessToken]: ...
    def save(self, identifier: T, token: AccessToken) -> None: ...


class AuthService(Generic[T], Protocol):
    token_provider: AccessTokenProvider[T]
    token_repo: AccessTokenRepo[T]

    def get(self, identifier: T) -> AccessToken: ...


class HttpClient(Protocol):
    client: httpx.Client

    def _request(self, request: Request) -> APIResponse: ...
    def request(self, request: Request) -> List[Attempt]: ...


class Extractor(Protocol):
    client: HttpClient
    auth_service: AuthService[str]

    def extract(self, request: Request) -> Extraction: ...


class ExtractionRepo(Protocol):
    def save(self, *args, **kwargs) -> Extraction: ...


class ExtractionService(Protocol):
    extractor: Extractor
    extraction_repo: ExtractionRepo

    async def extract(self, *args, **kwargs) -> Extraction: ...


class RequestBuilder(Protocol):
    def build(self, *args, **kwargs) -> Optional[Request]: ...


class RunGenerator(Protocol):
    req_builder: RequestBuilder
    extractor: Extractor

    def generate(self, *args, **kwargs) -> Generator[Extraction, None, None]: ...
