"""Permission-filtered Chroma retrieval using local query embeddings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import chromadb

from backend.auth.models import UserContext
from backend.auth.permissions import PermissionFilter, build_permission_filter


class QueryEmbedder(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        ...


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    document_id: str
    document_version_id: str
    content: str
    title: str
    source_file: str
    department: str
    access_level: str
    version: str
    page: Optional[int]
    section: Optional[str]
    effective_date: Optional[str]
    vector_score: float
    distance: float
    lexical_overlap: float = 0.0
    relevance_score: float = 0.0


@dataclass(frozen=True)
class RetrievalResult:
    chunks: List[RetrievedChunk]
    permission_filter: PermissionFilter


def normalize_query(question: str) -> str:
    return " ".join(question.split())


class VectorRetriever:
    """Query only the chunks authorized by the supplied user context."""

    def __init__(
        self,
        path: Path,
        collection_name: str,
        embedder: QueryEmbedder,
        sqlite_path: Optional[Path] = None,
    ) -> None:
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = embedder
        self.sqlite_path = sqlite_path

    def _source_document_ids(self, source_filter: str) -> Optional[List[str]]:
        if source_filter == "all" or self.sqlite_path is None:
            return None
        connection = sqlite3.connect(str(self.sqlite_path))
        try:
            if source_filter == "policies":
                rows = connection.execute(
                    "SELECT id FROM documents WHERE document_type = 'policy' AND status = 'indexed'"
                ).fetchall()
            elif source_filter == "handbooks":
                rows = connection.execute(
                    """
                    SELECT id FROM documents
                    WHERE status = 'indexed'
                      AND (lower(title) LIKE '%handbook%'
                           OR lower(source_file) LIKE '%handbook%')
                    """
                ).fetchall()
            else:
                return None
        finally:
            connection.close()
        return [str(row[0]) for row in rows]

    def search(
        self,
        question: str,
        user: UserContext,
        top_k: int = 20,
        department_filter: str = "all",
        source_filter: str = "all",
    ) -> RetrievalResult:
        normalized = normalize_query(question)
        document_ids = self._source_document_ids(source_filter)
        permission_filter = build_permission_filter(
            user,
            department=department_filter,
            document_ids=document_ids,
        )
        if document_ids == [] or self.collection.count() == 0:
            return RetrievalResult([], permission_filter)

        embeddings = self.embedder.embed_texts([normalized])
        if not embeddings:
            return RetrievalResult([], permission_filter)
        result = self.collection.query(
            query_embeddings=embeddings,
            n_results=min(top_k, self.collection.count()),
            where=permission_filter.chroma_where,
            include=["documents", "metadatas", "distances"],
        )

        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        chunks: List[RetrievedChunk] = []
        for chunk_id, content, metadata, distance_value in zip(
            ids, documents, metadatas, distances
        ):
            if content is None or metadata is None or distance_value is None:
                continue
            distance = float(distance_value)
            vector_score = max(0.0, min(1.0, 1.0 - distance))
            chunks.append(
                RetrievedChunk(
                    id=str(chunk_id),
                    document_id=str(metadata.get("document_id", "")),
                    document_version_id=str(
                        metadata.get("document_version_id", "")
                    ),
                    content=str(content),
                    title=str(metadata.get("title", "Untitled document")),
                    source_file=str(metadata.get("source_file", "unknown")),
                    department=str(metadata.get("department", "Unknown")),
                    access_level=str(metadata.get("access_level", "restricted")),
                    version=str(metadata.get("version", "unknown")),
                    page=(
                        int(metadata["page"])
                        if metadata.get("page") is not None
                        else None
                    ),
                    section=(
                        str(metadata["section"])
                        if metadata.get("section") is not None
                        else None
                    ),
                    effective_date=(
                        str(metadata["effective_date"])
                        if metadata.get("effective_date") is not None
                        else None
                    ),
                    vector_score=vector_score,
                    distance=distance,
                    relevance_score=vector_score,
                )
            )
        return RetrievalResult(chunks, permission_filter)
