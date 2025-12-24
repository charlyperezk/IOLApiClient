import sqlite3
from pathlib import Path
from typing import Optional, Union


_SHARED_CONNECTION: Optional[sqlite3.Connection] = None


def get_shared_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    global _SHARED_CONNECTION
    if _SHARED_CONNECTION is None:
        path = Path(db_path) if db_path else Path(__file__).resolve().parent.parent / "db.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        _SHARED_CONNECTION = sqlite3.connect(str(path), check_same_thread=False)
        _SHARED_CONNECTION.row_factory = sqlite3.Row
    return _SHARED_CONNECTION
