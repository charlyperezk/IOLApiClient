from datetime import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from .entities import Attempt, Extraction
from .interfaces import ExtractionRepo
from .sqlite_db import get_shared_connection


def _serialize(obj: Any) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


class InMemoryExtractionRepo(ExtractionRepo):
    saved: List[Extraction]

    def __init__(self) -> None:
        self.saved = []

    def save(self, extraction: Extraction) -> Extraction:
        self.saved.append(extraction)
        return extraction


class SQLiteExtractionRepo(ExtractionRepo):
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
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY,
                identifier TEXT,
                url TEXT,
                method TEXT,
                status TEXT,
                success INTEGER,
                retries INTEGER,
                fetched_at TEXT,
                created_at TEXT,
                headers TEXT,
                params TEXT,
                json_body TEXT,
                attempts TEXT,
                response TEXT
            )
            """
        )
        self._connection.commit()

    def _serialize_attempts(self, attempts: Sequence[Attempt]) -> str:
        serialized = []
        for attempt in attempts:
            serialized.append(
                {
                    "fetched_at": attempt.fetched_at.isoformat(),
                    "status_code": attempt.response.status_code,
                    "content": attempt.response.content,
                }
            )
        return _serialize(serialized)

    def save(self, extraction: Extraction) -> Extraction:
        request = extraction.request
        last_attempt = extraction.attempts[-1]
        response_payload = {
            "status_code": last_attempt.response.status_code,
            "content": last_attempt.response.content,
        }

        self._connection.execute(
            """
            INSERT INTO extractions (
                identifier,
                url,
                method,
                status,
                success,
                retries,
                fetched_at,
                created_at,
                headers,
                params,
                json_body,
                attempts,
                response
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                getattr(request, "identifier", None) or None,
                request.url,
                request.method.value,
                extraction.status.value,
                1 if extraction.success else 0,
                extraction.retries,
                last_attempt.fetched_at.isoformat(),
                request.created_at.isoformat(),
                _serialize(request.headers),
                _serialize(request.params),
                _serialize(request.json),
                self._serialize_attempts(extraction.attempts),
                _serialize(response_payload),
            ),
        )
        self._connection.commit()
        return extraction
