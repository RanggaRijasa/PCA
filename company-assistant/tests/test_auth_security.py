from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.auth.password import hash_password, verify_password
from backend.auth.session import create_session, user_for_session_token
from backend.db.connection import transaction
from backend.db.schema import initialize_database
from backend.db.users import grant_restricted_document_access, seed_default_roles_and_users


PASSWORD = "A-Strong-Local-Test-Password!"


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password(PASSWORD)
    second = hash_password(PASSWORD)
    assert first != second
    assert PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert not verify_password("wrong-password", first)


def test_session_stores_only_token_hash(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    initialize_database(database)
    with transaction(database) as connection:
        seed_default_roles_and_users(connection, PASSWORD)
        token = create_session(connection, "user_staff", ttl_hours=1)
        row = connection.execute(
            "SELECT token_hash FROM auth_sessions WHERE user_id = 'user_staff'"
        ).fetchone()
        assert row["token_hash"] != token
        assert token not in row["token_hash"]
        user = user_for_session_token(connection, token)
    assert user is not None
    assert user.role == "staff"


def test_restricted_document_grant_is_loaded_from_database(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    initialize_database(database)
    with transaction(database) as connection:
        seed_default_roles_and_users(connection, PASSWORD)
        connection.execute(
            """
            INSERT INTO documents (
                id, title, source_file, document_type, department,
                access_level, owner, status
            ) VALUES ('doc_restricted', 'Restricted', 'restricted.md', 'policy',
                      'People', 'restricted', 'People', 'indexed')
            """
        )
        grant_restricted_document_access(
            connection,
            "user_staff",
            "doc_restricted",
            granted_by_user_id="user_admin",
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        )
        token = create_session(connection, "user_staff")
        user = user_for_session_token(connection, token)
    assert user is not None
    assert user.allowed_restricted_document_ids == frozenset({"doc_restricted"})
