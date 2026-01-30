from typing import Any, Awaitable, Generator, List, Optional, Protocol, Generic, Tuple, TypeVar

import httpx

from .value_objects import AccessToken, APIResponse
from .entities import Attempt, Request, Extraction


T = TypeVar("T")


class AccessTokenProvider(Generic[T], Protocol):
    async def auth(self, identifier: T) -> AccessToken: ...
    async def refresh(self, identifier: T, refresh_token: str) -> AccessToken: ...


class AccessTokenRepo(Generic[T], Protocol):
    async def get(self, identifier: T) -> Optional[AccessToken]: ...
    async def save(self, identifier: T, token: AccessToken) -> None: ...


class AuthService(Generic[T], Protocol):
    token_provider: AccessTokenProvider[T]
    token_repo: AccessTokenRepo[T]

    async def get(self, identifier: T) -> AccessToken: ...


class HttpClient(Protocol):
    client: httpx.Client | httpx.AsyncClient

    def _request(self, request: Request) -> APIResponse | Awaitable[APIResponse]: ...
    def request(self, request: Request) -> List[Attempt] | Awaitable[List[Attempt]]: ...


class Extractor(Protocol):
    client: HttpClient
    auth_service: AuthService[str]

    async def extract(self, request: Request) -> Extraction: ...


class ExtractionRepo(Protocol):
    def save(self, *args, **kwargs) -> Extraction: ...
    def save_many(self, extractions: List[Extraction]) -> List[Extraction]: ...


class Mapper(Protocol):
    @staticmethod
    def to_entity(*args, **kwargs) -> Any: ...
