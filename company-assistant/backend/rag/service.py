"""Orchestrate secure retrieval, local generation, citations, and audit logging."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import logging
from pathlib import Path
import re
from time import perf_counter
from typing import Dict, List, Optional

from backend.auth.models import UserContext
from backend.auth.permissions import (
    PermissionFilter,
    build_permission_filter,
    requests_unauthorized_access,
)
from backend.config import settings
from backend.db.audit import create_audit_log
from backend.db.connection import transaction
from backend.llm.ollama_client import OllamaClient
from backend.rag.citation_builder import build_api_sources, build_sources_section
from backend.rag.prompt_builder import build_prompt
from backend.rag.reranker import HybridReranker, has_sufficient_evidence
from backend.rag.response_parser import clean_answer_body, is_refusal_body
from backend.rag.retriever import RetrievedChunk, VectorRetriever
from backend.safety.input_checks import check_user_input
from backend.safety.output_checks import unsafe_output_reason
from backend.safety.prompt_injection import SECURITY_REFUSAL
from ingestion.embedder import EmbeddingService


logger = logging.getLogger(__name__)

NO_EVIDENCE_REFUSAL = (
    "I could not find this information in the approved company documents "
    "available to your role."
)
PERMISSION_REFUSAL = (
    "I cannot answer this because your current role does not have access to "
    "the requested document class."
)

_CONFLICT_QUERY = re.compile(
    r"\b(conflict|conflicting|disagree)\b|\bolder\b.{0,50}\bnewer\b|\bnewer\b.{0,50}\bolder\b",
    re.I,
)


@dataclass(frozen=True)
class PreparedQuery:
    question: str
    user: UserContext
    permission_filter: PermissionFilter
    chunks: List[RetrievedChunk]
    refusal_reason: Optional[str]
    retrieval_ms: int


@dataclass(frozen=True)
class RagResult:
    answer: str
    sources: List[Dict[str, object]]
    chunks: List[RetrievedChunk]
    permission_filter: PermissionFilter
    confidence: str
    refused: bool
    refusal_reason: Optional[str]
    audit_id: Optional[str]
    latency_ms: int
    retrieval_ms: int
    generation_ms: int

    def metadata(self) -> Dict[str, object]:
        return {
            "modelName": settings.llm_model,
            "embeddingModel": settings.embed_model,
            "retrievalTopK": settings.default_top_k,
            "rerankTopN": settings.rerank_top_k,
            "maxContextChunks": settings.max_context_chunks,
            "contextScoreMargin": settings.context_score_margin,
            "minimumVectorScore": settings.retrieval_min_vector_score,
            "reranker": "hybrid-vector-lexical",
            "latencyMs": self.latency_ms,
            "retrievalMs": self.retrieval_ms,
            "generationMs": self.generation_ms,
            "auditId": self.audit_id,
            "refused": self.refused,
            "refusalReason": self.refusal_reason,
            "permissionFilter": self.permission_filter.to_audit_dict(),
        }


class RagService:
    def __init__(
        self,
        retriever: VectorRetriever,
        reranker: HybridReranker,
        llm_client: OllamaClient,
        llm_model: str,
        database_path: Optional[Path] = None,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.database_path = database_path or settings.sqlite_path

    def prepare(
        self,
        question: str,
        user: UserContext,
        department_filter: str = "all",
        source_filter: str = "all",
    ) -> PreparedQuery:
        started = perf_counter()
        checked = check_user_input(question)
        if checked.refusal_reason:
            permission_filter = build_permission_filter(
                user, department=department_filter
            )
            return PreparedQuery(
                checked.normalized_question,
                user,
                permission_filter,
                [],
                checked.refusal_reason,
                int((perf_counter() - started) * 1000),
            )
        if requests_unauthorized_access(checked.normalized_question, user):
            permission_filter = build_permission_filter(
                user, department=department_filter
            )
            return PreparedQuery(
                checked.normalized_question,
                user,
                permission_filter,
                [],
                "unauthorized_access_request",
                int((perf_counter() - started) * 1000),
            )

        retrieval = self.retriever.search(
            checked.normalized_question,
            user,
            top_k=settings.default_top_k,
            department_filter=department_filter,
            source_filter=source_filter,
        )
        reranked = self.reranker.rerank(
            checked.normalized_question,
            retrieval.chunks,
            top_k=settings.rerank_top_k,
        )
        refusal_reason = None
        if not has_sufficient_evidence(
            reranked,
            minimum_score=settings.retrieval_min_score,
            minimum_lexical_overlap=settings.retrieval_min_lexical_overlap,
            minimum_vector_score=settings.retrieval_min_vector_score,
        ):
            refusal_reason = "insufficient_evidence"
            reranked = []
        elif _CONFLICT_QUERY.search(checked.normalized_question):
            versions_by_document: Dict[str, set[str]] = {}
            for chunk in reranked:
                versions_by_document.setdefault(chunk.document_id, set()).add(
                    chunk.document_version_id
                )
            explicit_conflict = any(
                _CONFLICT_QUERY.search(chunk.content) for chunk in reranked
            )
            multiple_versions = any(
                len(versions) > 1 for versions in versions_by_document.values()
            )
            if not explicit_conflict and not multiple_versions:
                refusal_reason = "insufficient_conflict_evidence"
                reranked = []
        elif reranked:
            cutoff = max(
                settings.retrieval_min_score,
                reranked[0].relevance_score - settings.context_score_margin,
            )
            reranked = [chunk for chunk in reranked if chunk.relevance_score >= cutoff]
        return PreparedQuery(
            checked.normalized_question,
            user,
            retrieval.permission_filter,
            reranked[: settings.max_context_chunks],
            refusal_reason,
            int((perf_counter() - started) * 1000),
        )

    @staticmethod
    def _confidence(chunks: List[RetrievedChunk]) -> str:
        if not chunks:
            return "Low"
        if chunks[0].relevance_score >= 0.68 and len(chunks) >= 2:
            return "High"
        if chunks[0].relevance_score >= 0.45:
            return "Medium"
        return "Low"

    @staticmethod
    def _refusal_body(reason: str) -> str:
        if reason == "prompt_injection_or_secret_request":
            return SECURITY_REFUSAL
        if reason == "unauthorized_access_request":
            return PERMISSION_REFUSAL
        return NO_EVIDENCE_REFUSAL

    @staticmethod
    def _assemble_answer(
        body: str,
        chunks: List[RetrievedChunk],
        confidence: str,
        notes: str,
    ) -> str:
        return (
            f"Answer:\n{body}\n\n"
            f"Sources:\n{build_sources_section(chunks)}\n\n"
            f"Confidence:\n{confidence}\n\n"
            f"Notes:\n{notes}"
        )

    def _write_audit(
        self,
        prepared: PreparedQuery,
        answer: str,
        sources: List[Dict[str, object]],
        latency_ms: int,
        refused: bool,
        status: str,
        session_id: Optional[str],
    ) -> Optional[str]:
        with transaction(self.database_path) as connection:
            return create_audit_log(
                connection,
                event_type="rag_chat",
                user_id=prepared.user.id,
                session_id=session_id,
                question=prepared.question,
                document_ids=list(
                    dict.fromkeys(chunk.document_id for chunk in prepared.chunks)
                ),
                chunk_ids=[chunk.id for chunk in prepared.chunks],
                permission_filters=prepared.permission_filter.to_audit_dict(),
                answer_hash=hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                answer_text=answer if settings.audit_store_answer_text else None,
                citations=sources,
                latency_ms=latency_ms,
                model_name=self.llm_model,
                refusal_flag=refused,
                status=status,
            )

    def record_error(
        self,
        prepared: PreparedQuery,
        latency_ms: int,
        session_id: Optional[str],
    ) -> Optional[str]:
        return self._write_audit(
            prepared,
            answer="",
            sources=[],
            latency_ms=latency_ms,
            refused=False,
            status="error",
            session_id=session_id,
        )

    def query(
        self,
        question: str,
        user: UserContext,
        department_filter: str = "all",
        source_filter: str = "all",
        session_id: Optional[str] = None,
        stream_model: bool = False,
    ) -> RagResult:
        started = perf_counter()
        try:
            prepared = self.prepare(
                question,
                user,
                department_filter=department_filter,
                source_filter=source_filter,
            )
        except Exception:
            checked = check_user_input(question)
            failed_prepared = PreparedQuery(
                checked.normalized_question,
                user,
                build_permission_filter(user, department=department_filter),
                [],
                "runtime_error",
                int((perf_counter() - started) * 1000),
            )
            self.record_error(
                failed_prepared,
                int((perf_counter() - started) * 1000),
                session_id,
            )
            raise

        generation_ms = 0
        if prepared.refusal_reason:
            body = self._refusal_body(prepared.refusal_reason)
            confidence = "Low"
            if prepared.refusal_reason == "prompt_injection_or_secret_request":
                notes = "The request was refused by the safety policy."
            elif prepared.refusal_reason == "unauthorized_access_request":
                notes = "The requested access class is not available to this user."
            else:
                notes = "No sufficiently relevant authorized evidence was retrieved."
            answer = self._assemble_answer(body, [], confidence, notes)
            sources: List[Dict[str, object]] = []
            refused = True
            refusal_reason = prepared.refusal_reason
        else:
            generation_started = perf_counter()
            prompt = build_prompt(prepared.question, prepared.chunks)
            try:
                if stream_model:
                    raw_body = "".join(
                        self.llm_client.stream_generate(self.llm_model, prompt)
                    )
                else:
                    raw_body = self.llm_client.generate(self.llm_model, prompt)
            except Exception:
                self.record_error(
                    prepared,
                    int((perf_counter() - started) * 1000),
                    session_id,
                )
                raise
            generation_ms = int((perf_counter() - generation_started) * 1000)
            output_reason = unsafe_output_reason(raw_body)
            if output_reason:
                body = SECURITY_REFUSAL
                chunks: List[RetrievedChunk] = []
                confidence = "Low"
                notes = "The generated output failed a safety check."
                refused = True
                refusal_reason = output_reason
            else:
                model_reported_refusal = is_refusal_body(raw_body)
                body = clean_answer_body(
                    raw_body,
                    0 if model_reported_refusal else len(prepared.chunks),
                )
                if model_reported_refusal or is_refusal_body(body):
                    chunks = []
                    confidence = "Low"
                    notes = (
                        "The generated output said the retrieved context was insufficient."
                    )
                    refused = True
                    refusal_reason = "model_reported_insufficient_evidence"
                else:
                    chunks = prepared.chunks
                    confidence = self._confidence(chunks)
                    notes = (
                        f"Grounded in {len(chunks)} permission-filtered source chunk(s)."
                    )
                    refused = False
                    refusal_reason = None
            sources = build_api_sources(chunks)
            answer = self._assemble_answer(body, chunks, confidence, notes)

        latency_ms = int((perf_counter() - started) * 1000)
        audit_id = self._write_audit(
            prepared,
            answer,
            sources,
            latency_ms,
            refused,
            "refused" if refused else "completed",
            session_id,
        )
        return RagResult(
            answer=answer,
            sources=sources,
            chunks=[] if refused else prepared.chunks,
            permission_filter=prepared.permission_filter,
            confidence=confidence,
            refused=refused,
            refusal_reason=refusal_reason,
            audit_id=audit_id,
            latency_ms=latency_ms,
            retrieval_ms=prepared.retrieval_ms,
            generation_ms=generation_ms,
        )


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    client = OllamaClient(
        settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    embedder = EmbeddingService(client, settings.embed_model)
    retriever = VectorRetriever(
        settings.chroma_path,
        settings.chroma_collection,
        embedder,
        sqlite_path=settings.sqlite_path,
    )
    return RagService(
        retriever,
        HybridReranker(),
        client,
        settings.llm_model,
        database_path=settings.sqlite_path,
    )
