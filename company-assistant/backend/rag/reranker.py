"""Small local hybrid reranker for the Phase 7 runtime."""

from __future__ import annotations

import re
from datetime import date
from dataclasses import replace
from typing import Dict, Iterable, List, Optional, Set, Tuple

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


_STALE_MARKERS = ("outdated", "superseded", "obsolete", "deprecated")
_VERSION_TOKEN = re.compile(r"v?\d+(?:\.\d+)*|\d{4}", re.I)


def _parse_effective_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _family_tokens(text: str) -> Tuple[str, ...]:
    normalized = re.sub(r"[_./-]+", " ", text)
    tokens = {
        token
        for token in meaningful_tokens(normalized)
        if token not in _STALE_MARKERS and not _VERSION_TOKEN.fullmatch(token)
    }
    return tuple(sorted(tokens))


def _document_family_key(chunk: RetrievedChunk) -> Tuple[str, ...]:
    title_key = _family_tokens(chunk.title)
    if title_key:
        return title_key
    source_key = _family_tokens(chunk.source_file)
    return source_key or (chunk.document_id,)


def _stale_adjustment(chunk: RetrievedChunk) -> float:
    haystack = f"{chunk.title} {chunk.source_file}".casefold()
    if any(marker in haystack for marker in _STALE_MARKERS):
        return -0.12
    return 0.0


class HybridReranker:
    """Blend Chroma cosine similarity with deterministic lexical coverage."""

    def rerank(
        self,
        question: str,
        chunks: Iterable[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        query_tokens = meaningful_tokens(question)
        candidates = list(chunks)
        family_dates: Dict[Tuple[str, ...], Set[date]] = {}
        for chunk in candidates:
            effective_date = _parse_effective_date(chunk.effective_date)
            if effective_date is None:
                continue
            family_dates.setdefault(_document_family_key(chunk), set()).add(effective_date)
        latest_by_family = {
            family: max(dates)
            for family, dates in family_dates.items()
            if len(dates) > 1
        }

        reranked: List[RetrievedChunk] = []
        for chunk in candidates:
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

            version_adjustment = 0.0
            effective_date = _parse_effective_date(chunk.effective_date)
            latest_effective_date = latest_by_family.get(_document_family_key(chunk))
            if effective_date is not None and latest_effective_date is not None:
                if effective_date == latest_effective_date:
                    version_adjustment = 0.04
                elif effective_date < latest_effective_date:
                    version_adjustment = -0.08

            relevance_score = max(
                0.0,
                min(
                    1.0,
                    (chunk.vector_score * 0.70)
                    + (lexical_overlap * 0.30)
                    + section_adjustment
                    + version_adjustment
                    + _stale_adjustment(chunk),
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
