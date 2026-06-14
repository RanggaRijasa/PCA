"""Small local hybrid reranker for the Phase 7 runtime."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, List, Set

from backend.rag.retriever import RetrievedChunk


_TOKEN_PATTERN = re.compile(r"[\w-]+", re.UNICODE)
_STOP_WORDS = {
    "a", "an", "and", "are", "about", "company", "document", "documents",
    "for", "from", "how", "in", "is", "it", "of", "on", "our", "policy",
    "procedure", "the", "to", "what", "when", "where", "which", "who", "with",
    "apa", "bagaimana", "dan", "di", "dari", "ini", "itu", "kapan", "kami",
    "kebijakan", "perusahaan", "untuk", "yang",
}


def meaningful_tokens(text: str) -> Set[str]:
    return {
        token.casefold()
        for token in _TOKEN_PATTERN.findall(text.replace("-", " "))
        if len(token) > 1 and token.casefold() not in _STOP_WORDS
    }


class HybridReranker:
    """Blend Chroma cosine similarity with deterministic lexical coverage."""

    def rerank(
        self,
        question: str,
        chunks: Iterable[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        query_tokens = meaningful_tokens(question)
        reranked: List[RetrievedChunk] = []
        for chunk in chunks:
            searchable = " ".join(
                part for part in (chunk.title, chunk.section or "", chunk.content) if part
            )
            chunk_tokens = meaningful_tokens(searchable)
            lexical_overlap = (
                len(query_tokens.intersection(chunk_tokens)) / len(query_tokens)
                if query_tokens
                else 0.0
            )
            section_name = (chunk.section or "").casefold()
            section_adjustment = 0.0
            if section_name in {"purpose", "overview", "introduction"}:
                section_adjustment = -0.18
            elif any(
                label in section_name
                for label in ("approval", "eligibility", "process", "requirement", "steps")
            ):
                section_adjustment = 0.08
            relevance_score = max(
                0.0,
                min(
                    1.0,
                    (chunk.vector_score * 0.70)
                    + (lexical_overlap * 0.30)
                    + section_adjustment,
                ),
            )
            reranked.append(
                replace(
                    chunk,
                    lexical_overlap=lexical_overlap,
                    relevance_score=relevance_score,
                )
            )
        reranked.sort(
            key=lambda item: (
                item.relevance_score,
                item.effective_date or "",
                item.vector_score,
            ),
            reverse=True,
        )
        return reranked[:top_k]


def has_sufficient_evidence(
    chunks: List[RetrievedChunk],
    minimum_score: float,
    minimum_lexical_overlap: float,
    minimum_vector_score: float = 0.60,
) -> bool:
    if not chunks:
        return False
    top = chunks[0]
    return (
        top.relevance_score >= minimum_score
        and (
            top.lexical_overlap >= minimum_lexical_overlap
            or top.vector_score >= minimum_vector_score
        )
    )
