import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.seedwork.interfaces import ExtractionService

from iol.entities import Option, TickerCotization
from iol.resources import (
    TickerCotizationRequest,
    GetAllCotizationsRequest,
)


@dataclass
class IOLClient:
    service: ExtractionService
    identifier: str

    async def _fetch_all_options(self, market: str = "argentina") -> List[Option]:
        extraction = await self.service.extract(
            identifier=self.identifier,
            request=GetAllCotizationsRequest.new(market=market),
        )
        
        cotizations = extraction.data.get("cotizacion") or []
        return [Option.from_payload(option) for option in cotizations]
