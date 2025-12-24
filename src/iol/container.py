import httpx

from src.seedwork.access_token_repo import SQLiteAccessTokenRepo
from src.seedwork.auth_service import StandardAuthService
from src.seedwork.client import HttpxClientAdapter
from src.seedwork.extractor import StandardExtractor
from src.seedwork.service import StandardExtractionService
from src.seedwork.repositories import SQLiteExtractionRepo

from src.iol.auth.account_token_provider import IOLTokenProvider
from src.iol.client import IOLClient
from src.iol.constants import IDENTIFIER


httpx_client = httpx.Client(timeout=10)
client = HttpxClientAdapter(client=httpx_client)

token_provider = IOLTokenProvider(client)
token_repo = SQLiteAccessTokenRepo()
auth_service = StandardAuthService(token_provider=token_provider, token_repo=token_repo)

extractor = StandardExtractor(client=client, auth_service=auth_service)
extraction_repo = SQLiteExtractionRepo()

service = StandardExtractionService(extractor=extractor, extraction_repo=extraction_repo)
iol_client=IOLClient(service=service, identifier=IDENTIFIER)