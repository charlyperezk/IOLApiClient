import httpx

from src.seedwork.access_token_repo import SQLiteAccessTokenRepo
from src.seedwork.auth_service import StandardAuthService
from src.seedwork.client import HttpxClientAdapter
from src.seedwork.extractor import StandardExtractor
from src.seedwork.service import StandardExtractionService
from src.seedwork.strategies.scroll import GeneratedScrolledExtraction, ScrollRequestBuilder
from src.seedwork.strategies.paging import GeneratedPagingExtraction, PagingRequestBuilder
from src.seedwork.repositories import InMemoryExtractionRepo

from src.iol.auth.account_token_provider import IOLTokenProvider
from src.iol.client import IOLClient
from src.iol.constants import IDENTIFIER


httpx_client = httpx.Client(timeout=10)
client = HttpxClientAdapter(client=httpx_client)

token_provider = IOLTokenProvider(client)
token_repo = SQLiteAccessTokenRepo()
auth_service = StandardAuthService(token_provider=token_provider, token_repo=token_repo)

extractor = StandardExtractor(client=client, auth_service=auth_service)
extraction_repo = InMemoryExtractionRepo()

service = StandardExtractionService(extractor=extractor, extraction_repo=extraction_repo)

scroll_req_builder = ScrollRequestBuilder()
scroller = GeneratedScrolledExtraction(req_builder=scroll_req_builder)

paging_req_builder = PagingRequestBuilder()
paginator = GeneratedPagingExtraction(req_builder=paging_req_builder)

iol_client=IOLClient(service=service, identifier=IDENTIFIER)