"""Secured admin upload and staged ingestion workflow checks."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from backend.db.connection import get_connection, transaction
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users
import backend.services.admin_ingestion as admin_ingestion_service
from backend.services.admin_ingestion import stage_admin_upload
from ingestion.service import run_registered_ingestion

from conftest import login


METADATA_FORM = {
    "title": "Dummy Upload Policy",
    "department": "People",
    "access_level": "staff",
    "owner": "People Team",
    "version": "1.0",
    "effective_date": "2026-06-01",
    "expiry_date": "",
    "document_type": "policy",
}


@pytest.fixture
def admin_upload_storage(
    auth_database: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    raw_path = tmp_path / "data" / "raw"
    monkeypatch.setattr(
        admin_ingestion_service,
        "settings",
        SimpleNamespace(
            raw_docs_path=raw_path,
            max_upload_size_mb=1,
            embed_model="dummy-embed",
        ),
    )
    monkeypatch.setattr(
        admin_ingestion_service,
        "transaction",
        lambda _path=None: transaction(auth_database),
    )
    return raw_path


def test_admin_upload_is_staged_and_not_searchable(
    api_client: TestClient,
    auth_database: Path,
    admin_upload_storage: Path,
) -> None:
    del admin_upload_storage
    login(api_client, "admin")
    response = api_client.post(
        "/api/admin/documents/upload",
        data=METADATA_FORM,
        files={"file": ("dummy_policy.md", b"# Policy\nDummy approved text.", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["document"]["searchable"] is False
    jobs = api_client.get("/api/admin/ingestion/jobs").json()["items"]
    assert jobs[0]["status"] == "queued"
    assert jobs[0]["currentStep"] == "awaiting admin approval"
    with get_connection(auth_database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert connection.execute("SELECT status FROM documents").fetchone()[0] == "pending_ingestion"


def test_non_admin_cannot_upload_or_run(
    api_client: TestClient,
    admin_upload_storage: Path,
) -> None:
    del admin_upload_storage
    login(api_client, "staff")
    upload = api_client.post(
        "/api/admin/documents/upload",
        data=METADATA_FORM,
        files={"file": ("dummy_policy.md", b"# Policy\nText", "text/markdown")},
    )
    run = api_client.post("/api/admin/ingestion/run", json={"jobId": "ingest_x"})
    assert upload.status_code == 403
    assert run.status_code == 403


def test_upload_requires_metadata_and_rejects_invalid_type(
    api_client: TestClient,
    admin_upload_storage: Path,
) -> None:
    del admin_upload_storage
    login(api_client, "admin")
    missing = api_client.post(
        "/api/admin/documents/upload",
        files={"file": ("dummy.md", b"# Dummy", "text/markdown")},
    )
    invalid = api_client.post(
        "/api/admin/documents/upload",
        data=METADATA_FORM,
        files={"file": ("dummy.exe", b"not allowed", "application/octet-stream")},
    )
    assert missing.status_code == 422
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_UPLOAD"


class FakeEmbedder:
    def embed_texts(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class MemoryIndexer:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def upsert(self, chunks, embeddings) -> None:
        assert len(chunks) == len(embeddings)
        self.items.update({str(chunk["vector_id"]): dict(chunk) for chunk in chunks})

    def delete(self, vector_ids) -> None:
        for vector_id in vector_ids:
            self.items.pop(vector_id, None)


def test_registered_ingestion_indexes_only_after_explicit_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "data" / "app.db"
    raw = tmp_path / "data" / "raw"
    initialize_database(database)
    with transaction(database) as connection:
        seed_default_roles_and_users(connection)
    monkeypatch.setattr(
        admin_ingestion_service,
        "settings",
        SimpleNamespace(
            raw_docs_path=raw,
            max_upload_size_mb=1,
            embed_model="dummy-embed",
        ),
    )
    staged = stage_admin_upload(
        BytesIO(b"# Eligibility\nStaff may use this harmless dummy policy."),
        "dummy.md",
        METADATA_FORM,
        "user_admin",
        database_path=database,
        raw_path=raw,
    )
    with get_connection(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0

    indexer = MemoryIndexer()
    outcome = run_registered_ingestion(
        str(staged["jobId"]),
        str(staged["documentVersionId"]),
        FakeEmbedder(),
        indexer,
        database_path=database,
        processed_path=tmp_path / "data" / "processed",
    )

    assert outcome.status == "completed"
    assert outcome.chunk_count == 1
    assert len(indexer.items) == 1
    with get_connection(database) as connection:
        assert connection.execute("SELECT status FROM documents").fetchone()[0] == "indexed"
        assert connection.execute("SELECT status FROM ingestion_jobs").fetchone()[0] == "completed"
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 1
