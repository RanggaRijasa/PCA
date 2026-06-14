"""SQLite connection helpers with local safety defaults."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator, Optional

from backend.config import settings


def get_connection(path: Optional[Path] = None) -> sqlite3.Connection:
    database_path = path or settings.sqlite_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def transaction(path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    connection = get_connection(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()
