from dataclasses import dataclass
from typing import Optional, TypeVar

from .interfaces import AccessTokenProvider, AccessTokenRepo, AuthService
from .logging import get_logger
from .value_objects import AccessToken


T = TypeVar("T")

logger = get_logger(__name__)


@dataclass
class StandardAuthService(AuthService[T]):
    """AuthService that caches tokens in a repository and refreshes when needed."""

    token_provider: AccessTokenProvider[T]
    token_repo: AccessTokenRepo[T]

    async def get(self, identifier: T) -> AccessToken:
        cached = await self.token_repo.get(identifier)
        if cached and not cached.is_expired:
            logger.debug("Returning cached token for %s", identifier)
            return cached

        token: Optional[AccessToken] = None
        if cached and cached.refresh_token:
            try:
                refreshed = await self.token_provider.refresh(identifier, cached.refresh_token)
                token = refreshed
            except Exception as exc:
                logger.warning("Token refresh failed for %s: %s", identifier, exc)

        if token is None:
            logger.debug("Requesting new token for %s", identifier)
            token = await self.token_provider.auth(identifier)

        await self.token_repo.save(identifier, token)
        return token
