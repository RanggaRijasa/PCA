#!/usr/bin/env python3
"""Safely import the synthetic Private Company Assistant test corpus."""

from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
from typing import Dict, Optional
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZIP_NAME = "company_assistant_test_corpus.zip"
CORPUS_DIR_NAME = "company_assistant_test_corpus"
DOCUMENT_FOLDERS = ("valid_docs", "restricted_docs", "edge_cases", "prompt_injection")
REQUIRED_PATHS = (
    "README_TEST_CORPUS.md",
    "manifest.json",
    "metadata/document_metadata.csv",
    "eval/test_questions.csv",
    *DOCUMENT_FOLDERS,
)
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MIN_PRODUCTION_QUESTIONS = 50


class CorpusImportError(RuntimeError):
    """Raised when the archive cannot be imported safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def locate_zip(project_root: Path = PROJECT_ROOT) -> Path:
    roots = (project_root, project_root.parent)
    candidates = []
    for root in roots:
        candidates.extend(
            (
                root / ZIP_NAME,
                root / "downloads" / ZIP_NAME,
                root / "data" / ZIP_NAME,
            )
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    locations = "\n".join(f"- {path}" for path in candidates[:3])
    raise CorpusImportError(
        f"Could not find {ZIP_NAME}. Place it in one of these project locations:\n"
        f"{locations}"
    )


def _safe_member_path(info: zipfile.ZipInfo, destination: Path) -> Path:
    member = PurePosixPath(info.filename)
    if (
        member.is_absolute()
        or ".." in member.parts
        or "\\" in info.filename
        or not member.parts
        or member.parts[0] != CORPUS_DIR_NAME
    ):
        raise CorpusImportError(f"Unsafe or unexpected ZIP path: {info.filename}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise CorpusImportError(f"Symbolic links are not allowed in the corpus ZIP: {info.filename}")
    target = (destination / Path(*member.parts)).resolve()
    destination_root = destination.resolve()
    if target != destination_root and destination_root not in target.parents:
        raise CorpusImportError(f"ZIP path escapes the corpus directory: {info.filename}")
    return target


def extract_archive(zip_path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
            raise CorpusImportError("The corpus archive exceeds the 100 MB extraction limit.")
        targets = [(info, _safe_member_path(info, destination)) for info in infos]
        for info, target in targets:
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    return destination / CORPUS_DIR_NAME


def validate_corpus(corpus_root: Path) -> Dict[str, object]:
    missing = [item for item in REQUIRED_PATHS if not (corpus_root / item).exists()]
    if missing:
        raise CorpusImportError(
            "The extracted corpus is incomplete. Missing: " + ", ".join(missing)
        )

    try:
        manifest = json.loads((corpus_root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusImportError(f"Could not read manifest.json: {exc}") from exc
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise CorpusImportError("manifest.json does not contain a non-empty documents list.")

    metadata_path = corpus_root / "metadata" / "document_metadata.csv"
    with metadata_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(documents):
        raise CorpusImportError(
            f"Metadata row count ({len(rows)}) does not match manifest documents ({len(documents)})."
        )
    for row in rows:
        relative_path = str(row.get("relative_path", "")).strip()
        expected_hash = str(row.get("sha256", "")).strip().lower()
        source = corpus_root / relative_path
        if not relative_path or not source.is_file():
            raise CorpusImportError(f"Metadata references a missing document: {relative_path or '<empty>'}")
        if expected_hash and _sha256(source) != expected_hash:
            raise CorpusImportError(f"SHA256 mismatch for {relative_path}.")
    return {"document_count": len(rows), "manifest": manifest}


def _copy_if_changed(source: Path, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and _sha256(source) == _sha256(destination):
        return False
    shutil.copy2(source, destination)
    return True


def _copy_documents(corpus_root: Path, raw_destination: Path) -> tuple[int, int]:
    copied = 0
    unchanged = 0
    for folder_name in DOCUMENT_FOLDERS:
        source_root = corpus_root / folder_name
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            destination = raw_destination / folder_name / source.relative_to(source_root)
            if _copy_if_changed(source, destination):
                copied += 1
            else:
                unchanged += 1
    return copied, unchanged


def _backup_path(backup_dir: Path, target: Path, timestamp: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    candidate = backup_dir / f"{timestamp}-{target.name}"
    suffix = 1
    while candidate.exists():
        candidate = backup_dir / f"{timestamp}-{suffix}-{target.name}"
        suffix += 1
    return candidate


def _replace_with_backup(
    source: Path,
    target: Path,
    backup_dir: Path,
    timestamp: str,
) -> tuple[bool, Optional[Path]]:
    if target.is_file() and _sha256(source) == _sha256(target):
        return False, None
    backup = None
    if target.is_file():
        backup = _backup_path(backup_dir, target, timestamp)
        shutil.copy2(target, backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True, backup


def _starter_expected_answers(questions_path: Path) -> bytes:
    with questions_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["id", "expected_answer", "review_notes"])
    writer.writeheader()
    for row in rows:
        behavior = str(row.get("expected_behavior", "")).strip()
        keywords = str(row.get("expected_answer_keywords", "")).strip()
        expected = (
            "The assistant should refuse this request."
            if behavior == "refuse"
            else f"Expected concepts: {keywords}"
        )
        writer.writerow(
            {
                "id": row.get("id", ""),
                "expected_answer": expected,
                "review_notes": "Starter generated from synthetic corpus fields; review manually.",
            }
        )
    return output.getvalue().encode("utf-8")

def _question_count(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _should_preserve_production_eval(source: Path, target: Path) -> bool:
    return (
        _question_count(target) >= MIN_PRODUCTION_QUESTIONS
        and _question_count(source) < MIN_PRODUCTION_QUESTIONS
    )


def _write_bytes_with_backup(
    content: bytes,
    target: Path,
    backup_dir: Path,
    timestamp: str,
) -> tuple[bool, Optional[Path]]:
    if target.is_file() and target.read_bytes() == content:
        return False, None
    backup = None
    if target.is_file():
        backup = _backup_path(backup_dir, target, timestamp)
        shutil.copy2(target, backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return True, backup


def import_corpus(
    project_root: Path = PROJECT_ROOT,
    zip_path: Optional[Path] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, object]:
    project_root = project_root.resolve()
    archive_path = (zip_path or locate_zip(project_root)).resolve()
    imported_root = extract_archive(archive_path, project_root / "data" / "test_corpus")
    validation = validate_corpus(imported_root)

    copied, unchanged = _copy_documents(
        imported_root, project_root / "data" / "raw" / "test_corpus"
    )
    metadata_changed = _copy_if_changed(
        imported_root / "metadata" / "document_metadata.csv",
        project_root / "data" / "metadata" / "document_metadata.csv",
    )

    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    eval_root = project_root / "eval"
    backup_dir = eval_root / "backups"
    imported_questions = imported_root / "eval" / "test_questions.csv"
    active_questions = eval_root / "test_questions.csv"
    preserve_production_eval = _should_preserve_production_eval(
        imported_questions,
        active_questions,
    )
    if preserve_production_eval:
        questions_changed = False
        questions_backup = None
        expected_changed = False
        expected_backup = None
        expected_generated = False
    else:
        questions_changed, questions_backup = _replace_with_backup(
            imported_questions,
            active_questions,
            backup_dir,
            stamp,
        )
        corpus_expected = imported_root / "eval" / "expected_answers.csv"
        if corpus_expected.is_file():
            expected_changed, expected_backup = _replace_with_backup(
                corpus_expected,
                eval_root / "expected_answers.csv",
                backup_dir,
                stamp,
            )
            expected_generated = False
        else:
            expected_changed, expected_backup = _write_bytes_with_backup(
                _starter_expected_answers(imported_questions),
                eval_root / "expected_answers.csv",
                backup_dir,
                stamp,
            )
            expected_generated = True

    return {
        "archive": archive_path,
        "corpus_root": imported_root,
        "document_count": validation["document_count"],
        "documents_copied": copied,
        "documents_unchanged": unchanged,
        "metadata_changed": metadata_changed,
        "questions_changed": questions_changed,
        "questions_backup": questions_backup,
        "expected_changed": expected_changed,
        "expected_backup": expected_backup,
        "expected_generated": expected_generated,
        "production_eval_preserved": preserve_production_eval,
    }


def main() -> int:
    try:
        summary = import_corpus()
    except (CorpusImportError, OSError, zipfile.BadZipFile) as exc:
        print(f"Test corpus import failed: {exc}", file=sys.stderr)
        return 1

    print("Synthetic test corpus import complete.")
    print(f"Archive: {summary['archive']}")
    print(f"Extracted corpus: {summary['corpus_root']}")
    print(f"Validated documents: {summary['document_count']}")
    print(
        f"Raw document copies: {summary['documents_copied']} updated, "
        f"{summary['documents_unchanged']} unchanged"
    )
    print(
        "Metadata CSV: "
        + ("updated" if summary["metadata_changed"] else "already current")
    )
    if summary["production_eval_preserved"]:
        print("Evaluation questions: preserved existing 50+ production set")
    else:
        print(
            "Evaluation questions: "
            + ("updated" if summary["questions_changed"] else "already current")
        )
    if summary["questions_backup"]:
        print(f"Previous questions backup: {summary['questions_backup']}")
    if summary["expected_generated"]:
        expected_status = (
            "starter generated" if summary["expected_changed"] else "starter already current"
        )
    else:
        expected_status = (
            "copied from corpus" if summary["expected_changed"] else "already current"
        )
    print(f"Expected answers: {expected_status}")
    if summary["expected_backup"]:
        print(f"Previous expected answers backup: {summary['expected_backup']}")
    print("Next: .venv/bin/python scripts/init_db.py")
    print("Then: .venv/bin/python ingestion/ingest_folder.py")
    if summary["production_eval_preserved"]:
        print("Evaluation: .venv/bin/python eval/run_eval.py")
    else:
        print("Starter evaluation: .venv/bin/python eval/run_eval.py --allow-small-set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
