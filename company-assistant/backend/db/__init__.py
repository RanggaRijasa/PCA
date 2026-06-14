"""SQLite metadata database package."""

from backend.db.connection import get_connection
from backend.db.schema import initialize_database

__all__ = ["get_connection", "initialize_database"]
