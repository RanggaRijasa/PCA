"""Authenticated administration endpoints for local operations."""

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.api.models import RunIngestionRequest
from backend.services.admin_ingestion import DuplicateUploadError, stage_admin_upload
from backend.config import settings
from backend.db.audit import create_audit_log
from backend.db.audit import list_audit_logs as list_persisted_audit_logs
from backend.db.connection import get_connection, transaction
from backend.db.documents import (
    create_ingestion_job,
    get_document_version,
    get_ingestion_job,
    list_documents_for_access,
    list_ingestion_jobs as list_persisted_ingestion_jobs,
)
from backend.auth.models import UserContext
from backend.auth.permissions import allowed_access_levels
from backend.auth.session import get_current_user, require_admin
from backend.llm.ollama_client import OllamaClient
from ingestion.embedder import EmbeddingService
from ingestion.file_validator import FileValidationError
from ingestion.indexer import ChromaIndexer
from ingestion.metadata import MetadataValidationError
from ingestion.service import run_registered_ingestion

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/documents")
def list_documents(
    user: UserContext = Depends(get_current_user),
) -> dict[str, list[dict]]:
    connection = get_connection()
    try:
        items = list_documents_for_access(
            connection,
            allowed_access_levels(user.role),
            user.allowed_restricted_document_ids,
        )
    finally:
        connection.close()
    return {"items": items}


@router.get("/audit-logs")
def list_audit_logs(
    _admin: UserContext = Depends(require_admin),
) -> dict[str, list[dict]]:
    connection = get_connection()
    try:
        persisted = list_persisted_audit_logs(connection)
    finally:
        connection.close()
    return {"items": persisted}


@router.get("/evaluation/runs")
def list_evaluation_runs(
    _admin: UserContext = Depends(require_admin),
) -> dict[str, list[dict]]:
    items: list[dict] = []
    settings.eval_reports_path.mkdir(parents=True, exist_ok=True)
    for path in sorted(
        settings.eval_reports_path.glob("*-eval-results.json"), reverse=True
    ):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return {"items": items}


@router.post("/admin/documents/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    department: str = Form(...),
    access_level: str = Form(...),
    owner: str = Form(...),
    version: str = Form(...),
    effective_date: str = Form(...),
    document_type: str = Form(...),
    expiry_date: str = Form(default=""),
    admin: UserContext = Depends(require_admin),
) -> dict[str, object]:
    payload = {
        "title": title,
        "department": department,
        "access_level": access_level,
        "owner": owner,
        "version": version,
        "effective_date": effective_date,
        "expiry_date": expiry_date or None,
        "document_type": document_type,
    }
    try:
        staged = stage_admin_upload(
            file.file,
            file.filename or "",
            payload,
            admin.id,
        )
    except DuplicateUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": str(exc), "code": "DUPLICATE_DOCUMENT"},
        ) from exc
    except (FileValidationError, MetadataValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": str(exc), "code": "INVALID_UPLOAD"},
        ) from exc
    finally:
        file.file.close()
    return {"document": staged}


def _runtime() -> tuple[EmbeddingService, ChromaIndexer]:
    client = OllamaClient(
        base_url=settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    return (
        EmbeddingService(client, settings.embed_model),
        ChromaIndexer(settings.chroma_path, settings.chroma_collection),
    )


@router.post("/admin/ingestion/run")
def run_ingestion(
    payload: RunIngestionRequest,
    admin: UserContext = Depends(require_admin),
) -> dict[str, object]:
    if not payload.jobId and not payload.documentVersionId:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Provide jobId for a queued upload or documentVersionId for re-indexing.",
                "code": "INGESTION_TARGET_REQUIRED",
            },
        )

    with transaction() as connection:
        if payload.jobId:
            try:
                job = get_ingestion_job(connection, payload.jobId)
            except KeyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": str(exc), "code": "INGESTION_JOB_NOT_FOUND"},
                ) from exc
            if job["status"] not in {"queued", "failed"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": f"Job is already {job['status']}.",
                        "code": "INGESTION_JOB_NOT_RUNNABLE",
                    },
                )
            job_id = str(job["id"])
            document_version_id = str(job["document_version_id"])
        else:
            document_version_id = str(payload.documentVersionId)
            try:
                record = get_document_version(connection, document_version_id)
            except KeyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": str(exc), "code": "DOCUMENT_VERSION_NOT_FOUND"},
                ) from exc
            if not payload.reindex:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Set reindex=true to create a new job for this version.",
                        "code": "REINDEX_CONFIRMATION_REQUIRED",
                    },
                )
            job_id = f"ingest_{uuid4().hex}"
            create_ingestion_job(
                connection,
                job_id,
                str(record["source_file"]),
                str(record["document_id"]),
                document_version_id,
                current_step="queued for re-indexing",
            )

    embedder, indexer = _runtime()
    outcome = run_registered_ingestion(
        job_id,
        document_version_id,
        embedder,
        indexer,
    )
    with transaction() as connection:
        create_audit_log(
            connection,
            event_type="admin_ingestion_run",
            user_id=admin.id,
            document_ids=[outcome.document_id],
            chunk_ids=[],
            permission_filters={
                "action": "reindex" if payload.reindex else "approve_and_index",
                "job_id": job_id,
            },
            status=outcome.status,
        )
        persisted_job = next(
            item
            for item in list_persisted_ingestion_jobs(connection)
            if item["id"] == job_id
        )
    return {
        "job": persisted_job,
        "chunkCount": outcome.chunk_count,
        "searchable": outcome.status == "completed",
    }


@router.get("/admin/ingestion/jobs")
def list_ingestion_jobs(
    _admin: UserContext = Depends(require_admin),
) -> dict[str, list[dict[str, object]]]:
    connection = get_connection()
    try:
        return {"items": list_persisted_ingestion_jobs(connection)}
    finally:
        connection.close()
