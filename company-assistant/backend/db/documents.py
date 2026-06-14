"""Document, version, chunk, and ingestion job repository functions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def find_version_by_hash(
    connection: sqlite3.Connection, file_hash: str
) -> Optional[Dict[str, object]]:
    row = connection.execute(
        """
        SELECT document_versions.*,
               document_versions.id AS document_version_id,
               documents.title,
               documents.source_file
        FROM document_versions
        JOIN documents ON documents.id = document_versions.document_id
        WHERE document_versions.file_hash = ?
        """,
        (file_hash,),
    ).fetchone()
    return dict(row) if row else None


def upsert_document(connection: sqlite3.Connection, metadata: Dict[str, object]) -> None:
    connection.execute(
        """
        INSERT INTO documents (
            id, title, source_file, document_type, department,
            access_level, owner, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_ingestion')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            source_file = excluded.source_file,
            document_type = excluded.document_type,
            department = excluded.department,
            access_level = excluded.access_level,
            owner = excluded.owner,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            metadata["document_id"],
            metadata["title"],
            metadata["source_file"],
            metadata["document_type"],
            metadata["department"],
            metadata["access_level"],
            metadata["owner"],
        ),
    )


def create_document_version(
    connection: sqlite3.Connection, metadata: Dict[str, object]
) -> None:
    connection.execute(
        """
        INSERT INTO document_versions (
            id, document_id, file_hash, version, effective_date, expiry_date,
            source_path, file_size_bytes, embedding_model, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            metadata["document_version_id"],
            metadata["document_id"],
            metadata["file_hash"],
            metadata["version"],
            metadata.get("effective_date"),
            metadata.get("expiry_date"),
            metadata["source_path"],
            metadata["file_size_bytes"],
            metadata["embedding_model"],
        ),
    )


def create_ingestion_job(
    connection: sqlite3.Connection,
    job_id: str,
    source_file: str,
    document_id: Optional[str] = None,
    document_version_id: Optional[str] = None,
    current_step: str = "queued",
) -> None:
    connection.execute(
        """
        INSERT INTO ingestion_jobs (
            id, document_id, document_version_id, source_file,
            status, current_step
        )
        VALUES (?, ?, ?, ?, 'queued', ?)
        """,
        (job_id, document_id, document_version_id, source_file, current_step),
    )


def attach_job_document(
    connection: sqlite3.Connection,
    job_id: str,
    document_id: str,
    document_version_id: str,
) -> None:
    connection.execute(
        """
        UPDATE ingestion_jobs
        SET document_id = ?, document_version_id = ?
        WHERE id = ?
        """,
        (document_id, document_version_id, job_id),
    )


def update_ingestion_job(
    connection: sqlite3.Connection,
    job_id: str,
    status: str,
    current_step: str,
    error_message: Optional[str] = None,
) -> None:
    completed = "CURRENT_TIMESTAMP" if status in {"completed", "failed", "archived"} else "NULL"
    started = "COALESCE(started_at, CURRENT_TIMESTAMP)" if status != "queued" else "started_at"
    connection.execute(
        f"""
        UPDATE ingestion_jobs
        SET status = ?, current_step = ?, error_message = ?,
            started_at = {started}, completed_at = {completed}
        WHERE id = ?
        """,
        (status, current_step, error_message, job_id),
    )


def mark_version_status(
    connection: sqlite3.Connection,
    document_version_id: str,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    indexed_at = "CURRENT_TIMESTAMP" if status == "indexed" else "indexed_at"
    connection.execute(
        f"""
        UPDATE document_versions
        SET status = ?, error_message = ?, indexed_at = {indexed_at}
        WHERE id = ?
        """,
        (status, error_message, document_version_id),
    )


def replace_chunks(
    connection: sqlite3.Connection,
    document_version_id: str,
    chunks: Iterable[Dict[str, object]],
) -> None:
    connection.execute(
        "DELETE FROM chunks WHERE document_version_id = ?",
        (document_version_id,),
    )
    connection.executemany(
        """
        INSERT INTO chunks (
            id, document_id, document_version_id, chunk_index, content,
            page, section, title, source_file, department, access_level,
            version, effective_date, token_count, vector_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                chunk["chunk_id"],
                chunk["document_id"],
                chunk["document_version_id"],
                chunk["chunk_index"],
                chunk["content"],
                chunk.get("page"),
                chunk.get("section"),
                chunk["title"],
                chunk["source_file"],
                chunk["department"],
                chunk["access_level"],
                chunk["version"],
                chunk.get("effective_date"),
                chunk["token_count"],
                chunk["vector_id"],
            )
            for chunk in chunks
        ],
    )


def mark_document_indexed(
    connection: sqlite3.Connection,
    document_id: str,
    document_version_id: str,
) -> None:
    connection.execute(
        """
        UPDATE documents
        SET status = 'indexed',
            current_version_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (document_version_id, document_id),
    )


def mark_document_approved(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        UPDATE documents
        SET status = CASE WHEN current_version_id IS NULL THEN 'approved' ELSE status END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (document_id,),
    )


def mark_document_indexing(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        UPDATE documents
        SET status = 'indexing', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (document_id,),
    )


def mark_document_failed(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        UPDATE documents
        SET status = CASE
                WHEN current_version_id IS NULL THEN 'failed'
                ELSE status
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (document_id,),
    )


def restore_document_indexed(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        UPDATE documents
        SET status = 'indexed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND current_version_id IS NOT NULL
        """,
        (document_id,),
    )


def get_document_version(
    connection: sqlite3.Connection, document_version_id: str
) -> Dict[str, object]:
    row = connection.execute(
        """
        SELECT document_versions.id AS document_version_id,
               document_versions.document_id,
               document_versions.file_hash,
               document_versions.version,
               document_versions.effective_date,
               document_versions.expiry_date,
               document_versions.source_path,
               document_versions.file_size_bytes,
               document_versions.embedding_model,
               document_versions.status AS version_status,
               documents.title, documents.source_file, documents.document_type,
               documents.department, documents.access_level, documents.owner,
               documents.status AS document_status,
               documents.current_version_id
        FROM document_versions
        JOIN documents ON documents.id = document_versions.document_id
        WHERE document_versions.id = ?
        """,
        (document_version_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"Document version '{document_version_id}' was not found.")
    return dict(row)


def get_ingestion_job(connection: sqlite3.Connection, job_id: str) -> Dict[str, object]:
    row = connection.execute(
        """
        SELECT id, document_id, document_version_id, source_file, status,
               current_step, error_message, started_at, completed_at, created_at
        FROM ingestion_jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"Ingestion job '{job_id}' was not found.")
    return dict(row)


def list_ingestion_jobs(
    connection: sqlite3.Connection, limit: int = 100
) -> List[Dict[str, object]]:
    rows = connection.execute(
        """
        SELECT ingestion_jobs.id, ingestion_jobs.document_id,
               ingestion_jobs.document_version_id, ingestion_jobs.source_file,
               ingestion_jobs.status, ingestion_jobs.current_step,
               ingestion_jobs.error_message, ingestion_jobs.started_at,
               ingestion_jobs.completed_at, ingestion_jobs.created_at,
               documents.title, documents.department, documents.access_level,
               documents.owner, documents.document_type,
               documents.status AS document_status,
               documents.current_version_id,
               document_versions.version, document_versions.effective_date,
               document_versions.expiry_date, document_versions.file_size_bytes
        FROM ingestion_jobs
        LEFT JOIN documents ON documents.id = ingestion_jobs.document_id
        LEFT JOIN document_versions
          ON document_versions.id = ingestion_jobs.document_version_id
        ORDER BY ingestion_jobs.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "documentId": row["document_id"],
            "documentVersionId": row["document_version_id"],
            "sourceFile": row["source_file"],
            "title": row["title"] or row["source_file"],
            "department": row["department"] or "",
            "accessLevel": row["access_level"] or "restricted",
            "owner": row["owner"] or "",
            "documentType": row["document_type"] or "other",
            "version": row["version"] or "",
            "effectiveDate": row["effective_date"],
            "expiryDate": row["expiry_date"],
            "fileSizeBytes": row["file_size_bytes"] or 0,
            "status": row["status"],
            "documentStatus": row["document_status"],
            "currentStep": row["current_step"],
            "errorMessage": row["error_message"],
            "startedAt": row["started_at"],
            "completedAt": row["completed_at"],
            "createdAt": row["created_at"],
            "isCurrentVersion": bool(
                row["current_version_id"]
                and row["document_version_id"]
                and row["current_version_id"] == row["document_version_id"]
            ),
        }
        for row in rows
    ]


def list_documents_for_access(
    connection: sqlite3.Connection,
    access_levels: Iterable[str],
    restricted_document_ids: Iterable[str] = (),
) -> List[Dict[str, object]]:
    """List document metadata without exposing records outside the user's grants."""

    levels = tuple(sorted(set(access_levels)))
    restricted_ids = tuple(sorted(set(restricted_document_ids)))
    clauses: List[str] = []
    parameters: List[object] = []
    if levels:
        clauses.append(f"documents.access_level IN ({','.join('?' for _ in levels)})")
        parameters.extend(levels)
    if restricted_ids:
        clauses.append(
            "(documents.access_level = 'restricted' "
            f"AND documents.id IN ({','.join('?' for _ in restricted_ids)}))"
        )
        parameters.extend(restricted_ids)
    if not clauses:
        return []

    rows = connection.execute(
        f"""
        SELECT documents.id, documents.title, documents.source_file,
               documents.document_type, documents.department,
               documents.access_level, documents.owner, documents.status,
               document_versions.version, document_versions.indexed_at,
               COUNT(chunks.id) AS chunk_count
        FROM documents
        LEFT JOIN document_versions
          ON document_versions.id = COALESCE(
              documents.current_version_id,
              (
                  SELECT candidate.id
                  FROM document_versions AS candidate
                  WHERE candidate.document_id = documents.id
                  ORDER BY candidate.created_at DESC
                  LIMIT 1
              )
          )
        LEFT JOIN chunks
          ON chunks.document_version_id = document_versions.id
        WHERE {' OR '.join(clauses)}
        GROUP BY documents.id, document_versions.id
        ORDER BY documents.title COLLATE NOCASE ASC
        """,
        parameters,
    ).fetchall()
    items: List[Dict[str, object]] = []
    for row in rows:
        suffix = Path(str(row["source_file"])).suffix.lower().lstrip(".")
        items.append(
            {
                "id": row["id"],
                "title": row["title"],
                "fileName": row["source_file"],
                "fileType": suffix or row["document_type"],
                "department": row["department"],
                "accessLevel": row["access_level"],
                "version": row["version"] or "Not versioned",
                "owner": row["owner"],
                "status": row["status"],
                "lastIndexedAt": row["indexed_at"],
                "chunkCount": int(row["chunk_count"] or 0),
            }
        )
    return items


def vector_ids_for_version(
    connection: sqlite3.Connection, document_version_id: str
) -> List[str]:
    rows = connection.execute(
        "SELECT vector_id FROM chunks WHERE document_version_id = ?",
        (document_version_id,),
    ).fetchall()
    return [str(row["vector_id"]) for row in rows]


def archive_superseded_version(
    connection: sqlite3.Connection, document_version_id: str
) -> None:
    connection.execute(
        "UPDATE document_versions SET status = 'archived' WHERE id = ?",
        (document_version_id,),
    )
    connection.execute(
        "DELETE FROM chunks WHERE document_version_id = ?",
        (document_version_id,),
    )


def count_chunks(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])


def list_chunks(
    connection: sqlite3.Connection, limit: int = 20
) -> List[Dict[str, object]]:
    rows = connection.execute(
        """
        SELECT id, document_id, document_version_id, chunk_index, title,
               source_file, page, section, version, department, access_level,
               effective_date, token_count, vector_id
        FROM chunks
        ORDER BY created_at DESC, chunk_index ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]
