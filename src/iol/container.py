import httpx

from src.seedwork.auth_service import StandardAuthService
from src.seedwork.client import HttpxClientAdapter
from src.seedwork.extractor import StandardExtractor
from src.seedwork.access_token_repo import SQLAlchemyAccessTokenRepo


from src.iol.auth.provider import IOLTokenProvider
from src.iol.client import IOLClient


httpx_client = httpx.Client(timeout=10)
client = HttpxClientAdapter(client=httpx_client)

token_provider = IOLTokenProvider(client)
token_repo = SQLAlchemyAccessTokenRepo()
auth_service = StandardAuthService(token_provider=token_provider, token_repo=token_repo)

extractor = StandardExtractor(client=client, auth_service=auth_service)

iol_client=IOLClient(extractor=extractor)