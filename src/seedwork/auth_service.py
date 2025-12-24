from dataclasses import dataclass
from typing import Optional, TypeVar

from .interfaces import AccessTokenProvider, AccessTokenRepo, AuthService
from .value_objects import AccessToken


T = TypeVar("T")


@dataclass
class StandardAuthService(AuthService[T]):
    """AuthService that caches tokens in a repository and refreshes when needed."""

    token_provider: AccessTokenProvider[T]
    token_repo: AccessTokenRepo[T]

    def get(self, identifier: T) -> AccessToken:
        cached = self.token_repo.get(identifier)
        if cached and not cached.is_expired:
            return cached

        token: Optional[AccessToken] = None
        if cached and cached.refresh_token:
            try:
                token = self.token_provider.refresh(identifier, cached.refresh_token)
            except Exception:
                token = None

        if token is None:
            token = self.token_provider.auth(identifier)

        self.token_repo.save(identifier, token)
        return token
