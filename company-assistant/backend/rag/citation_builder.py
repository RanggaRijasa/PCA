"""Create deterministic text and API citations from retrieved chunks."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from backend.rag.retriever import RetrievedChunk


def citation_text(chunk: RetrievedChunk, rank: int) -> str:
    details = [chunk.title, chunk.source_file]
    if chunk.page is not None:
        details.append(f"page {chunk.page}")
    if chunk.section:
        details.append(f"section {chunk.section}")
    details.append(f"version {chunk.version}")
    if chunk.effective_date:
        details.append(f"effective {chunk.effective_date}")
    return f"{rank}. " + ", ".join(details)


def build_sources_section(chunks: Iterable[RetrievedChunk]) -> str:
    lines = [citation_text(chunk, rank) for rank, chunk in enumerate(chunks, 1)]
    return "\n".join(lines) if lines else "None."


def _file_type(source_file: str) -> str:
    suffix = Path(source_file).suffix.lower().lstrip(".")
    return suffix if suffix in {"pdf", "docx", "txt", "md"} else "txt"


def build_api_sources(chunks: Iterable[RetrievedChunk]) -> List[Dict[str, object]]:
    sources: List[Dict[str, object]] = []
    for rank, chunk in enumerate(chunks, start=1):
        sources.append(
            {
                "id": chunk.id,
                "documentId": chunk.document_id,
                "chunkId": chunk.id,
                "title": chunk.title,
                "fileName": chunk.source_file,
                "fileType": _file_type(chunk.source_file),
                "department": chunk.department,
                "accessLevel": chunk.access_level,
                "page": chunk.page,
                "section": chunk.section,
                "version": chunk.version,
                "effectiveDate": chunk.effective_date,
                "snippet": chunk.content[:320].strip(),
                "relevanceScore": round(chunk.relevance_score, 4),
                "citationRank": rank,
            }
        )
    return sources
