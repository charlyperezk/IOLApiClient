from dataclasses import dataclass
from typing import List

from src.seedwork.interfaces import ExtractionService

from src.iol.enums import Country, InstrumentType
from src.iol.entities import Account, Option, Portfolio
from src.iol.resources import (
    MeRequest,
    PortfolioRequest,
    GetAllCotizationsRequest,
)


@dataclass
class IOLClient:
    service: ExtractionService
    identifier: str

    async def fetch_me(self) -> Account:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=MeRequest.new(),
        )
        return Account.from_payload(extraction.data)

    async def fetch_portfolio(self, country: Country = Country.ARG) -> ...:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=PortfolioRequest.new(country=country),
        )
        return Portfolio.from_payload(extraction.data)

    async def fetch_all_options(self, country: Country = Country.ARG) -> List[Option]:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=GetAllCotizationsRequest.new(country=country, instrument_type=InstrumentType.OPTIONS),
        )
        cotizations = extraction.data.get("titulos") or []
        return [Option.from_payload(option) for option in cotizations]