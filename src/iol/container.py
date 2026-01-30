import httpx

from src.seedwork.access_token_repo import AsyncSQLAlchemyAccessTokenRepo
from src.seedwork.auth_service import StandardAuthService
from src.seedwork.client import HttpxAsyncClientAdapter
from src.seedwork.database import get_async_engine, get_async_session_factory, init_database_async
from src.seedwork.extractor import AsyncExtractor
from src.iol.auth.provider import IOLTokenProvider
from src.iol.client import IOLClient
from src.iol.raw_repositories import AsyncIOLPortfolioRawRepo


async def build_iol_client() -> IOLClient:
    httpx_client = httpx.AsyncClient(timeout=10)
    client_adapter = HttpxAsyncClientAdapter(client=httpx_client)

    token_provider = IOLTokenProvider(client_adapter)
    async_engine = get_async_engine()
    await init_database_async(async_engine)
    session_factory = get_async_session_factory()
    token_repo = AsyncSQLAlchemyAccessTokenRepo(session_factory)
    portfolio_raw_repo = AsyncIOLPortfolioRawRepo(session_factory)
    auth_service = StandardAuthService(token_provider=token_provider, token_repo=token_repo)

    extractor = AsyncExtractor(client=client_adapter, auth_service=auth_service)
    return IOLClient(extractor=extractor, portfolio_raw_repo=portfolio_raw_repo)
