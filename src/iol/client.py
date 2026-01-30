from dataclasses import dataclass
from typing import Optional

from src.seedwork.entities import Extraction
from src.seedwork.interfaces import Extractor

from src.iol.enums import Country, InstrumentType
from src.iol.raw_repositories import AsyncIOLPortfolioRawRepo
from src.iol.resources import (
    MeRequest,
    PortfolioRequest,
    GetAllCotizationsRequest,
)


@dataclass
class IOLClient:
    extractor: Extractor
    portfolio_raw_repo: Optional[AsyncIOLPortfolioRawRepo] = None

    async def fetch_me(self) -> Extraction:
        return await self.extractor.extract(request=MeRequest.new())

    async def fetch_portfolio(self, country: Country = Country.ARG) -> Extraction:
        extraction = await self.extractor.extract(request=PortfolioRequest.new(country=country))
        if self.portfolio_raw_repo is not None:
            await self.portfolio_raw_repo.save(extraction, country=str(country))
        return extraction

    async def fetch_all_options(self, country: Country = Country.ARG) -> Extraction:
        return await self.extractor.extract(
            request=GetAllCotizationsRequest.new(
                country=country,
                instrument_type=InstrumentType.OPTIONS
            )
        )
