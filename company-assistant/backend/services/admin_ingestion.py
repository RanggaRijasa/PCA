"""Secure staging helpers for administrator document uploads."""

from __future__ import annotations

from dataclasses import replace
import re
import sqlite3
from pathlib import Path
from typing import BinaryIO, Dict, Optional
from uuid import uuid4

from backend.config import settings
from backend.db.audit import create_audit_log
from backend.db.connection import transaction
from backend.db.documents import (
    create_document_version,
    create_ingestion_job,
    find_version_by_hash,
    get_ingestion_job,
    upsert_document,
)
from ingestion.file_validator import (
    FileValidationError,
    validate_extension,
    validate_file,
)
from ingestion.metadata import DocumentMetadata, metadata_from_payload


class DuplicateUploadError(ValueError):
    """Raised when an uploaded file or version already exists."""


def _safe_filename(filename: str) -> str:
    basename = Path(filename).name.strip()
    if not basename:
        raise FileValidationError("The upload must include a file name.")
    extension = validate_extension(basename)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(basename).stem).strip("._")
    return f"{(stem or 'document')[:120]}{extension}"


def _write_limited_upload(
    source: BinaryIO,
    destination: Path,
    max_size_mb: int,
) -> None:
    max_bytes = max_size_mb * 1024 * 1024
    total = 0
    with destination.open("wb") as target:
        while block := source.read(1024 * 1024):
            total += len(block)
            if total > max_bytes:
                raise FileValidationError(
                    f"File exceeds the configured {max_size_mb} MB upload limit."
                )
            target.write(block)


def stage_admin_upload(
    source: BinaryIO,
    filename: str,
    payload: Dict[str, object],
    admin_user_id: str,
    *,
    database_path: Optional[Path] = None,
    raw_path: Optional[Path] = None,
) -> Dict[str, object]:
    """Validate, persist, and queue an upload without making it searchable."""

    safe_name = _safe_filename(filename)
    upload_root = (raw_path or settings.raw_docs_path) / "uploads"
    staging_root = upload_root / ".staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    temporary_path = staging_root / f"{uuid4().hex}{Path(safe_name).suffix}"
    final_path: Optional[Path] = None

    try:
        _write_limited_upload(source, temporary_path, settings.max_upload_size_mb)
        validated = validate_file(temporary_path, settings.max_upload_size_mb)
        metadata = metadata_from_payload(
            validated,
            settings.embed_model,
            payload,
            source_file=safe_name,
        )
        version_root = upload_root / metadata.document_id
        version_root.mkdir(parents=True, exist_ok=True)
        final_path = version_root / (
            f"{metadata.document_version_id}--{uuid4().hex[:8]}--{safe_name}"
        )
        temporary_path.replace(final_path)
        metadata = replace(metadata, source_path=str(final_path.resolve()))
        job_id = f"ingest_{uuid4().hex}"

        try:
            with transaction(database_path) as connection:
                duplicate = find_version_by_hash(connection, metadata.file_hash)
                if duplicate:
                    raise DuplicateUploadError(
                        "This exact file is already registered as "
                        f"{duplicate['title']} ({duplicate['document_version_id']})."
                    )
                upsert_document(connection, metadata.to_record())
                create_document_version(connection, metadata.to_record())
                create_ingestion_job(
                    connection,
                    job_id,
                    safe_name,
                    metadata.document_id,
                    metadata.document_version_id,
                    current_step="awaiting admin approval",
                )
                create_audit_log(
                    connection,
                    event_type="admin_document_upload",
                    user_id=admin_user_id,
                    document_ids=[metadata.document_id],
                    permission_filters={
                        "action": "upload",
                        "access_level": metadata.access_level,
                        "searchable": False,
                    },
                    status="completed",
                )
                job = get_ingestion_job(connection, job_id)
        except sqlite3.IntegrityError as exc:
            if "document_versions.document_id, document_versions.version" in str(exc):
                raise DuplicateUploadError(
                    "That document version label already exists. Use a new version value."
                ) from exc
            raise

        return {
            "documentId": metadata.document_id,
            "documentVersionId": metadata.document_version_id,
            "jobId": job_id,
            "sourceFile": safe_name,
            "fileHash": metadata.file_hash,
            "fileSizeBytes": metadata.file_size_bytes,
            "status": job["status"],
            "searchable": False,
        }
    except Exception:
        temporary_path.unlink(missing_ok=True)
        if final_path is not None:
            final_path.unlink(missing_ok=True)
        raise
