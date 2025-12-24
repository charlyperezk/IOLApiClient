import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .interfaces import AccessTokenRepo
from .value_objects import AccessToken


class SQLiteAccessTokenRepo(AccessTokenRepo[str]):
    """SQLite-backed repository for caching access tokens per identifier."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        path = Path(db_path) if db_path else Path(__file__).resolve().parent.parent / "access_tokens.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS access_tokens (
                identifier TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                life_time INTEGER NOT NULL,
                obtained_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, identifier: str) -> Optional[AccessToken]:
        cursor = self._connection.execute(
            "SELECT value, refresh_token, life_time, obtained_at FROM access_tokens WHERE identifier = ?",
            (identifier,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return AccessToken(
            life_time=row["life_time"],
            value=row["value"],
            refresh_token=row["refresh_token"],
            obtained_at=datetime.fromisoformat(row["obtained_at"]),
        )

    def save(self, identifier: str, token: AccessToken) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO access_tokens (
                identifier,
                value,
                refresh_token,
                life_time,
                obtained_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                identifier,
                token.value,
                token.refresh_token,
                token.life_time,
                token.obtained_at.isoformat(),
            ),
        )
        self._connection.commit()
