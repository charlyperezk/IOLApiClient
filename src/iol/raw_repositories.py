from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.iol.entities import IOLPortfolioRawSnapshot
from src.seedwork.entities import Extraction


class AsyncIOLPortfolioRawRepo:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, extraction: Extraction, *, country: Optional[str] = None) -> None:
        last_attempt = extraction.attempts[-1]
        model = IOLPortfolioRawSnapshot(
            identity=extraction.request.identity,
            country=country,
            status_code=last_attempt.response.status_code,
            fetched_at=last_attempt.fetched_at,
            payload=last_attempt.response.content,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
