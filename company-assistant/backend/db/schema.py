"""Idempotent SQLite schema for metadata and audit foundations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.db.connection import transaction


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name IN ('viewer', 'staff', 'manager', 'admin')),
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role_id TEXT NOT NULL REFERENCES roles(id),
    department TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    password_hash TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_file TEXT NOT NULL,
    document_type TEXT NOT NULL,
    department TEXT NOT NULL,
    access_level TEXT NOT NULL CHECK (
        access_level IN ('public_internal', 'staff', 'manager', 'admin', 'restricted')
    ),
    owner TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_ingestion' CHECK (
        status IN ('pending_ingestion', 'approved', 'indexing', 'indexed', 'failed', 'archived')
    ),
    current_version_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    file_hash TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    effective_date TEXT,
    expiry_date TEXT,
    source_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    embedding_model TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'indexed', 'failed', 'archived')
    ),
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    indexed_at TEXT,
    UNIQUE(document_id, version)
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_version_id TEXT NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page INTEGER,
    section TEXT,
    title TEXT NOT NULL,
    source_file TEXT NOT NULL,
    department TEXT NOT NULL,
    access_level TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date TEXT,
    token_count INTEGER NOT NULL,
    vector_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_version_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    document_version_id TEXT REFERENCES document_versions(id) ON DELETE SET NULL,
    source_file TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'queued', 'validating', 'extracting', 'chunking', 'embedding',
            'indexing', 'completed', 'failed', 'archived'
        )
    ),
    current_step TEXT NOT NULL,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'complete',
    sources TEXT,
    metadata TEXT,
    audit_id TEXT REFERENCES audit_logs(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    session_id TEXT REFERENCES chat_sessions(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    question TEXT,
    document_ids TEXT,
    chunk_ids TEXT,
    permission_filters TEXT,
    answer_hash TEXT,
    answer_text TEXT,
    citations TEXT,
    latency_ms INTEGER,
    model_name TEXT,
    refusal_flag INTEGER NOT NULL DEFAULT 0 CHECK (refusal_flag IN (0, 1)),
    feedback_rating TEXT CHECK (feedback_rating IN ('up', 'down')),
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    message_id TEXT REFERENCES chat_messages(id) ON DELETE SET NULL,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    audit_id TEXT REFERENCES audit_logs(id) ON DELETE SET NULL,
    rating TEXT NOT NULL CHECK (rating IN ('up', 'down')),
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_access_grants (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    granted_by_user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_access_level ON documents(access_level);
CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_hash ON document_versions(file_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_version_id ON chunks(document_version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_access_level ON chunks(access_level);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_document_access_grants_user_id ON document_access_grants(user_id);
"""


def _columns(connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _add_column_if_missing(
    connection, table: str, column: str, definition: str
) -> None:
    if column not in _columns(connection, table):
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_existing_database(connection) -> None:
    _add_column_if_missing(connection, "users", "password_hash", "TEXT")
    _add_column_if_missing(connection, "chat_messages", "sources", "TEXT")
    _add_column_if_missing(connection, "chat_messages", "metadata", "TEXT")
    _add_column_if_missing(connection, "chat_messages", "audit_id", "TEXT")
    _add_column_if_missing(connection, "audit_logs", "feedback_rating", "TEXT")
    _add_column_if_missing(connection, "feedback", "audit_id", "TEXT")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_audit_id ON feedback(audit_id)"
    )


def initialize_database(path: Optional[Path] = None) -> None:
    with transaction(path) as connection:
        connection.executescript(SCHEMA_SQL)
        _migrate_existing_database(connection)
