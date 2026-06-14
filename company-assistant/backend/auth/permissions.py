"""Build Chroma metadata filters before any document retrieval occurs."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Iterable, List, Optional

from backend.auth.models import UserContext, UserRole


ROLE_ACCESS_LEVELS: Dict[UserRole, tuple[str, ...]] = {
    "viewer": ("public_internal",),
    "staff": ("public_internal", "staff"),
    "manager": ("public_internal", "staff", "manager"),
    "admin": ("public_internal", "staff", "manager", "admin"),
}

_EXPLICIT_LEVEL_REQUEST = re.compile(
    r"\b(viewer|staff|manager|admin)[ -]only\b|\brestricted\b",
    re.I,
)
_ACCESS_RANK = {"viewer": 0, "staff": 1, "manager": 2, "admin": 3}


@dataclass(frozen=True)
class PermissionFilter:
    role: UserRole
    allowed_access_levels: tuple[str, ...]
    restricted_document_ids: tuple[str, ...]
    department: Optional[str]
    document_ids: tuple[str, ...]
    chroma_where: Dict[str, object]

    def to_audit_dict(self) -> Dict[str, object]:
        return {
            "role": self.role,
            "allowed_access_levels": list(self.allowed_access_levels),
            "restricted_document_ids": list(self.restricted_document_ids),
            "department": self.department,
            "document_ids": list(self.document_ids),
            "chroma_where": self.chroma_where,
        }


def allowed_access_levels(role: UserRole) -> tuple[str, ...]:
    try:
        return ROLE_ACCESS_LEVELS[role]
    except KeyError as exc:
        raise ValueError(f"Unsupported role '{role}'.") from exc


def requests_unauthorized_access(question: str, user: UserContext) -> bool:
    """Reject explicit requests for a higher or restricted access class."""

    match = _EXPLICIT_LEVEL_REQUEST.search(question)
    if not match:
        return False
    requested = (match.group(1) or "restricted").lower()
    if requested == "restricted":
        return True
    requested_role = "viewer" if requested == "viewer" else requested
    return _ACCESS_RANK[requested_role] > _ACCESS_RANK[user.role]


def build_permission_filter(
    user: UserContext,
    department: Optional[str] = None,
    document_ids: Optional[Iterable[str]] = None,
) -> PermissionFilter:
    """Return a filter that excludes unauthorized chunks inside ChromaDB."""

    standard_levels = allowed_access_levels(user.role)
    restricted_ids = tuple(sorted(user.allowed_restricted_document_ids))
    scoped_document_ids = tuple(sorted(set(document_ids or [])))

    access_clauses: List[Dict[str, object]] = [
        {"access_level": {"$in": list(standard_levels)}}
    ]
    if restricted_ids:
        access_clauses.append(
            {
                "$and": [
                    {"access_level": {"$eq": "restricted"}},
                    {"document_id": {"$in": list(restricted_ids)}},
                ]
            }
        )

    access_filter: Dict[str, object]
    if len(access_clauses) == 1:
        access_filter = access_clauses[0]
    else:
        access_filter = {"$or": access_clauses}

    filters: List[Dict[str, object]] = [access_filter]
    if department and department.lower() != "all":
        filters.append({"department": {"$eq": department}})
    if scoped_document_ids:
        filters.append({"document_id": {"$in": list(scoped_document_ids)}})

    chroma_where = filters[0] if len(filters) == 1 else {"$and": filters}
    return PermissionFilter(
        role=user.role,
        allowed_access_levels=standard_levels,
        restricted_document_ids=restricted_ids,
        department=department if department and department.lower() != "all" else None,
        document_ids=scoped_document_ids,
        chroma_where=chroma_where,
    )
