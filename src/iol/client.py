from dataclasses import dataclass
from typing import List

from src.seedwork.interfaces import ExtractionService

from src.iol.enums import Country
from src.iol.entities import Option
from src.iol.resources import (
    MeRequest,
    PortfolioRequest,
    GetAllCotizationsRequest,
)


@dataclass
class IOLClient:
    service: ExtractionService
    identifier: str

    async def fetch_me(self) -> ...:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=MeRequest.new(),
        )
        return extraction

    async def fetch_portfolio(self, country: Country = Country.ARG) -> ...:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=PortfolioRequest.new(country=country),
        )
        return extraction

    async def fetch_all_options(self, country: Country = Country.ARG) -> List[Option]:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=GetAllCotizationsRequest.new(country=country),
        )
        
        cotizations = extraction.data.get("cotizacion") or []
        return [Option.from_payload(option) for option in cotizations]