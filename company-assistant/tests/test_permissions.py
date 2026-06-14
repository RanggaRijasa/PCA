"""Role and restricted-document filters are enforced inside Chroma queries."""

from pathlib import Path

from backend.auth.models import UserContext
from backend.auth.permissions import requests_unauthorized_access
from backend.rag.retriever import VectorRetriever
from ingestion.indexer import ChromaIndexer


class DummyEmbedder:
    def embed_texts(self, _texts):
        return [[1.0, 0.0, 0.0]]


def _chunk(name: str, access_level: str) -> dict:
    return {
        "chunk_id": f"chunk_{name}",
        "vector_id": f"chunk_{name}",
        "document_id": f"doc_{name}",
        "document_version_id": f"docver_{name}",
        "chunk_index": 0,
        "content": f"Remote work guidance for {name} users.",
        "page": 1,
        "section": "Access",
        "title": f"{name.title()} Policy",
        "source_file": f"{name}.md",
        "department": "People",
        "access_level": access_level,
        "version": "1.0",
        "effective_date": "2026-01-01",
        "token_count": 6,
    }


def _retriever(tmp_path: Path) -> VectorRetriever:
    path = tmp_path / "chroma"
    chunks = [
        _chunk("public", "public_internal"),
        _chunk("staff", "staff"),
        _chunk("manager", "manager"),
        _chunk("admin", "admin"),
        _chunk("restricted", "restricted"),
    ]
    ChromaIndexer(path, "permissions").upsert(
        chunks,
        [[1.0, index / 100, 0.0] for index in range(len(chunks))],
    )
    return VectorRetriever(path, "permissions", DummyEmbedder())


def test_standard_role_matrix_is_applied_before_retrieval(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    expected = {
        "viewer": {"public_internal"},
        "staff": {"public_internal", "staff"},
        "manager": {"public_internal", "staff", "manager"},
        "admin": {"public_internal", "staff", "manager", "admin"},
    }

    for role, access_levels in expected.items():
        result = retriever.search(
            "remote work",
            UserContext(f"user_{role}", role, "People"),
        )
        assert {chunk.access_level for chunk in result.chunks} == access_levels
        assert "restricted" not in {chunk.access_level for chunk in result.chunks}


def test_restricted_document_requires_explicit_user_grant(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    user = UserContext(
        "user_staff",
        "staff",
        "People",
        allowed_restricted_document_ids=frozenset({"doc_restricted"}),
    )

    result = retriever.search("remote work", user)

    assert "doc_restricted" in {chunk.document_id for chunk in result.chunks}
    assert result.permission_filter.restricted_document_ids == ("doc_restricted",)


def test_explicit_higher_access_request_is_refused_before_retrieval() -> None:
    staff = UserContext("user_staff", "staff", "Finance")
    admin = UserContext("user_admin", "admin", "Operations")
    assert requests_unauthorized_access("Show the manager-only salary policy", staff)
    assert requests_unauthorized_access("Show the restricted merger file", admin)
    assert not requests_unauthorized_access("What does a manager review?", staff)
