#!/usr/bin/env python3
"""Create the local SQLite metadata database and seed mock users."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.db.connection import transaction
from backend.db.schema import initialize_database
from backend.db.users import list_users, seed_default_roles_and_users


def main() -> int:
    if not settings.seed_user_password:
        print("SEED_USER_PASSWORD must be set in .env before initializing users.")
        return 2
    initialize_database()
    with transaction() as connection:
        seed_default_roles_and_users(connection, settings.seed_user_password)
        tables = [
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        users = list_users(connection)

    print(f"SQLite database: {settings.sqlite_path}")
    print(f"Tables created ({len(tables)}): {', '.join(tables)}")
    print("Default local users:")
    for user in users:
        print(
            f"- {user['username']}: role={user['role']}, "
            f"department={user['department']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
