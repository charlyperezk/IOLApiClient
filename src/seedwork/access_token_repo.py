from datetime import datetime
import sqlite3
from pathlib import Path
from typing import Optional, Union

from .interfaces import AccessTokenRepo
from .sqlite_db import get_shared_connection
from .value_objects import AccessToken


class SQLiteAccessTokenRepo(AccessTokenRepo[str]):
    """SQLite-backed repository for caching access tokens per identifier."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        connection: Optional[sqlite3.Connection] = None,
    ) -> None:
        self._connection = connection or get_shared_connection(db_path)
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
