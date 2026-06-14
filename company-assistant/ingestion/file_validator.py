"""Validate local source files before parsing or indexing."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import zipfile


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class FileValidationError(ValueError):
    """Raised when a source file cannot enter the ingestion pipeline."""


@dataclass(frozen=True)
class ValidatedFile:
    path: Path
    extension: str
    size_bytes: int
    sha256: str


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileValidationError(
            f"Unsupported file type '{extension or 'none'}'. Allowed types: {allowed}."
        )
    return extension


def _validate_content(path: Path, extension: str) -> None:
    if extension == ".pdf":
        if not path.read_bytes()[:5].startswith(b"%PDF-"):
            raise FileValidationError("The uploaded file is not a valid PDF.")
        return
    if extension == ".docx":
        if not zipfile.is_zipfile(path):
            raise FileValidationError("The uploaded file is not a valid DOCX archive.")
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise FileValidationError("The uploaded file is not a valid DOCX document.")
        return
    try:
        path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileValidationError(
            "Text and Markdown uploads must use UTF-8 encoding."
        ) from exc


def validate_file(path: Path, max_size_mb: int) -> ValidatedFile:
    if not path.exists():
        raise FileValidationError(f"File does not exist: {path}")
    if not path.is_file():
        raise FileValidationError(f"Path is not a regular file: {path}")

    extension = validate_extension(path.name)

    size_bytes = path.stat().st_size
    if size_bytes == 0:
        raise FileValidationError("File is empty.")
    max_size_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise FileValidationError(
            f"File is {size_bytes} bytes, exceeding the {max_size_mb} MB limit."
        )

    _validate_content(path, extension)

    return ValidatedFile(
        path=path.resolve(),
        extension=extension,
        size_bytes=size_bytes,
        sha256=calculate_sha256(path),
    )
