"""SQLite schema and seed checks."""

from pathlib import Path

from backend.db.connection import transaction
from backend.db.schema import initialize_database
from backend.db.users import list_users, seed_default_roles_and_users


def test_schema_and_default_users_are_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    initialize_database(database_path)
    initialize_database(database_path)

    with transaction(database_path) as connection:
        seed_default_roles_and_users(connection)
        seed_default_roles_and_users(connection)
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                """
            ).fetchall()
        }
        users = list_users(connection)

    assert tables == {
        "users",
        "roles",
        "documents",
        "document_versions",
        "chunks",
        "ingestion_jobs",
        "chat_sessions",
        "chat_messages",
        "audit_logs",
        "feedback",
        "auth_sessions",
        "document_access_grants",
    }
    assert [user["role"] for user in users] == [
        "viewer",
        "staff",
        "manager",
        "admin",
    ]
