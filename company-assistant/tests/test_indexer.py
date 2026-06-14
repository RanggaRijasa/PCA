"""Chroma persistence checks using precomputed dummy embeddings."""

from pathlib import Path

from ingestion.indexer import ChromaIndexer


def test_chroma_stores_precomputed_embeddings_and_metadata(
    tmp_path: Path,
) -> None:
    indexer = ChromaIndexer(tmp_path / "chroma", "test_collection")
    chunk = {
        "chunk_id": "chunk_1",
        "vector_id": "chunk_1",
        "document_id": "doc_1",
        "document_version_id": "docver_1",
        "chunk_index": 0,
        "content": "Employees may work remotely.",
        "page": 3,
        "section": "Eligibility",
        "title": "Remote Work Policy",
        "source_file": "remote.md",
        "department": "HR",
        "access_level": "staff",
        "version": "v1.0",
        "effective_date": "2026-01-01",
        "token_count": 5,
    }

    indexer.upsert([chunk], [[0.1, 0.2, 0.3]])
    result = indexer.peek(limit=1)

    assert indexer.count() == 1
    assert result["ids"] == ["chunk_1"]
    assert result["metadatas"][0]["access_level"] == "staff"
    assert result["metadatas"][0]["section"] == "Eligibility"
