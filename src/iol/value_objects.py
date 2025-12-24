from dataclasses import dataclass
from typing import Any, Dict, Optional


def _parse_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class BookEntry:
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "BookEntry":
        if not isinstance(payload, dict):
            return None

        bid_price = _parse_float(payload.get("precioCompra"))
        ask_price = _parse_float(payload.get("precioVenta"))
        bid_size = _parse_float(payload.get("cantidadCompra")) or 0.0
        ask_size = _parse_float(payload.get("cantidadVenta")) or 0.0

        if bid_price is None and ask_price is None:
            return None

        return cls(
            bid_price=bid_price or 0.0,
            bid_size=bid_size,
            ask_price=ask_price or 0.0,
            ask_size=ask_size,
        )
