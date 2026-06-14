#!/usr/bin/env python3
"""Create a timestamped local backup without copying secrets."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings


SAFE_PROJECT_FILES = (".env.example", "README.md", "requirements.txt")


def _copy_tree(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copytree(source, destination, dirs_exist_ok=True)


def _backup_sqlite(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection = sqlite3.connect(str(source))
    destination_connection = sqlite3.connect(str(destination))
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def _manifest_files(root: Path) -> Iterable[dict[str, object]]:
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "manifest.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        yield {
            "path": str(path.relative_to(root)),
            "sizeBytes": path.stat().st_size,
            "sha256": digest,
        }


def create_backup(destination_root: Path | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_root = destination_root or settings.backups_path
    destination = backup_root / timestamp
    suffix = 1
    while destination.exists():
        destination = backup_root / f"{timestamp}-{suffix}"
        suffix += 1
    destination.mkdir(parents=True)

    _copy_tree(settings.raw_docs_path, destination / "data" / "raw")
    _copy_tree(settings.processed_docs_path, destination / "data" / "processed")
    _copy_tree(settings.chroma_path, destination / "data" / "chroma")
    _backup_sqlite(settings.sqlite_path, destination / "data" / "app.db")
    _copy_tree(PROJECT_ROOT / "eval", destination / "eval")

    safe_config_root = destination / "project"
    safe_config_root.mkdir(parents=True, exist_ok=True)
    for filename in SAFE_PROJECT_FILES:
        source = PROJECT_ROOT / filename
        if source.exists():
            shutil.copy2(source, safe_config_root / filename)

    manifest = {
        "createdAt": datetime.now().astimezone().isoformat(),
        "project": "Private Company Assistant",
        "warning": "Private local backup. Store it securely and do not commit it.",
        "files": list(_manifest_files(destination)),
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        help="Backup parent directory. Defaults to BACKUP_PATH from .env.",
    )
    args = parser.parse_args()
    destination = create_backup(args.destination.expanduser().resolve() if args.destination else None)
    print(f"Backup created: {destination}")
    print("Includes raw/processed documents, ChromaDB, SQLite, eval files, and safe templates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
