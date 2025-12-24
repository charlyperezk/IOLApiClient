from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any


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
