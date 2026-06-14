"""Audit log repository foundation for later chat phases."""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional
from uuid import uuid4

from backend.safety.input_checks import redact_sensitive_text


def create_audit_log(
    connection: sqlite3.Connection,
    event_type: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    question: Optional[str] = None,
    document_ids: Optional[List[str]] = None,
    chunk_ids: Optional[List[str]] = None,
    permission_filters: Optional[Dict[str, object]] = None,
    answer_hash: Optional[str] = None,
    answer_text: Optional[str] = None,
    citations: Optional[List[Dict[str, object]]] = None,
    latency_ms: Optional[int] = None,
    model_name: Optional[str] = None,
    refusal_flag: bool = False,
    status: str = "completed",
) -> str:
    audit_id = f"audit_{uuid4().hex}"
    connection.execute(
        """
        INSERT INTO audit_logs (
            id, user_id, session_id, event_type, question,
            document_ids, chunk_ids, permission_filters,
            answer_hash, answer_text, citations, latency_ms,
            model_name, refusal_flag, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            user_id,
            session_id,
            event_type,
            redact_sensitive_text(question) if question else None,
            json.dumps(document_ids or []),
            json.dumps(chunk_ids or []),
            json.dumps(permission_filters or {}),
            answer_hash,
            redact_sensitive_text(answer_text) if answer_text else None,
            json.dumps(citations or []),
            latency_ms,
            model_name,
            int(refusal_flag),
            status,
        ),
    )
    return audit_id


def list_audit_logs(
    connection: sqlite3.Connection, limit: int = 100
) -> List[Dict[str, object]]:
    rows = connection.execute(
        """
        SELECT audit_logs.id, audit_logs.created_at, audit_logs.event_type,
               audit_logs.question, audit_logs.document_ids, audit_logs.chunk_ids,
               audit_logs.permission_filters, audit_logs.answer_hash,
               audit_logs.answer_text, audit_logs.citations, audit_logs.latency_ms,
               audit_logs.model_name, audit_logs.feedback_rating,
               audit_logs.refusal_flag, audit_logs.status,
               users.name AS user_name, roles.name AS role
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        LEFT JOIN roles ON roles.id = users.role_id
        ORDER BY audit_logs.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    logs: List[Dict[str, object]] = []
    for row in rows:
        document_ids = json.loads(row["document_ids"] or "[]")
        chunk_ids = json.loads(row["chunk_ids"] or "[]")
        citations = json.loads(row["citations"] or "[]")
        permission_filter = json.loads(row["permission_filters"] or "{}")
        status_value = "refused" if row["refusal_flag"] else row["status"]
        if status_value == "completed":
            status_value = "answered"
        logs.append(
            {
                "id": row["id"],
                "timestamp": row["created_at"],
                "user": row["user_name"] or "Unknown local user",
                "role": row["role"] or "viewer",
                "eventType": row["event_type"],
                "questionPreview": (row["question"] or "")[:160],
                "question": row["question"] or "",
                "sourcesCount": len(document_ids),
                "documentIds": document_ids,
                "chunkIds": chunk_ids,
                "citations": citations,
                "permissionFilter": json.dumps(permission_filter, sort_keys=True),
                "permissionFilterData": permission_filter,
                "latencyMs": row["latency_ms"] or 0,
                "modelName": row["model_name"] or "",
                "answerHash": row["answer_hash"] or "",
                "answerText": row["answer_text"],
                "feedbackRating": row["feedback_rating"],
                "refused": bool(row["refusal_flag"]),
                "status": status_value,
            }
        )
    return logs
