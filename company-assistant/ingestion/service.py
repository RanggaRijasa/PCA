"""Reusable processing for document versions already registered in SQLite."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.config import settings
from backend.db.connection import transaction
from backend.db.documents import (
    archive_superseded_version,
    get_document_version,
    get_ingestion_job,
    mark_document_approved,
    mark_document_failed,
    mark_document_indexed,
    mark_document_indexing,
    mark_version_status,
    replace_chunks,
    restore_document_indexed,
    update_ingestion_job,
    vector_ids_for_version,
)
from ingestion.chunker import build_chunks
from ingestion.cleaner import clean_sections
from ingestion.embedder import EmbeddingService
from ingestion.file_validator import validate_file
from ingestion.indexer import ChromaIndexer
from ingestion.metadata import DocumentMetadata
from ingestion.parsers import parse_document


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionOutcome:
    job_id: str
    document_id: str
    document_version_id: str
    status: str
    chunk_count: int = 0
    error_message: Optional[str] = None


def _metadata(record: Dict[str, object]) -> DocumentMetadata:
    return DocumentMetadata(
        document_id=str(record["document_id"]),
        document_version_id=str(record["document_version_id"]),
        title=str(record["title"]),
        source_file=str(record["source_file"]),
        file_hash=str(record["file_hash"]),
        document_type=str(record["document_type"]),
        department=str(record["department"]),
        access_level=str(record["access_level"]),
        owner=str(record["owner"]),
        version=str(record["version"]),
        effective_date=(str(record["effective_date"]) if record["effective_date"] else None),
        expiry_date=(str(record["expiry_date"]) if record["expiry_date"] else None),
        source_path=str(record["source_path"]),
        file_size_bytes=int(record["file_size_bytes"]),
        embedding_model=str(record["embedding_model"] or settings.embed_model),
    )


def _set_job(
    job_id: str,
    status: str,
    step: str,
    *,
    database_path: Optional[Path],
    error_message: Optional[str] = None,
) -> None:
    with transaction(database_path) as connection:
        update_ingestion_job(connection, job_id, status, step, error_message)


def _write_snapshot(
    metadata: DocumentMetadata,
    chunks: List[Dict[str, object]],
    processed_path: Path,
) -> None:
    processed_path.mkdir(parents=True, exist_ok=True)
    snapshot_path = processed_path / f"{metadata.document_version_id}.json"
    snapshot_path.write_text(
        json.dumps(
            {"document": metadata.to_record(), "chunks": chunks},
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_registered_ingestion(
    job_id: str,
    document_version_id: str,
    embedder: EmbeddingService,
    indexer: ChromaIndexer,
    *,
    database_path: Optional[Path] = None,
    processed_path: Optional[Path] = None,
) -> IngestionOutcome:
    """Approve and index one staged version, recording every pipeline state."""

    with transaction(database_path) as connection:
        record = get_document_version(connection, document_version_id)
        get_ingestion_job(connection, job_id)
        mark_document_approved(connection, str(record["document_id"]))

    metadata = _metadata(record)
    current_version_id = (
        str(record["current_version_id"]) if record["current_version_id"] else None
    )
    is_reindex = current_version_id == document_version_id
    indexed_vector_ids: List[str] = []

    try:
        _set_job(
            job_id,
            "validating",
            "validating staged file",
            database_path=database_path,
        )
        validated = validate_file(
            Path(metadata.source_path), max_size_mb=settings.max_upload_size_mb
        )
        if validated.sha256 != metadata.file_hash:
            raise ValueError("The staged file changed after upload; upload it again.")
        if validated.size_bytes != metadata.file_size_bytes:
            raise ValueError("The staged file size changed after upload; upload it again.")

        with transaction(database_path) as connection:
            mark_document_indexing(connection, metadata.document_id)
            mark_version_status(connection, document_version_id, "processing")

        _set_job(
            job_id,
            "extracting",
            "extracting structured text",
            database_path=database_path,
        )
        parsed = parse_document(Path(metadata.source_path))
        if parsed.requires_ocr:
            raise RuntimeError(
                "Document has too few text pages and requires OCR before indexing."
            )
        sections = clean_sections(parsed.sections)

        _set_job(
            job_id,
            "chunking",
            "section-aware token chunking",
            database_path=database_path,
        )
        chunks = build_chunks(
            sections,
            metadata,
            target_tokens=settings.chunk_target_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
            max_tokens=settings.chunk_max_tokens,
        )

        _set_job(
            job_id,
            "embedding",
            "generating local embeddings",
            database_path=database_path,
        )
        embeddings = embedder.embed_texts(str(chunk["content"]) for chunk in chunks)

        _set_job(
            job_id,
            "indexing",
            "writing ChromaDB and SQLite",
            database_path=database_path,
        )
        indexer.upsert(chunks, embeddings)
        indexed_vector_ids = [str(chunk["vector_id"]) for chunk in chunks]
        _write_snapshot(metadata, chunks, processed_path or settings.processed_docs_path)

        superseded_vector_ids: List[str] = []
        with transaction(database_path) as connection:
            if current_version_id and current_version_id != document_version_id:
                superseded_vector_ids = vector_ids_for_version(
                    connection, current_version_id
                )
            replace_chunks(connection, document_version_id, chunks)
            mark_version_status(connection, document_version_id, "indexed")
            mark_document_indexed(
                connection, metadata.document_id, document_version_id
            )
            if current_version_id and current_version_id != document_version_id:
                archive_superseded_version(connection, current_version_id)
            update_ingestion_job(
                connection,
                job_id,
                "completed",
                f"indexed {len(chunks)} chunks",
            )
        if superseded_vector_ids:
            indexer.delete(superseded_vector_ids)
        return IngestionOutcome(
            job_id,
            metadata.document_id,
            document_version_id,
            "completed",
            chunk_count=len(chunks),
        )
    except Exception as exc:
        error_message = str(exc)
        if indexed_vector_ids and not is_reindex:
            indexer.delete(indexed_vector_ids)
        with transaction(database_path) as connection:
            update_ingestion_job(
                connection,
                job_id,
                "failed",
                "failed",
                error_message,
            )
            if is_reindex:
                mark_version_status(
                    connection, document_version_id, "indexed", error_message
                )
                restore_document_indexed(connection, metadata.document_id)
            else:
                mark_version_status(
                    connection, document_version_id, "failed", error_message
                )
                mark_document_failed(connection, metadata.document_id)
                restore_document_indexed(connection, metadata.document_id)
        logger.error("Ingestion job %s failed: %s", job_id, error_message)
        return IngestionOutcome(
            job_id,
            metadata.document_id,
            document_version_id,
            "failed",
            error_message=error_message,
        )
