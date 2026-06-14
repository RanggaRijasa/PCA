"""Section-first chunking with token windows and overlap."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Match
from uuid import NAMESPACE_URL, uuid5

from ingestion.metadata import DocumentMetadata
from ingestion.parsers import ParsedSection


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class ChunkingError(ValueError):
    """Raised when chunk settings or source sections are invalid."""


def count_tokens(text: str) -> int:
    return sum(1 for _ in TOKEN_PATTERN.finditer(text))


def _token_windows(
    text: str,
    target_tokens: int,
    overlap_tokens: int,
    max_tokens: int,
) -> Iterable[str]:
    matches: List[Match[str]] = list(TOKEN_PATTERN.finditer(text))
    if not matches:
        return
    if len(matches) <= max_tokens:
        yield text.strip()
        return

    window_size = min(target_tokens, max_tokens)
    step = window_size - overlap_tokens
    if step <= 0:
        raise ChunkingError("Chunk overlap must be smaller than the target size.")

    start_token = 0
    while start_token < len(matches):
        end_token = min(start_token + window_size, len(matches))
        start_character = matches[start_token].start()
        end_character = matches[end_token - 1].end()
        window = text[start_character:end_character].strip()
        if window:
            yield window
        if end_token == len(matches):
            break
        start_token += step


def build_chunks(
    sections: Iterable[ParsedSection],
    metadata: DocumentMetadata,
    target_tokens: int,
    overlap_tokens: int,
    max_tokens: int,
) -> List[Dict[str, object]]:
    if target_tokens <= 0 or max_tokens <= 0:
        raise ChunkingError("Chunk token sizes must be positive.")
    if target_tokens > max_tokens:
        raise ChunkingError("CHUNK_TARGET_TOKENS cannot exceed CHUNK_MAX_TOKENS.")

    chunks: List[Dict[str, object]] = []
    for section in sections:
        for content in _token_windows(
            section.text,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
            max_tokens=max_tokens,
        ):
            chunk_index = len(chunks)
            chunk_id = (
                f"chunk_{uuid5(NAMESPACE_URL, metadata.document_version_id + ':' + str(chunk_index)).hex}"
            )
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "vector_id": chunk_id,
                    "document_id": metadata.document_id,
                    "document_version_id": metadata.document_version_id,
                    "chunk_index": chunk_index,
                    "content": content,
                    "page": section.page,
                    "section": section.section,
                    "title": metadata.title,
                    "source_file": metadata.source_file,
                    "department": metadata.department,
                    "access_level": metadata.access_level,
                    "version": metadata.version,
                    "effective_date": metadata.effective_date,
                    "token_count": count_tokens(content),
                }
            )

    if not chunks:
        raise ChunkingError("No non-empty chunks were created from the document.")
    return chunks
