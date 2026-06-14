"""Local password authentication and opaque server-side sessions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import sqlite3
from typing import Dict, Optional, cast
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status

from backend.auth.models import UserContext, UserRole
from backend.auth.password import verify_password
from backend.config import settings
from backend.db.connection import get_connection
from backend.db.users import (
    get_user,
    get_user_for_login,
    list_restricted_document_grants,
)


ROLE_USER_IDS: Dict[UserRole, str] = {
    "viewer": "user_viewer",
    "staff": "user_staff",
    "manager": "user_manager",
    "admin": "user_admin",
}


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _from_record(
    connection: sqlite3.Connection, record: Dict[str, object]
) -> UserContext:
    return UserContext(
        id=str(record["id"]),
        role=cast(UserRole, record["role"]),
        department=str(record["department"]),
        name=str(record["name"]),
        username=str(record.get("username", "")),
        email=str(record.get("email", "")),
        allowed_restricted_document_ids=frozenset(
            list_restricted_document_grants(connection, str(record["id"]))
        ),
    )


def authenticate_user(
    connection: sqlite3.Connection, username: str, password: str
) -> UserContext:
    """Validate credentials with a generic failure message."""

    try:
        record = get_user_for_login(connection, username.strip())
    except KeyError as exc:
        raise ValueError("Invalid username or password.") from exc
    password_hash = str(record.get("password_hash") or "")
    if record["status"] != "active" or not verify_password(password, password_hash):
        raise ValueError("Invalid username or password.")
    return _from_record(connection, record)


def create_session(
    connection: sqlite3.Connection,
    user_id: str,
    ttl_hours: Optional[int] = None,
) -> str:
    """Create an opaque session and store only its SHA256 hash."""

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=ttl_hours or settings.session_ttl_hours
    )
    connection.execute(
        """
        INSERT INTO auth_sessions (id, user_id, token_hash, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (f"session_{uuid4().hex}", user_id, _token_hash(token), expires_at.isoformat()),
    )
    return token


def revoke_session(connection: sqlite3.Connection, token: str) -> None:
    connection.execute(
        """
        UPDATE auth_sessions
        SET revoked_at = CURRENT_TIMESTAMP
        WHERE token_hash = ? AND revoked_at IS NULL
        """,
        (_token_hash(token),),
    )


def _request_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return request.cookies.get(settings.session_cookie_name)


def user_for_session_token(
    connection: sqlite3.Connection, token: str
) -> Optional[UserContext]:
    now = datetime.now(timezone.utc).isoformat()
    row = connection.execute(
        """
        SELECT users.id, users.username, users.name, users.email,
               roles.name AS role, users.department, users.status,
               auth_sessions.id AS session_id
        FROM auth_sessions
        JOIN users ON users.id = auth_sessions.user_id
        JOIN roles ON roles.id = users.role_id
        WHERE auth_sessions.token_hash = ?
          AND auth_sessions.revoked_at IS NULL
          AND auth_sessions.expires_at > ?
        """,
        (_token_hash(token), now),
    ).fetchone()
    if row is None or row["status"] != "active":
        return None
    connection.execute(
        "UPDATE auth_sessions SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
        (row["session_id"],),
    )
    return _from_record(connection, dict(row))


def get_current_user(request: Request) -> UserContext:
    token = _request_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication is required.", "code": "AUTH_REQUIRED"},
        )
    connection = get_connection()
    try:
        user = user_for_session_token(connection, token)
        connection.commit()
    finally:
        connection.close()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "The session is invalid or expired.", "code": "INVALID_SESSION"},
        )
    return user


def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Administrator access is required.", "code": "ADMIN_REQUIRED"},
        )
    return user


def simulated_user_for_role(role: UserRole) -> UserContext:
    """Load a seeded role for terminal tools only, never for HTTP authorization."""

    connection = get_connection()
    try:
        return _from_record(connection, get_user(connection, ROLE_USER_IDS[role]))
    finally:
        connection.close()


def session_token_from_request(request: Request) -> Optional[str]:
    """Expose token extraction for logout without exposing token values to logs."""

    return _request_token(request)
