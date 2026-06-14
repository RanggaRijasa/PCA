"""Persistent ChromaDB storage for precomputed local embeddings."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import chromadb


class ChromaIndexer:
    """Store chunk text, metadata, and externally generated embeddings."""

    def __init__(self, path: Path, collection_name: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _metadata(chunk: Dict[str, object]) -> Dict[str, object]:
        keys = [
            "document_id",
            "document_version_id",
            "chunk_index",
            "title",
            "source_file",
            "page",
            "section",
            "department",
            "access_level",
            "version",
            "effective_date",
            "token_count",
        ]
        return {
            key: value
            for key in keys
            if (value := chunk.get(key)) is not None
        }

    def upsert(
        self,
        chunks: Sequence[Dict[str, object]],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts do not match.")
        self.collection.upsert(
            ids=[str(chunk["vector_id"]) for chunk in chunks],
            embeddings=[list(embedding) for embedding in embeddings],
            documents=[str(chunk["content"]) for chunk in chunks],
            metadatas=[self._metadata(chunk) for chunk in chunks],
        )

    def delete(self, vector_ids: Iterable[str]) -> None:
        ids = list(vector_ids)
        if ids:
            self.collection.delete(ids=ids)

    def count(self) -> int:
        return int(self.collection.count())

    def peek(self, limit: int = 10) -> Dict[str, object]:
        return self.collection.peek(limit=limit)
