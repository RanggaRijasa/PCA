"""Authenticated API contract checks."""

from fastapi.testclient import TestClient

from backend.db.connection import transaction
from conftest import login


def test_health_and_auth_contracts(api_client: TestClient) -> None:
    health = api_client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "version": "0.13.0", "mode": "local-rag"}

    assert api_client.get("/api/me").status_code == 401
    login(api_client, "admin")
    me = api_client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["role"] == "admin"
    assert "password" not in me.text.lower()


def test_conversations_mock_chat_and_feedback(api_client: TestClient) -> None:
    login(api_client, "staff")
    create_response = api_client.post("/api/conversations", json={"title": "API test"})
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    detail = api_client.get(f"/api/conversations/{conversation_id}")
    assert detail.status_code == 200
    assert detail.json()["messages"] == []

    chat_response = api_client.post(
        "/api/chat/mock",
        json={"conversationId": conversation_id, "message": "Remote work?"},
    )
    assert chat_response.status_code == 200
    message_id = chat_response.json()["messageId"]

    feedback = api_client.post(
        "/api/feedback", json={"messageId": message_id, "rating": "up"}
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedbackId"].startswith("feedback_")


def test_admin_endpoints_are_backend_protected(api_client: TestClient) -> None:
    login(api_client, "staff")
    assert api_client.get("/api/audit-logs").status_code == 403
    assert api_client.get("/api/evaluation/runs").status_code == 403
    assert api_client.get("/api/admin/ingestion/jobs").status_code == 403

    api_client.post("/api/auth/logout")
    login(api_client, "admin")
    assert api_client.get("/api/audit-logs").status_code == 200
    assert api_client.get("/api/evaluation/runs").status_code == 200
    assert api_client.get("/api/admin/ingestion/jobs").status_code == 200


def test_documents_endpoint_reads_database_and_enforces_access(
    api_client: TestClient, auth_database
) -> None:
    documents = [
        ("doc_public", "Public Guide", "public.md", "public_internal"),
        ("doc_staff", "Staff Guide", "staff.md", "staff"),
        ("doc_manager", "Manager Guide", "manager.md", "manager"),
        ("doc_admin", "Admin Guide", "admin.md", "admin"),
        ("doc_restricted", "Restricted Guide", "restricted.md", "restricted"),
    ]
    with transaction(auth_database) as connection:
        connection.executemany(
            """
            INSERT INTO documents (
                id, title, source_file, document_type, department,
                access_level, owner, status
            ) VALUES (?, ?, ?, 'policy', 'General', ?, 'Test Owner', 'indexed')
            """,
            documents,
        )
        connection.execute(
            """
            INSERT INTO document_versions (
                id, document_id, file_hash, version, source_path,
                file_size_bytes, status, indexed_at
            ) VALUES ('version_public', 'doc_public', 'hash_public', 'v1.0',
                      'data/raw/public.md', 10, 'indexed', CURRENT_TIMESTAMP)
            """
        )
        connection.execute(
            "UPDATE documents SET current_version_id = 'version_public' WHERE id = 'doc_public'"
        )
        connection.execute(
            """
            INSERT INTO chunks (
                id, document_id, document_version_id, chunk_index, content,
                title, source_file, department, access_level, version,
                token_count, vector_id
            ) VALUES ('chunk_public', 'doc_public', 'version_public', 0, 'Public content',
                      'Public Guide', 'public.md', 'General', 'public_internal', 'v1.0',
                      2, 'vector_public')
            """
        )
        connection.execute(
            """
            INSERT INTO document_access_grants (id, user_id, document_id)
            VALUES ('grant_viewer_restricted', 'user_viewer', 'doc_restricted')
            """
        )

    login(api_client, "staff")
    staff_items = api_client.get("/api/documents").json()["items"]
    assert {item["title"] for item in staff_items} == {"Public Guide", "Staff Guide"}
    public_item = next(item for item in staff_items if item["id"] == "doc_public")
    assert public_item["version"] == "v1.0"
    assert public_item["chunkCount"] == 1

    api_client.post("/api/auth/logout")
    login(api_client, "viewer")
    viewer_items = api_client.get("/api/documents").json()["items"]
    assert {item["title"] for item in viewer_items} == {
        "Public Guide",
        "Restricted Guide",
    }

    api_client.post("/api/auth/logout")
    login(api_client, "admin")
    admin_items = api_client.get("/api/documents").json()["items"]
    assert {item["title"] for item in admin_items} == {
        "Public Guide",
        "Staff Guide",
        "Manager Guide",
        "Admin Guide",
    }


def test_conversation_ownership_is_enforced(api_client: TestClient) -> None:
    login(api_client, "staff")
    conversation_id = api_client.post(
        "/api/conversations", json={"title": "Private staff chat"}
    ).json()["id"]
    api_client.post("/api/auth/logout")
    login(api_client, "viewer")
    assert api_client.get(f"/api/conversations/{conversation_id}").status_code == 404


def test_readable_not_found_error(api_client: TestClient) -> None:
    login(api_client, "admin")
    response = api_client.get("/api/conversations/not-real")
    assert response.status_code == 404
    assert response.json() == {
        "error": "Conversation not found",
        "code": "CONVERSATION_NOT_FOUND",
    }
