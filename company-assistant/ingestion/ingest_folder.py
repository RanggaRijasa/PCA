#!/usr/bin/env python3
"""Ingest permission-tagged local documents into ChromaDB and SQLite."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sqlite3
import sys
from typing import Dict, List, Optional
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.db.connection import transaction
from backend.db.documents import (
    attach_job_document,
    create_document_version,
    create_ingestion_job,
    find_version_by_hash,
    mark_document_failed,
    mark_document_indexed,
    mark_version_status,
    replace_chunks,
    update_ingestion_job,
    upsert_document,
)
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users
from backend.llm.ollama_client import OllamaClient
from ingestion.chunker import build_chunks
from ingestion.cleaner import clean_sections
from ingestion.embedder import EmbeddingService
from ingestion.file_validator import SUPPORTED_EXTENSIONS, validate_file
from ingestion.indexer import ChromaIndexer
from ingestion.metadata import DocumentMetadata, load_metadata
from ingestion.parsers import parse_document


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ingestion")


def _discover_files(raw_path: Path) -> List[Path]:
    if not raw_path.exists():
        return []
    return sorted(
        path
        for path in raw_path.rglob("*")
        if path.is_file()
        and not path.name.startswith(".")
        and not any(part.startswith(".") for part in path.relative_to(raw_path).parts)
        and "uploads" not in path.relative_to(raw_path).parts
        and not path.name.endswith(".metadata.json")
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _set_job(
    job_id: str,
    status: str,
    step: str,
    error_message: Optional[str] = None,
) -> None:
    with transaction() as connection:
        update_ingestion_job(
            connection,
            job_id=job_id,
            status=status,
            current_step=step,
            error_message=error_message,
        )


def _write_processed_snapshot(
    metadata: DocumentMetadata, chunks: List[Dict[str, object]]
) -> None:
    settings.processed_docs_path.mkdir(parents=True, exist_ok=True)
    snapshot_path = (
        settings.processed_docs_path / f"{metadata.document_version_id}.json"
    )
    snapshot = {
        "document": metadata.to_record(),
        "chunks": chunks,
    }
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def ingest_file(
    path: Path,
    embedder: EmbeddingService,
    indexer: ChromaIndexer,
) -> str:
    job_id = f"ingest_{uuid4().hex}"
    metadata: Optional[DocumentMetadata] = None
    indexed_vector_ids: List[str] = []
    with transaction() as connection:
        create_ingestion_job(connection, job_id=job_id, source_file=path.name)

    try:
        _set_job(job_id, "validating", "validating file")
        validated = validate_file(path, max_size_mb=settings.max_upload_size_mb)
        metadata = load_metadata(
            validated,
            embedding_model=settings.embed_model,
            metadata_csv_path=settings.metadata_csv_path,
            raw_root=settings.raw_docs_path,
        )

        with transaction() as connection:
            duplicate = find_version_by_hash(connection, validated.sha256)
            if duplicate:
                attach_job_document(
                    connection,
                    job_id,
                    str(duplicate["document_id"]),
                    str(duplicate["document_version_id"]),
                )
                update_ingestion_job(
                    connection,
                    job_id,
                    "completed",
                    f"duplicate skipped: {duplicate['document_version_id']}",
                )
                logger.info("%s skipped: exact duplicate already indexed", path.name)
                return "duplicate"

            upsert_document(connection, metadata.to_record())
            create_document_version(connection, metadata.to_record())
            attach_job_document(
                connection,
                job_id,
                metadata.document_id,
                metadata.document_version_id,
            )
            mark_version_status(
                connection, metadata.document_version_id, "processing"
            )

        _set_job(job_id, "extracting", "extracting structured text")
        parsed = parse_document(path)
        if parsed.requires_ocr:
            raise RuntimeError(
                "Document has too few text pages and requires OCR before indexing."
            )
        cleaned_sections = clean_sections(parsed.sections)

        _set_job(job_id, "chunking", "section-aware token chunking")
        chunks = build_chunks(
            sections=cleaned_sections,
            metadata=metadata,
            target_tokens=settings.chunk_target_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
            max_tokens=settings.chunk_max_tokens,
        )

        _set_job(job_id, "embedding", "generating local embeddings")
        embeddings = embedder.embed_texts(
            str(chunk["content"]) for chunk in chunks
        )

        _set_job(job_id, "indexing", "writing ChromaDB and SQLite")
        indexer.upsert(chunks, embeddings)
        indexed_vector_ids = [str(chunk["vector_id"]) for chunk in chunks]
        with transaction() as connection:
            replace_chunks(connection, metadata.document_version_id, chunks)
            mark_version_status(connection, metadata.document_version_id, "indexed")
            mark_document_indexed(
                connection, metadata.document_id, metadata.document_version_id
            )
            update_ingestion_job(
                connection,
                job_id,
                "completed",
                f"indexed {len(chunks)} chunks",
            )
        _write_processed_snapshot(metadata, chunks)
        logger.info(
            "%s indexed: %s chunks, document_version=%s",
            path.name,
            len(chunks),
            metadata.document_version_id,
        )
        return "indexed"
    except Exception as exc:
        if indexed_vector_ids:
            indexer.delete(indexed_vector_ids)
        error_message = str(exc)
        with transaction() as connection:
            update_ingestion_job(
                connection,
                job_id,
                "failed",
                "failed",
                error_message=error_message,
            )
            if metadata:
                mark_version_status(
                    connection,
                    metadata.document_version_id,
                    "failed",
                    error_message=error_message,
                )
                mark_document_failed(connection, metadata.document_id)
        logger.error("%s failed: %s", path.name, error_message)
        return "failed"


def main() -> int:
    initialize_database()
    with transaction() as connection:
        seed_default_roles_and_users(connection)

    files = _discover_files(settings.raw_docs_path)
    if not files:
        print(f"No source files found in {settings.raw_docs_path}.")
        print("Add PDF, DOCX, TXT, or MD files with sidecars or metadata CSV rows.")
        return 0

    client = OllamaClient(
        base_url=settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    embedder = EmbeddingService(client=client, model=settings.embed_model)
    indexer = ChromaIndexer(
        path=settings.chroma_path,
        collection_name=settings.chroma_collection,
    )

    results = {"indexed": 0, "duplicate": 0, "failed": 0}
    for path in files:
        result = ingest_file(path, embedder=embedder, indexer=indexer)
        results[result] += 1

    print(
        "Ingestion complete: "
        f"{results['indexed']} indexed, "
        f"{results['duplicate']} duplicates, "
        f"{results['failed']} failed."
    )
    print(f"Chroma collection count: {indexer.count()}")
    return 1 if results["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
