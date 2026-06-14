#!/usr/bin/env python3
"""Print SQLite chunk provenance and matching Chroma collection counts."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.db.connection import get_connection
from backend.db.documents import count_chunks, list_chunks
from ingestion.indexer import ChromaIndexer


def main() -> int:
    connection = get_connection()
    try:
        sqlite_count = count_chunks(connection)
        chunks = list_chunks(connection, limit=20)
    finally:
        connection.close()

    indexer = ChromaIndexer(settings.chroma_path, settings.chroma_collection)
    print(f"SQLite chunks: {sqlite_count}")
    print(f"Chroma vectors: {indexer.count()}")
    print(json.dumps(chunks, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
