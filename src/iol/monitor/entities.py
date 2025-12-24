import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class OptionMonitoringConfig:
    spot_prices: Dict[str, float]
    min_price: float = 0
    min_volume: float = 5
    min_trades: float = 2
    atm_threshold: float = 0.03
    variation_cap: float = 50
    volume_weight: float = 2
    volume_cap: float = 40
    atm_bonus: float = 20
    otm_bonus: float = 10


@dataclass
class ParsedSymbol:
    underlying: str
    option_type: str
    raw_strike: float


@dataclass
class OptionSnapshot:
    symbol: str
    underlying: str
    option_type: str
    strike: float
    spot: float
    moneyness: float
    bucket: str
    last_price: float
    variation: float
    volume: float
    trade_count: float
    score: float