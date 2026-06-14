"""SQLite persistence for user-owned chat sessions and messages."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
from typing import Dict, List, Optional
from uuid import uuid4

from backend.safety.input_checks import redact_sensitive_text


def create_chat_session(
    connection: sqlite3.Connection, user_id: str, title: str = "New chat"
) -> Dict[str, str]:
    session_id = f"conv_{uuid4().hex[:12]}"
    connection.execute(
        "INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)",
        (session_id, user_id, title.strip()),
    )
    row = connection.execute(
        "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    return _session_summary(row)


def _session_summary(row: sqlite3.Row) -> Dict[str, str]:
    return {
        "id": str(row["id"]),
        "title": str(row["title"]),
        "createdAt": str(row["created_at"]),
        "updatedAt": str(row["updated_at"]),
    }


def list_chat_sessions(
    connection: sqlite3.Connection, user_id: str
) -> List[Dict[str, str]]:
    rows = connection.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [_session_summary(row) for row in rows]


def get_chat_session(
    connection: sqlite3.Connection, session_id: str, user_id: str
) -> Dict[str, object]:
    row = connection.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    ).fetchone()
    if row is None:
        raise KeyError("Conversation not found.")
    messages = connection.execute(
        """
        SELECT id, role, content, status, sources, metadata, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at, rowid
        """,
        (session_id,),
    ).fetchall()
    result: Dict[str, object] = _session_summary(row)
    result["messages"] = [
        {
            "id": message["id"],
            "role": message["role"],
            "content": message["content"],
            "status": message["status"],
            "sources": json.loads(message["sources"] or "[]"),
            "metadata": json.loads(message["metadata"] or "{}"),
            "createdAt": message["created_at"],
        }
        for message in messages
    ]
    return result


def ensure_chat_session_owner(
    connection: sqlite3.Connection, session_id: str, user_id: str
) -> None:
    row = connection.execute(
        "SELECT 1 FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()
    if row is None:
        raise KeyError("Conversation not found.")


def append_chat_message(
    connection: sqlite3.Connection,
    message_id: str,
    session_id: str,
    role: str,
    content: str,
    status: str = "complete",
    sources: Optional[List[Dict[str, object]]] = None,
    metadata: Optional[Dict[str, object]] = None,
    audit_id: Optional[str] = None,
) -> None:
    safe_content = redact_sensitive_text(content)
    connection.execute(
        """
        INSERT INTO chat_messages (
            id, session_id, role, content, status, sources, metadata, audit_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            session_id,
            role,
            safe_content,
            status,
            json.dumps(sources or []),
            json.dumps(metadata or {}),
            audit_id,
        ),
    )
    title_update = ""
    parameters: tuple[object, ...]
    if role == "user":
        row = connection.execute(
            "SELECT title FROM chat_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is not None and row["title"] == "New chat":
            title_update = ", title = ?"
            parameters = (safe_content[:48], session_id)
        else:
            parameters = (session_id,)
    else:
        parameters = (session_id,)
    connection.execute(
        f"UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP{title_update} WHERE id = ?",
        parameters,
    )


def message_ownership(
    connection: sqlite3.Connection, message_id: str
) -> Optional[Dict[str, object]]:
    row = connection.execute(
        """
        SELECT chat_messages.id, chat_messages.audit_id, chat_sessions.user_id
        FROM chat_messages
        JOIN chat_sessions ON chat_sessions.id = chat_messages.session_id
        WHERE chat_messages.id = ? AND chat_messages.role = 'assistant'
        """,
        (message_id,),
    ).fetchone()
    return dict(row) if row is not None else None
