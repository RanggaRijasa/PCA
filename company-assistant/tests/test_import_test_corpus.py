"""Synthetic corpus import safety and idempotence checks."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from ingestion.ingest_folder import _discover_files
from scripts.import_test_corpus import CorpusImportError, import_corpus


def _build_archive(path: Path, unsafe_member: str | None = None) -> None:
    document = b"# Synthetic Policy\nSafe dummy content.\n"
    digest = hashlib.sha256(document).hexdigest()
    metadata_headers = [
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
        "notes",
        "sha256",
    ]
    metadata_row = [
        "policy.md",
        "valid_docs/policy.md",
        "Synthetic Policy",
        "General",
        "public_internal",
        "policy",
        "Test Owner",
        "v1.0",
        "2026-06-01",
        "",
        "",
        digest,
    ]
    metadata_text = ",".join(metadata_headers) + "\n" + ",".join(metadata_row) + "\n"
    questions = (
        "id,category,user_role,question,expected_behavior,expected_source,expected_answer_keywords\n"
        "Q001,direct,viewer,What is synthetic?,answer,policy.md,synthetic\n"
    )
    manifest = {
        "document_count": 1,
        "documents": [
            {
                "file_name": "policy.md",
                "relative_path": "valid_docs/policy.md",
                "sha256": digest,
            }
        ],
    }
    root = "company_assistant_test_corpus"
    with zipfile.ZipFile(path, "w") as archive:
        for folder in (
            "valid_docs/",
            "restricted_docs/",
            "edge_cases/",
            "prompt_injection/",
            "metadata/",
            "eval/",
        ):
            archive.writestr(f"{root}/{folder}", b"")
        archive.writestr(f"{root}/README_TEST_CORPUS.md", "# Synthetic\n")
        archive.writestr(f"{root}/manifest.json", json.dumps(manifest))
        archive.writestr(f"{root}/metadata/document_metadata.csv", metadata_text)
        archive.writestr(f"{root}/eval/test_questions.csv", questions)
        archive.writestr(f"{root}/valid_docs/policy.md", document)
        if unsafe_member:
            archive.writestr(unsafe_member, "unsafe")


def test_import_corpus_backs_up_eval_and_is_idempotent(tmp_path: Path) -> None:
    project = tmp_path / "company-assistant"
    (project / "eval").mkdir(parents=True)
    (project / "eval" / "test_questions.csv").write_text("old questions\n", encoding="utf-8")
    (project / "eval" / "expected_answers.csv").write_text("old answers\n", encoding="utf-8")
    archive = tmp_path / "company_assistant_test_corpus.zip"
    _build_archive(archive)

    first = import_corpus(project, archive, timestamp="20260614-120000")
    second = import_corpus(project, archive, timestamp="20260614-120001")

    assert first["document_count"] == 1
    assert first["documents_copied"] == 1
    assert first["questions_backup"].is_file()
    assert first["expected_backup"].is_file()
    assert (project / "data/raw/test_corpus/valid_docs/policy.md").is_file()
    assert (project / "data/metadata/document_metadata.csv").is_file()
    assert second["documents_copied"] == 0
    assert second["questions_changed"] is False
    assert second["expected_changed"] is False


def test_import_preserves_existing_production_eval_for_starter_corpus(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company-assistant"
    (project / "eval").mkdir(parents=True)
    production_questions = "id,category,user_role,question,expected_behavior,expected_source,expected_answer_keywords\n" + "".join(
        f"Q{index:03d},direct-answer,staff,Question {index}?,answer,policy.md,safe\n"
        for index in range(1, 51)
    )
    production_expected = "id,expected_answer,review_notes\n" + "".join(
        f"Q{index:03d},Expected answer {index},Production case.\n"
        for index in range(1, 51)
    )
    (project / "eval" / "test_questions.csv").write_text(
        production_questions,
        encoding="utf-8",
    )
    (project / "eval" / "expected_answers.csv").write_text(
        production_expected,
        encoding="utf-8",
    )
    archive = tmp_path / "company_assistant_test_corpus.zip"
    _build_archive(archive)

    result = import_corpus(project, archive, timestamp="20260614-130000")

    assert result["production_eval_preserved"] is True
    assert result["questions_changed"] is False
    assert result["expected_changed"] is False
    assert (project / "eval" / "test_questions.csv").read_text(
        encoding="utf-8"
    ) == production_questions


def test_import_rejects_zip_path_traversal(tmp_path: Path) -> None:
    project = tmp_path / "company-assistant"
    archive = tmp_path / "company_assistant_test_corpus.zip"
    _build_archive(archive, unsafe_member="company_assistant_test_corpus/../escape.txt")

    with pytest.raises(CorpusImportError, match="Unsafe or unexpected ZIP path"):
        import_corpus(project, archive)


def test_nested_discovery_excludes_admin_upload_staging(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    corpus = raw / "test_corpus" / "valid_docs" / "policy.md"
    upload = raw / "uploads" / "doc_1" / "unapproved.md"
    corpus.parent.mkdir(parents=True)
    upload.parent.mkdir(parents=True)
    corpus.write_text("safe", encoding="utf-8")
    upload.write_text("not approved", encoding="utf-8")

    discovered = _discover_files(raw)

    assert discovered == [corpus]
