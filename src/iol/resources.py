from src.seedwork.entities import Request
from src.seedwork.enums import RequestMethod

from src.iol.enums import Country, InstrumentType, Market
from src.iol.constants import (
    ALL_COTIZATIONS_PATH, 
    ME_PATH, 
    PORTFOLIO_PATH, 
    TICKER_COTIZATION_PATH, 
    TOKEN_PATH
)


class MeRequest(Request):
    @classmethod
    def new(cls) -> "Request":        
        return super().create(ME_PATH, method=RequestMethod.GET)


class PortfolioRequest(Request):
    @classmethod
    def new(cls, country: Country) -> "Request":
        return super().create(PORTFOLIO_PATH.format(country=country), method=RequestMethod.GET)


class AuthenticateRequest(Request):
    @classmethod
    def new(cls, username: str, password: str) -> "Request":
        body = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        return super().create(TOKEN_PATH, method=RequestMethod.POST, json=body)


class RefreshTokenRequest(Request):
    @classmethod
    def new(cls, refresh_token: str) -> "Request":
        body = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        return super().create(TOKEN_PATH, method=RequestMethod.POST, json=body)


class TickerCotizationRequest(Request):
    @classmethod
    def new(cls, symbol: str, market: Market = Market.BCBA) -> "Request":
        return super().create(
            TICKER_COTIZATION_PATH.format(market=market, symbol=symbol),
            method=RequestMethod.GET,
        )


class GetAllCotizationsRequest(Request):
    @classmethod
    def new(cls, country: Country = Country.ARG, instrument_type: InstrumentType = InstrumentType.OPTIONS) -> "Request":
        return super().create(
            ALL_COTIZATIONS_PATH.format(symbol="no-required", country=country),
            params={
                "cotizacionInstrumentoModel.instrumento": instrument_type,
                "cotizacionInstrumentoModel.pais": country
            },
            method=RequestMethod.GET,
        )