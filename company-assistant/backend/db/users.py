"""Role and user repository functions."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from backend.auth.password import hash_password


ROLES = [
    ("role_viewer", "viewer", "Public internal documents only"),
    ("role_staff", "staff", "Staff and public internal documents"),
    ("role_manager", "manager", "Manager, staff, and public internal documents"),
    ("role_admin", "admin", "Administrative and all standard role documents"),
]

MOCK_USERS = [
    ("user_viewer", "viewer", "Lina Hartono", "viewer@company.local", "role_viewer", "General"),
    ("user_staff", "staff", "Budi Santoso", "staff@company.local", "role_staff", "Finance"),
    ("user_manager", "manager", "Andrew Davis", "manager@company.local", "role_manager", "HR"),
    ("user_admin", "admin", "Maya Putri", "admin@company.local", "role_admin", "Operations"),
]


def seed_default_roles_and_users(
    connection: sqlite3.Connection, default_password: Optional[str] = None
) -> None:
    connection.executemany(
        """
        INSERT INTO roles (id, name, description)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET description = excluded.description
        """,
        ROLES,
    )
    connection.executemany(
        """
        INSERT INTO users (id, username, name, email, role_id, department, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        ON CONFLICT(username) DO UPDATE SET
            name = excluded.name,
            email = excluded.email,
            role_id = excluded.role_id,
            department = excluded.department,
            status = 'active',
            updated_at = CURRENT_TIMESTAMP
        """,
        MOCK_USERS,
    )
    if default_password:
        password_hash = hash_password(default_password)
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE password_hash IS NULL",
            (password_hash,),
        )


def list_users(connection: sqlite3.Connection) -> List[Dict[str, object]]:
    rows = connection.execute(
        """
        SELECT users.id, users.username, users.name, users.email,
               roles.name AS role, users.department, users.status
        FROM users
        JOIN roles ON roles.id = users.role_id
        ORDER BY CASE roles.name
            WHEN 'viewer' THEN 1
            WHEN 'staff' THEN 2
            WHEN 'manager' THEN 3
            WHEN 'admin' THEN 4
        END
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_user(connection: sqlite3.Connection, user_id: str) -> Dict[str, object]:
    row = connection.execute(
        """
        SELECT users.id, users.username, users.name, users.email,
               roles.name AS role, users.department, users.status
        FROM users
        JOIN roles ON roles.id = users.role_id
        WHERE users.id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"User '{user_id}' was not found.")
    return dict(row)


def get_user_for_login(
    connection: sqlite3.Connection, username_or_email: str
) -> Dict[str, object]:
    row = connection.execute(
        """
        SELECT users.id, users.username, users.name, users.email,
               users.password_hash, roles.name AS role,
               users.department, users.status
        FROM users
        JOIN roles ON roles.id = users.role_id
        WHERE lower(users.username) = lower(?) OR lower(users.email) = lower(?)
        """,
        (username_or_email, username_or_email),
    ).fetchone()
    if row is None:
        raise KeyError("User was not found.")
    return dict(row)


def list_restricted_document_grants(
    connection: sqlite3.Connection, user_id: str
) -> List[str]:
    now = datetime.now(timezone.utc).isoformat()
    rows = connection.execute(
        """
        SELECT document_id
        FROM document_access_grants
        WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)
        ORDER BY document_id
        """,
        (user_id, now),
    ).fetchall()
    return [str(row["document_id"]) for row in rows]


def grant_restricted_document_access(
    connection: sqlite3.Connection,
    user_id: str,
    document_id: str,
    granted_by_user_id: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> str:
    grant_id = f"grant_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO document_access_grants (
            id, user_id, document_id, granted_by_user_id, expires_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, document_id) DO UPDATE SET
            granted_by_user_id = excluded.granted_by_user_id,
            expires_at = excluded.expires_at
        """,
        (grant_id, user_id, document_id, granted_by_user_id, expires_at),
    )
    return grant_id
