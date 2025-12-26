from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from src.seedwork.interfaces import AccessTokenProvider, AccessToken, HttpClient
from src.seedwork.value_objects import APIResponse

from src.iol.constants import ACCESS_TOKEN_DEFAULT_LIFETIME
from src.iol.auth.accounts import ACCOUNTS, PASSWORDS
from src.iol.resources import AuthenticateRequest, RefreshTokenRequest


@dataclass
class IOLTokenProvider(AccessTokenProvider[str]):
    _client: HttpClient

    def _get_credentials(self, identifier: str) -> Tuple[str, str]:
        username = ACCOUNTS.get(identifier, None)
        password = PASSWORDS.get(identifier, None)

        if not username or not password:
            raise ValueError("Account not found")

        return username, password

    def _build_token_from_response(self, response: APIResponse) -> AccessToken:
        if not response.sucess:
            raise RuntimeError(f"Refresh request failed with status {response.status_code}")

        access_token = response.content.get("access_token")
        refresh_token = response.content.get("refresh_token")

        if not access_token or not refresh_token:
            raise RuntimeError("Can't extract access_token or refresh_token from response")

        return AccessToken(
            life_time=ACCESS_TOKEN_DEFAULT_LIFETIME,
            value=access_token,
            refresh_token=refresh_token,
            obtained_at=datetime.now()
        )

    def auth(self, identifier: str) -> AccessToken:
        username, password = self._get_credentials(identifier)
        auth_request = AuthenticateRequest.new(username=username, password=password)
        response = self._client._request(auth_request)
        return self._build_token_from_response(response)

    def refresh(self, identifier: str, refresh_token: str) -> AccessToken:
        refresh_request = RefreshTokenRequest.new(refresh_token=refresh_token)
        response = self._client._request(refresh_request)
        return self._build_token_from_response(response)