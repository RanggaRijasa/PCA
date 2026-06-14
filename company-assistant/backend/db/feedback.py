"""Persist answer feedback and link it back to its audit event."""

from __future__ import annotations

import sqlite3
from typing import Optional
from uuid import uuid4

from backend.db.chat import message_ownership
from backend.safety.input_checks import redact_sensitive_text


def create_feedback(
    connection: sqlite3.Connection,
    rating: str,
    message_id: str,
    user_id: str,
    comment: Optional[str] = None,
    audit_id: Optional[str] = None,
) -> str:
    ownership = message_ownership(connection, message_id)
    if ownership is None or ownership["user_id"] != user_id:
        raise KeyError("Answer message not found.")
    linked_audit_id = str(ownership["audit_id"] or audit_id or "") or None
    if audit_id and linked_audit_id != audit_id:
        raise ValueError("Feedback audit ID does not match the answer message.")

    existing = connection.execute(
        "SELECT id FROM feedback WHERE message_id = ? AND user_id = ?",
        (message_id, user_id),
    ).fetchone()
    safe_comment = redact_sensitive_text(comment) if comment else None
    if existing:
        feedback_id = str(existing["id"])
        connection.execute(
            """
            UPDATE feedback
            SET rating = ?, comment = ?, audit_id = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (rating, safe_comment, linked_audit_id, feedback_id),
        )
    else:
        feedback_id = f"feedback_{uuid4().hex}"
        connection.execute(
            """
            INSERT INTO feedback (id, message_id, user_id, audit_id, rating, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feedback_id, message_id, user_id, linked_audit_id, rating, safe_comment),
        )
    if linked_audit_id:
        connection.execute(
            "UPDATE audit_logs SET feedback_rating = ? WHERE id = ?",
            (rating, linked_audit_id),
        )
    return feedback_id
