"""Permission metadata sidecar validation checks."""

import json
import csv
from pathlib import Path

import pytest

from ingestion.file_validator import calculate_sha256, validate_file
from ingestion.metadata import MetadataValidationError, load_metadata


def test_metadata_sidecar_is_required(tmp_path: Path) -> None:
    source = tmp_path / "policy.md"
    source.write_text("# Policy\nText", encoding="utf-8")
    validated = validate_file(source, max_size_mb=1)

    with pytest.raises(MetadataValidationError, match="sidecar is missing"):
        load_metadata(validated, embedding_model="embed-model")


def test_metadata_preserves_access_and_version(tmp_path: Path) -> None:
    source = tmp_path / "policy.md"
    source.write_text("# Policy\nText", encoding="utf-8")
    sidecar = source.with_suffix(".metadata.json")
    sidecar.write_text(
        json.dumps(
            {
                "title": "Policy",
                "document_type": "policy",
                "department": "HR",
                "access_level": "manager",
                "owner": "HR",
                "version": "v2.0",
                "effective_date": "2026-01-01",
                "expiry_date": None,
            }
        ),
        encoding="utf-8",
    )

    metadata = load_metadata(
        validate_file(source, max_size_mb=1),
        embedding_model="embed-model",
    )

    assert metadata.access_level == "manager"
    assert metadata.version == "v2.0"
    assert metadata.effective_date == "2026-01-01"


def test_metadata_csv_maps_nested_corpus_file(tmp_path: Path) -> None:
    raw_root = tmp_path / "data" / "raw"
    source = raw_root / "test_corpus" / "valid_docs" / "policy.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Policy\nSynthetic text", encoding="utf-8")
    metadata_csv = tmp_path / "data" / "metadata" / "document_metadata.csv"
    metadata_csv.parent.mkdir(parents=True)
    with metadata_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file_name",
                "relative_path",
                "title",
                "department",
                "access_level",
                "document_type",
                "owner",
                "version",
                "effective_date",
                "expiry_date",
                "sha256",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "file_name": source.name,
                "relative_path": "valid_docs/policy.md",
                "title": "Synthetic Policy",
                "department": "HR",
                "access_level": "staff",
                "document_type": "policy",
                "owner": "HR",
                "version": "v1.0",
                "effective_date": "2026-06-01",
                "expiry_date": "",
                "sha256": calculate_sha256(source),
            }
        )

    metadata = load_metadata(
        validate_file(source, max_size_mb=1),
        embedding_model="embed-model",
        metadata_csv_path=metadata_csv,
        raw_root=raw_root,
    )

    assert metadata.title == "Synthetic Policy"
    assert metadata.source_file == "policy.md"
    assert metadata.access_level == "staff"


def test_metadata_csv_rejects_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "policy.md"
    source.write_text("# Policy\nSynthetic text", encoding="utf-8")
    metadata_csv = tmp_path / "document_metadata.csv"
    metadata_csv.write_text(
        "file_name,relative_path,title,department,access_level,document_type,owner,version,effective_date,expiry_date,sha256\n"
        "policy.md,valid_docs/policy.md,Policy,HR,staff,policy,HR,v1.0,2026-01-01,,wrong\n",
        encoding="utf-8",
    )

    with pytest.raises(MetadataValidationError, match="SHA256 does not match"):
        load_metadata(
            validate_file(source, max_size_mb=1),
            embedding_model="embed-model",
            metadata_csv_path=metadata_csv,
        )
