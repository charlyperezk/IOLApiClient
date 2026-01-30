import asyncio
import json
from datetime import datetime
from typing import Callable, Optional

import redis.asyncio as aioredis
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session

from .database import Base
from .interfaces import AccessTokenRepo
from .logging import get_logger
from .value_objects import AccessToken


class AccessTokenModel(Base):
    __tablename__ = "access_tokens"

    identifier = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    life_time = Column(Integer, nullable=False)
    obtained_at = Column(DateTime, nullable=False)


class SQLAlchemyAccessTokenRepo(AccessTokenRepo[str]):
    """SQLAlchemy-backed repository for caching access tokens per identifier."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    async def get(self, identifier: str) -> Optional[AccessToken]:
        return await asyncio.to_thread(self._get_sync, identifier)

    async def save(self, identifier: str, token: AccessToken) -> None:
        await asyncio.to_thread(self._save_sync, identifier, token)

    def _get_sync(self, identifier: str) -> Optional[AccessToken]:
        with self._session_factory() as session:
            token_model = session.get(AccessTokenModel, identifier)
            if token_model is None:
                return None
            return AccessToken(
                life_time=token_model.life_time,
                value=token_model.value,
                refresh_token=token_model.refresh_token,
                obtained_at=token_model.obtained_at,
            )

    def _save_sync(self, identifier: str, token: AccessToken) -> None:
        with self._session_factory() as session:
            model = AccessTokenModel(
                identifier=identifier,
                value=token.value,
                refresh_token=token.refresh_token,
                life_time=token.life_time,
                obtained_at=token.obtained_at,
            )
            session.merge(model)
            session.commit()


class AsyncSQLAlchemyAccessTokenRepo(AccessTokenRepo[str]):
    """Async SQLAlchemy-backed repository for caching access tokens per identifier."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, identifier: str) -> Optional[AccessToken]:
        async with self._session_factory() as session:
            token_model = await session.get(AccessTokenModel, identifier)
            if token_model is None:
                return None
            return AccessToken(
                life_time=token_model.life_time,
                value=token_model.value,
                refresh_token=token_model.refresh_token,
                obtained_at=token_model.obtained_at,
            )

    async def save(self, identifier: str, token: AccessToken) -> None:
        async with self._session_factory() as session:
            model = AccessTokenModel(
                identifier=identifier,
                value=token.value,
                refresh_token=token.refresh_token,
                life_time=token.life_time,
                obtained_at=token.obtained_at,
            )
            await session.merge(model)
            await session.commit()


class RedisBackedAccessTokenRepo(AccessTokenRepo[str]):
    """Access token repository that caches reads and writes in Redis."""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        fallback_repo: AccessTokenRepo[str],
        key_prefix: str = "access_token",
    ) -> None:
        self._redis = redis_client
        self._fallback = fallback_repo
        self._key_prefix = key_prefix
        self._logger = get_logger(__name__)

    async def get(self, identifier: str) -> Optional[AccessToken]:
        cached = await self._get_from_cache(identifier)
        if cached:
            return cached

        token = await self._fallback.get(identifier)
        if token:
            await self._cache_token(identifier, token)
        return token

    async def save(self, identifier: str, token: AccessToken) -> None:
        await self._fallback.save(identifier, token)
        await self._cache_token(identifier, token)

    def _cache_key(self, identifier: str) -> str:
        return f"{self._key_prefix}:{identifier}"

    async def _cache_token(self, identifier: str, token: AccessToken) -> None:
        payload = self._serialize_token(token)
        expires = max(token.life_time, 1) if token.life_time > 0 else None
        try:
            await self._redis.set(self._cache_key(identifier), payload, ex=expires)
        except aioredis.RedisError as exc:
            self._logger.warning("Unable to cache token for %s: %s", identifier, exc)

    async def _get_from_cache(self, identifier: str) -> Optional[AccessToken]:
        try:
            raw = await self._redis.get(self._cache_key(identifier))
        except aioredis.RedisError as exc:
            self._logger.warning("Unable to read cache for %s: %s", identifier, exc)
            return None

        if not raw:
            return None

        try:
            return self._deserialize_token(raw)
        except (ValueError, KeyError) as exc:
            self._logger.warning("Corrupted token cached for %s: %s", identifier, exc)
            try:
                await self._redis.delete(self._cache_key(identifier))
            except aioredis.RedisError:
                pass
            return None

    def _serialize_token(self, token: AccessToken) -> str:
        return json.dumps(
            {
                "value": token.value,
                "refresh_token": token.refresh_token,
                "life_time": token.life_time,
                "obtained_at": token.obtained_at.isoformat(),
            }
        )

    def _deserialize_token(self, raw: bytes | str) -> AccessToken:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        data = json.loads(raw)
        obtained_at = datetime.fromisoformat(data["obtained_at"])
        return AccessToken(
            life_time=int(data["life_time"]),
            value=data["value"],
            refresh_token=data["refresh_token"],
            obtained_at=obtained_at,
        )
