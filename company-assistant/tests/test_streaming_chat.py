"""Streaming API contract without invoking local models."""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import chat
from backend.auth.models import UserContext
from backend.auth.permissions import build_permission_filter
from backend.auth.session import get_current_user
from backend.db.chat import create_chat_session
from backend.db.connection import transaction
from backend.llm.ollama_client import OllamaOfflineError
from backend.main import app
from backend.rag.retriever import RetrievedChunk
from backend.rag.service import RagResult


class FakeService:
    def query(self, _question, user, **_kwargs):
        chunk = RetrievedChunk(
            id="chunk_1",
            document_id="doc_1",
            document_version_id="docver_1",
            content="Remote work is allowed.",
            title="Remote Work Policy",
            source_file="remote.md",
            department="People",
            access_level="staff",
            version="1.0",
            page=None,
            section="Eligibility",
            effective_date="2026-01-01",
            vector_score=0.9,
            distance=0.1,
            lexical_overlap=1.0,
            relevance_score=0.93,
        )
        return RagResult(
            answer="Answer:\nRemote work is allowed [1].\n\nSources:\n1. Remote Work Policy, remote.md, section Eligibility, version 1.0, effective 2026-01-01\n\nConfidence:\nHigh\n\nNotes:\nGrounded.",
            sources=[{
                "id": "chunk_1", "documentId": "doc_1", "chunkId": "chunk_1",
                "title": "Remote Work Policy", "fileName": "remote.md", "fileType": "md",
                "department": "People", "accessLevel": "staff", "section": "Eligibility",
                "version": "1.0", "effectiveDate": "2026-01-01", "snippet": chunk.content,
                "relevanceScore": 0.93, "citationRank": 1,
            }],
            chunks=[chunk],
            permission_filter=build_permission_filter(user),
            confidence="High",
            refused=False,
            refusal_reason=None,
            audit_id=None,
            latency_ms=25,
            retrieval_ms=5,
            generation_ms=20,
        )


class OfflineService:
    def query(self, *_args, **_kwargs):
        raise OllamaOfflineError(
            "Ollama is not reachable. Check that Ollama is running at http://localhost:11434."
        )


def _conversation(database: Path, user_id: str) -> str:
    with transaction(database) as connection:
        return create_chat_session(connection, user_id, "Streaming test")["id"]


def test_real_chat_stream_contains_tokens_sources_and_metadata(
    monkeypatch, api_client: TestClient, auth_database: Path
) -> None:
    user = UserContext("user_staff", "staff", "Finance", "Budi Santoso")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(chat, "get_rag_service", lambda: FakeService())
    conversation_id = _conversation(auth_database, user.id)
    try:
        response = api_client.post(
            "/api/chat",
            json={"conversationId": conversation_id, "message": "Remote work?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "event: start" in response.text
    assert "event: token" in response.text
    assert "event: final" in response.text
    assert "Remote Work Policy" in response.text


def test_real_chat_stream_surfaces_ollama_offline_error(
    monkeypatch, api_client: TestClient, auth_database: Path
) -> None:
    user = UserContext("user_staff", "staff", "Finance", "Budi Santoso")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(chat, "get_rag_service", lambda: OfflineService())
    conversation_id = _conversation(auth_database, user.id)
    try:
        response = api_client.post(
            "/api/chat",
            json={"conversationId": conversation_id, "message": "Remote work?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "OLLAMA_OFFLINE" in response.text
