from __future__ import annotations

import asyncio
from typing import Dict

import httpx
import re

from src.seedwork.settings import ENDPOINT_LOCK_NORMALIZATION_RULES


class EndpointLockRegistry:
    def __init__(self) -> None:
        self._locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    async def lock_for(self, key: str) -> asyncio.Lock:
        async with self._registry_lock:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock


def _normalize_path(path: str) -> str:
    normalized_rules = [
        (re.compile(pattern), replacement)
        for pattern, replacement in ENDPOINT_LOCK_NORMALIZATION_RULES
    ]
    for pattern, replacement in normalized_rules:
        if pattern.match(path):
            return replacement
    return path


def build_endpoint_key(url: str) -> str:
    parsed = httpx.URL(url)
    host = parsed.netloc or parsed.host or "unknown"
    path = _normalize_path(parsed.path or "/")
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}{path}"
