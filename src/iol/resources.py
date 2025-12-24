from src.seedwork.entities import Request
from src.seedwork.enums import ExtractionType, RequestMethod

from src.iol.constants import HOST, API_ROOT_V2


TOKEN_PATH = HOST + "/token"
TICKER_COTIZATION_PATH = API_ROOT_V2 + "/bCBA/Titulos/{symbol}/CotizacionDetalle"
ALL_COTIZATIONS_PATH = API_ROOT_V2 + "/Cotizaciones/{symbol}/{market}/Todos"


class AuthenticateRequest(Request):
    @classmethod
    def new(
        cls, 
        url: str = "DEFAULT API ROOT", 
        *, 
        username: str,
        password: str,
        extraction_type: ExtractionType = ExtractionType.REGULAR
    ) -> "Request":
        body = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        
        return super().create(
            TOKEN_PATH,
            method=RequestMethod.POST,
            json=body,
            extraction_type=extraction_type
        )


class RefreshTokenRequest(Request):
    @classmethod
    def new(
        cls, 
        url: str = "DEFAULT API ROOT", 
        *, 
        refresh_token: str,
        extraction_type: ExtractionType = ExtractionType.REGULAR
    ) -> "Request":
        body = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        return super().create(
            TOKEN_PATH,
            method=RequestMethod.POST,
            json=body,
            extraction_type=extraction_type
        )


class TickerCotizationRequest(Request):
    @classmethod
    def new(
        cls,
        url: str = "DEFAULT API ROOT",
        *,
        symbol: str,
        extraction_type: ExtractionType = ExtractionType.REGULAR
    ) -> "Request":
        return super().create(
            TICKER_COTIZATION_PATH.format(symbol=symbol),
            method=RequestMethod.GET,
            extraction_type=extraction_type
        )


class GetAllCotizationsRequest(Request):
    @classmethod
    def new(
        cls,
        url: str = "DEFAULT API ROOT",
        *,
        market: str = "argentina",
        instrument: str = "opciones",
        extraction_type: ExtractionType = ExtractionType.REGULAR
    ) -> "Request":
        return super().create(
            ALL_COTIZATIONS_PATH.format(symbol="no-required", market=market),
            params={
                "cotizacionInstrumentoModel.instrumento": instrument,
                "cotizacionInstrumentoModel.pais": market
            },
            method=RequestMethod.GET,
            extraction_type=extraction_type
        )
