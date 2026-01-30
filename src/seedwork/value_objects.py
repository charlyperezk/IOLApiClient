from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

from src.seedwork.utils import split_date_range


@dataclass(frozen=True)
class AccessToken:
    life_time: int
    value: str
    refresh_token: str
    obtained_at: datetime

    @property
    def caducity(self) -> datetime:
        return self.obtained_at + timedelta(seconds=self.life_time)

    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.caducity

    def as_header(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.value}"}


@dataclass(frozen=True)
class APIResponse:
    status_code: int
    content: Dict[str, Any]

    @property
    def sucess(self) -> bool:
        return self.status_code in {200, 201, 204}


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("El inicio del rango debe ser anterior o igual al final.")

    @property
    def span_days(self) -> int:
        return (self.end - self.start).days + 1

    def intersects(self, other: "DateRange") -> bool:
        return self.start <= other.end and other.start <= self.end

    def split(self, max_span_days: int) -> List["DateRange"]:
        return [
            DateRange(start, end)
            for start, end in split_date_range(self.start, self.end, max_span_days)
        ]
