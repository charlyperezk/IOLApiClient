import re
from typing import Iterable, List, Optional

from src.iol.client import IOLClient
from src.iol.entities import Option
from src.iol.monitor.entities import ParsedSymbol, OptionMonitoringConfig, OptionSnapshot


class OptionSymbolParser:
    def __init__(self, pattern: str = r"(?P<underlying>[A-Z]+)(?P<cp>[CV])(?P<strike>\d+)"):
        self._pattern = re.compile(pattern)

    def parse(self, symbol: str) -> Optional[ParsedSymbol]:
        if not symbol:
            return None
        match = self._pattern.match(symbol)
        if not match:
            return None
        cp = match.group("cp")
        option_type = "CALL" if cp == "C" else "PUT"
        try:
            raw_strike = float(match.group("strike"))
        except ValueError:
            return None
        return ParsedSymbol(
            underlying=match.group("underlying"),
            option_type=option_type,
            raw_strike=raw_strike,
        )


class OptionFilter:
    def __init__(self, config: OptionMonitoringConfig):
        self._config = config

    def apply(self, options: Iterable[Option]) -> List[Option]:
        filtered: List[Option] = []
        for option in options:
            if option.last_price is None or option.last_price <= self._config.min_price:
                continue
            if option.volume is None or option.volume < self._config.min_volume:
                continue
            if option.trade_count is None or option.trade_count < self._config.min_trades:
                continue
            filtered.append(option)
        return filtered


class OptionMetricsCalculator:
    def __init__(self, config: OptionMonitoringConfig, parser: OptionSymbolParser):
        self._config = config
        self._parser = parser

    def _normalize_strike(self, strike: float, spot: float) -> float:
        if strike > spot * 3:
            return strike / 10
        return strike

    def _moneyness(self, option_type: str, strike: float, spot: float) -> float:
        if option_type == "CALL":
            return (spot - strike) / spot
        return (strike - spot) / spot

    def _bucket(self, moneyness: float) -> str:
        if abs(moneyness) < self._config.atm_threshold:
            return "ATM"
        if moneyness > 0:
            return "ITM"
        return "OTM"

    def _score(self, variation: float, volume: float, bucket: str) -> float:
        score = min(variation, self._config.variation_cap)
        score += min(volume * self._config.volume_weight, self._config.volume_cap)
        if bucket == "ATM":
            score += self._config.atm_bonus
        if bucket == "OTM":
            score += self._config.otm_bonus
        return score

    def build_snapshot(self, option: Option) -> Optional[OptionSnapshot]:
        parsed = self._parser.parse(option.symbol)
        underlying = parsed.underlying if parsed else None
        option_type = option.option_type or (parsed.option_type if parsed else None)
        strike = option.strike or (parsed.raw_strike if parsed else None)
        if not underlying or not option_type or strike is None:
            return None

        spot = self._config.spot_prices.get(underlying)
        if spot is None:
            return None

        strike = self._normalize_strike(strike, spot)
        moneyness = self._moneyness(option_type, strike, spot)
        bucket = self._bucket(moneyness)
        variation = option.variation or 0
        volume = option.volume or 0
        trade_count = option.trade_count or 0
        score = self._score(variation, volume, bucket)

        return OptionSnapshot(
            symbol=option.symbol,
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            spot=spot,
            moneyness=moneyness,
            bucket=bucket,
            last_price=option.last_price or 0,
            variation=variation,
            volume=volume,
            trade_count=trade_count,
            score=score,
        )


class OptionMonitorOrchestrator:
    def __init__(self, client: IOLClient, config: OptionMonitoringConfig):
        self._client = client
        self._filter = OptionFilter(config)
        self._calculator = OptionMetricsCalculator(config, OptionSymbolParser())

    async def run(self) -> List[OptionSnapshot]:
        options = await self._client.fetch_all_options()
        filtered = self._filter.apply(options)
        snapshots: List[OptionSnapshot] = []
        for option in filtered:
            snapshot = self._calculator.build_snapshot(option)
            if snapshot:
                snapshots.append(snapshot)
        snapshots.sort(key=lambda snap: snap.score, reverse=True)
        return snapshots
