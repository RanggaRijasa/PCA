"""Section-aware token chunking checks."""

from ingestion.chunker import build_chunks
from ingestion.metadata import DocumentMetadata
from ingestion.parsers import ParsedSection


def _metadata() -> DocumentMetadata:
    return DocumentMetadata(
        document_id="doc_test",
        document_version_id="docver_test",
        title="Test Policy",
        source_file="test.md",
        file_hash="hash",
        document_type="policy",
        department="HR",
        access_level="staff",
        owner="People Operations",
        version="v1.0",
        effective_date="2026-01-01",
        expiry_date=None,
        source_path="/tmp/test.md",
        file_size_bytes=100,
        embedding_model="test-embed",
    )


def test_chunks_split_within_sections_and_preserve_provenance() -> None:
    sections = [
        ParsedSection(
            section="Eligibility",
            page=3,
            text=" ".join(f"word{index}" for index in range(25)),
        ),
        ParsedSection(
            section="Approval",
            page=4,
            text="Manager approval is required.",
        ),
    ]
    chunks = build_chunks(
        sections,
        metadata=_metadata(),
        target_tokens=10,
        overlap_tokens=2,
        max_tokens=10,
    )

    assert len(chunks) == 4
    assert chunks[0]["section"] == "Eligibility"
    assert chunks[-1]["section"] == "Approval"
    assert chunks[0]["page"] == 3
    assert chunks[0]["title"] == "Test Policy"
    assert chunks[0]["source_file"] == "test.md"
    assert chunks[0]["version"] == "v1.0"
    assert chunks[0]["department"] == "HR"
    assert chunks[0]["access_level"] == "staff"
    assert chunks[0]["effective_date"] == "2026-01-01"
    assert all(int(chunk["token_count"]) <= 10 for chunk in chunks)
