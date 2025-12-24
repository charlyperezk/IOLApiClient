from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.iol.value_objects import BookEntry


def _parse_optional_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_optional_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def _build_book_entries(payload: Any) -> List[BookEntry]:
    if not isinstance(payload, list):
        return []
    entries: List[BookEntry] = []
    for item in payload:
        if isinstance(item, dict):
            entry = BookEntry.from_payload(item)
            if entry:
                entries.append(entry)
    return entries


@dataclass
class MarketQuote:
    symbol: str
    description: str
    book_entries: List[BookEntry]
    last_price: Optional[float]
    variation: Optional[float]
    open_price: Optional[float]
    high: Optional[float]
    low: Optional[float]
    previous_close: Optional[float]
    volume: Optional[float]
    trade_count: Optional[float]
    timestamp: Optional[datetime]
    market: Optional[str]
    currency: Optional[str]
    term: Optional[str]
    min_lot: Optional[float]
    lot: Optional[float]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def best_bid(self) -> Optional[BookEntry]:
        bids = [entry for entry in self.book_entries if entry.bid_price > 0]
        return max(bids, key=lambda entry: entry.bid_price, default=None)

    @property
    def best_ask(self) -> Optional[BookEntry]:
        asks = [entry for entry in self.book_entries if entry.ask_price > 0]
        return min(asks, key=lambda entry: entry.ask_price, default=None)

    @property
    def spread(self) -> Optional[float]:
        bid = self.best_bid
        ask = self.best_ask
        if not bid or not ask:
            return None
        return ask.ask_price - bid.bid_price

    @property
    def mid_price(self) -> Optional[float]:
        bid = self.best_bid
        ask = self.best_ask
        if not bid or not ask:
            return None
        return (ask.ask_price + bid.bid_price) / 2


@dataclass
class Option(MarketQuote):
    option_type: Optional[str] = None
    strike: Optional[float] = None
    expiry: Optional[datetime] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "Option":
        symbol = payload.get("simbolo") or payload.get("symbol")
        if not symbol:
            raise ValueError("Can't find symbol")

        description = payload.get("descripcion") or str(symbol)
        last_price = _parse_optional_float(payload.get("ultimoPrecio"))
        variation = _parse_optional_float(payload.get("variacionPorcentual"))
        open_price = _parse_optional_float(payload.get("apertura"))
        high = _parse_optional_float(payload.get("maximo"))
        low = _parse_optional_float(payload.get("minimo"))
        previous_close = _parse_optional_float(payload.get("ultimoCierre"))
        volume = _parse_optional_float(payload.get("volumen"))
        trade_count = _parse_optional_float(payload.get("cantidadOperaciones"))
        strike = (
            _parse_optional_float(payload.get("precioEjercicio"))
            or _parse_optional_float(payload.get("strike"))
        )
        expiry = _parse_optional_datetime(
            payload.get("fechaVencimiento") or payload.get("vencimiento")
        )
        timestamp = _parse_optional_datetime(payload.get("fecha"))
        option_type = (
            payload.get("tipoOpcion")
            or payload.get("tipo")
            or payload.get("type")
            or None
        )
        market = payload.get("mercado")
        currency = payload.get("moneda")
        term = payload.get("plazo")
        min_lot = _parse_optional_float(payload.get("laminaMinima"))
        lot = _parse_optional_float(payload.get("lote"))
        book_entries = _build_book_entries(payload.get("puntas"))

        return cls(
            symbol=symbol,
            description=description,
            book_entries=book_entries,
            last_price=last_price,
            variation=variation,
            open_price=open_price,
            high=high,
            low=low,
            previous_close=previous_close,
            volume=volume,
            trade_count=trade_count,
            timestamp=timestamp,
            market=market,
            currency=currency,
            term=term,
            min_lot=min_lot,
            lot=lot,
            raw=payload,
            option_type=option_type.upper() if option_type else None,
            strike=strike,
            expiry=expiry,
        )


@dataclass
class TickerCotization(MarketQuote):
    trend: Optional[str] = None
    amount_traded: Optional[float] = None
    nominal_volume: Optional[float] = None
    average_price: Optional[float] = None
    adjusted_price: Optional[float] = None
    open_interest: Optional[float] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "TickerCotization":
        base = Option.from_payload  # reuse parsing for shared fields
        data = base(payload)
        if data is None:
            raise ValueError("Can't found data")
            
        trend = payload.get("tendencia")
        amount_traded = _parse_optional_float(payload.get("montoOperado"))
        nominal_volume = _parse_optional_float(payload.get("volumenNominal"))
        average_price = _parse_optional_float(payload.get("precioPromedio"))
        adjusted_price = _parse_optional_float(payload.get("precioAjuste"))
        open_interest = _parse_optional_float(payload.get("interesesAbiertos"))

        return cls(
            symbol=data.symbol,
            description=data.description,
            book_entries=data.book_entries,
            last_price=data.last_price,
            variation=_parse_optional_float(payload.get("variacion"))
            or data.variation,
            open_price=data.open_price,
            high=data.high,
            low=data.low,
            previous_close=_parse_optional_float(payload.get("cierreAnterior"))
            or data.previous_close,
            volume=data.volume,
            trade_count=data.trade_count,
            timestamp=_parse_optional_datetime(payload.get("fechaHora"))
            or data.timestamp,
            market=data.market,
            currency=data.currency,
            term=data.term,
            min_lot=data.min_lot,
            lot=data.lot,
            raw=payload,
            trend=trend,
            amount_traded=amount_traded,
            nominal_volume=nominal_volume,
            average_price=average_price,
            adjusted_price=adjusted_price,
            open_interest=open_interest,
        )
