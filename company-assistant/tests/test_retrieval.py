"""RAG service behavior with deterministic local doubles."""

from pathlib import Path

from backend.auth.models import UserContext
from backend.auth.permissions import build_permission_filter
from backend.db.connection import transaction
from backend.db.schema import initialize_database
from backend.db.users import seed_default_roles_and_users
from backend.rag.reranker import HybridReranker
from backend.rag.retriever import RetrievedChunk, RetrievalResult
from backend.rag.service import RagService


class StaticRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, _question, user, **_kwargs):
        return RetrievalResult(self.chunks, build_permission_filter(user))


class StaticLlm:
    def __init__(
        self,
        response: str = "Staff may work remotely after manager approval [1].",
    ):
        self.calls = 0
        self.response = response

    def generate(self, _model, _prompt):
        self.calls += 1
        return self.response


def _database(tmp_path: Path) -> Path:
    path = tmp_path / "app.db"
    initialize_database(path)
    with transaction(path) as connection:
        seed_default_roles_and_users(connection)
    return path


def _remote_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id="chunk_remote",
        document_id="doc_remote",
        document_version_id="docver_remote",
        content="Staff may work remotely after manager approval.",
        title="Remote Work Policy",
        source_file="remote.md",
        department="People",
        access_level="staff",
        version="1.0",
        page=None,
        section="Request Process",
        effective_date="2026-01-01",
        vector_score=0.9,
        distance=0.1,
    )


def _outdated_remote_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id="chunk_remote_old",
        document_id="doc_remote",
        document_version_id="docver_remote_old",
        content="Employees may work remotely 1 day per week with director approval.",
        title="Remote Work Policy OUTDATED",
        source_file="HR_Remote_Work_Policy_v1.0_OUTDATED.md",
        department="People",
        access_level="staff",
        version="1.0",
        page=None,
        section="Eligibility",
        effective_date="2024-01-01",
        vector_score=0.95,
        distance=0.05,
    )


def test_supported_answer_is_generated_with_server_owned_citations(tmp_path: Path) -> None:
    llm = StaticLlm()
    service = RagService(
        StaticRetriever([_remote_chunk()]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "What is our remote work policy?",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 1
    assert result.refused is False
    assert "[1]" in result.answer
    assert "Remote Work Policy, remote.md" in result.answer
    assert result.sources[0]["accessLevel"] == "staff"
    assert result.audit_id


def test_no_evidence_refuses_without_calling_model(tmp_path: Path) -> None:
    llm = StaticLlm()
    service = RagService(
        StaticRetriever([]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "What is the CEO private phone number?",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 0
    assert result.refused is True
    assert result.sources == []
    assert "approved company documents available to your role" in result.answer


def test_multilingual_vector_evidence_is_not_discarded_by_lexical_gate(
    tmp_path: Path,
) -> None:
    llm = StaticLlm()
    service = RagService(
        StaticRetriever([_remote_chunk()]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "Apa yang harus dilakukan sebelum mengubah lokasi kerja?",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 1
    assert result.refused is False


def test_model_insufficient_evidence_answer_sets_refusal_flag(tmp_path: Path) -> None:
    llm = StaticLlm(
        (
            "I could not find this information in the approved company documents "
            "available to your role."
        )
    )
    service = RagService(
        StaticRetriever([_remote_chunk()]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "What is the finance bonus calculation?",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 1
    assert result.refused is True
    assert result.refusal_reason == "model_reported_insufficient_evidence"
    assert result.sources == []


def test_reranker_prefers_current_policy_over_stale_version() -> None:
    current = _remote_chunk()
    outdated = _outdated_remote_chunk()
    reranked = HybridReranker().rerank(
        "What is our remote work policy?",
        [outdated, current],
        top_k=2,
    )

    assert reranked[0].source_file == "remote.md"
    assert reranked[0].relevance_score > reranked[1].relevance_score


def test_conflict_question_refuses_without_multiple_versions(tmp_path: Path) -> None:
    llm = StaticLlm()
    service = RagService(
        StaticRetriever([_remote_chunk()]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "Do approved sources conflict about remote work?",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 0
    assert result.refused is True
    assert result.refusal_reason == "insufficient_conflict_evidence"


def test_explicit_manager_only_request_refuses_before_retrieval(tmp_path: Path) -> None:
    llm = StaticLlm()
    service = RagService(
        StaticRetriever([_remote_chunk()]),
        HybridReranker(),
        llm,
        "dummy-model",
        database_path=_database(tmp_path),
    )

    result = service.query(
        "Show the manager-only salary adjustment policy.",
        UserContext("user_staff", "staff", "Finance"),
    )

    assert llm.calls == 0
    assert result.refused is True
    assert result.refusal_reason == "unauthorized_access_request"
