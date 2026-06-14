"""Citation text and API metadata must correspond to retrieved chunks."""

from backend.rag.citation_builder import build_api_sources, build_sources_section
from backend.rag.retriever import RetrievedChunk


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id="chunk_remote",
        document_id="doc_remote",
        document_version_id="docver_remote",
        content="Staff may work remotely with manager approval.",
        title="Remote Work Policy",
        source_file="remote_work.pdf",
        department="People",
        access_level="staff",
        version="2.1",
        page=3,
        section="Eligibility",
        effective_date="2026-05-01",
        vector_score=0.9,
        distance=0.1,
        lexical_overlap=1.0,
        relevance_score=0.93,
    )


def test_citation_contains_required_provenance() -> None:
    chunk = _chunk()
    text = build_sources_section([chunk])
    source = build_api_sources([chunk])[0]

    assert "Remote Work Policy" in text
    assert "remote_work.pdf" in text
    assert "page 3" in text
    assert "section Eligibility" in text
    assert "version 2.1" in text
    assert "effective 2026-05-01" in text
    assert source["chunkId"] == chunk.id
    assert source["version"] == "2.1"
    assert source["effectiveDate"] == "2026-05-01"
