"""Load and validate permission-aware document metadata sidecars."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from uuid import NAMESPACE_URL, uuid5

from ingestion.file_validator import ValidatedFile


ACCESS_LEVELS = {"public_internal", "staff", "manager", "admin", "restricted"}
DOCUMENT_TYPES = {"policy", "sop", "manual", "faq", "report", "other"}
REQUIRED_FIELDS = {
    "title",
    "document_type",
    "department",
    "access_level",
    "owner",
    "version",
    "effective_date",
}


class MetadataValidationError(ValueError):
    """Raised when required provenance or permission metadata is missing."""


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    document_version_id: str
    title: str
    source_file: str
    file_hash: str
    document_type: str
    department: str
    access_level: str
    owner: str
    version: str
    effective_date: Optional[str]
    expiry_date: Optional[str]
    source_path: str
    file_size_bytes: int
    embedding_model: str

    def to_record(self) -> Dict[str, object]:
        return asdict(self)


def _sidecar_path(path: Path) -> Path:
    candidates = [
        path.with_name(f"{path.name}.metadata.json"),
        path.with_suffix(".metadata.json"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    expected = " or ".join(candidate.name for candidate in candidates)
    raise MetadataValidationError(
        f"Required metadata sidecar is missing for '{path.name}'. Expected {expected}."
    )


def _metadata_rows(metadata_csv_path: Path) -> List[Dict[str, object]]:
    try:
        with metadata_csv_path.open(newline="", encoding="utf-8-sig") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except OSError as exc:
        raise MetadataValidationError(
            f"Could not read metadata CSV '{metadata_csv_path}': {exc}"
        ) from exc


def _csv_payload(
    validated_file: ValidatedFile,
    metadata_csv_path: Path,
    raw_root: Optional[Path],
) -> Dict[str, object]:
    rows = _metadata_rows(metadata_csv_path)
    source_relative = None
    if raw_root is not None:
        try:
            source_relative = validated_file.path.relative_to(raw_root.resolve()).as_posix()
        except ValueError:
            source_relative = None

    matches: List[Dict[str, object]] = []
    for row in rows:
        relative_path = str(row.get("relative_path", "")).strip().replace("\\", "/")
        file_name = str(row.get("file_name", "")).strip()
        relative_match = bool(
            source_relative
            and relative_path
            and (
                source_relative == relative_path
                or source_relative.endswith(f"/{relative_path}")
            )
        )
        if relative_match or file_name == validated_file.path.name:
            matches.append(row)

    exact_relative = [
        row
        for row in matches
        if source_relative
        and str(row.get("relative_path", "")).strip().replace("\\", "/")
        and (
            source_relative
            == str(row.get("relative_path", "")).strip().replace("\\", "/")
            or source_relative.endswith(
                "/" + str(row.get("relative_path", "")).strip().replace("\\", "/")
            )
        )
    ]
    selected = exact_relative or matches
    if not selected:
        raise MetadataValidationError(
            f"No metadata CSV row matches '{validated_file.path.name}'."
        )
    if len(selected) > 1:
        raise MetadataValidationError(
            f"Metadata CSV contains multiple matches for '{validated_file.path.name}'."
        )
    payload = selected[0]
    expected_hash = str(payload.get("sha256", "")).strip().lower()
    if expected_hash and expected_hash != validated_file.sha256:
        raise MetadataValidationError(
            f"Metadata CSV SHA256 does not match '{validated_file.path.name}'."
        )
    return payload


def _optional_date(payload: Dict[str, object], field: str) -> Optional[str]:
    value = payload.get(field)
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise MetadataValidationError(
            f"Metadata field '{field}' must use YYYY-MM-DD or null."
        ) from exc


def metadata_from_payload(
    validated_file: ValidatedFile,
    embedding_model: str,
    payload: Dict[str, object],
    *,
    source_file: Optional[str] = None,
) -> DocumentMetadata:
    if not isinstance(payload, dict):
        raise MetadataValidationError("Document metadata must be a JSON object.")

    missing = sorted(field for field in REQUIRED_FIELDS if field not in payload)
    if missing:
        raise MetadataValidationError(
            f"Document metadata is missing required fields: {', '.join(missing)}."
        )

    string_fields = [
        "title",
        "document_type",
        "department",
        "access_level",
        "owner",
        "version",
    ]
    for field in string_fields:
        if not str(payload.get(field, "")).strip():
            raise MetadataValidationError(f"Metadata field '{field}' cannot be empty.")

    document_type = str(payload["document_type"]).strip().lower()
    access_level = str(payload["access_level"]).strip().lower()
    if document_type not in DOCUMENT_TYPES:
        raise MetadataValidationError(
            f"Unsupported document_type '{document_type}'. "
            f"Allowed values: {', '.join(sorted(DOCUMENT_TYPES))}."
        )
    if access_level not in ACCESS_LEVELS:
        raise MetadataValidationError(
            f"Unsupported access_level '{access_level}'. "
            f"Allowed values: {', '.join(sorted(ACCESS_LEVELS))}."
        )
    if not embedding_model:
        raise MetadataValidationError("EMBED_MODEL must be configured in .env.")

    effective_date = _optional_date(payload, "effective_date")
    expiry_date = _optional_date(payload, "expiry_date")
    if effective_date is None:
        raise MetadataValidationError("Metadata field 'effective_date' is required.")
    if expiry_date and expiry_date < effective_date:
        raise MetadataValidationError(
            "Metadata field 'expiry_date' cannot be earlier than effective_date."
        )

    title = str(payload["title"]).strip()
    version = str(payload["version"]).strip()
    document_id = str(
        payload.get("document_id")
        or f"doc_{uuid5(NAMESPACE_URL, title.casefold()).hex}"
    )
    document_version_id = (
        f"docver_{uuid5(NAMESPACE_URL, document_id + ':' + validated_file.sha256).hex}"
    )
    return DocumentMetadata(
        document_id=document_id,
        document_version_id=document_version_id,
        title=title,
        source_file=source_file or validated_file.path.name,
        file_hash=validated_file.sha256,
        document_type=document_type,
        department=str(payload["department"]).strip(),
        access_level=access_level,
        owner=str(payload["owner"]).strip(),
        version=version,
        effective_date=effective_date,
        expiry_date=expiry_date,
        source_path=str(validated_file.path),
        file_size_bytes=validated_file.size_bytes,
        embedding_model=embedding_model,
    )


def load_metadata(
    validated_file: ValidatedFile,
    embedding_model: str,
    metadata_csv_path: Optional[Path] = None,
    raw_root: Optional[Path] = None,
) -> DocumentMetadata:
    try:
        sidecar = _sidecar_path(validated_file.path)
    except MetadataValidationError:
        if metadata_csv_path is None or not metadata_csv_path.is_file():
            raise
        payload = _csv_payload(validated_file, metadata_csv_path, raw_root)
    else:
        try:
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MetadataValidationError(
                f"Could not read metadata sidecar '{sidecar.name}': {exc}"
            ) from exc
    return metadata_from_payload(validated_file, embedding_model, payload)
