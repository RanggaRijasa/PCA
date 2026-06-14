"""User context used by permission-aware retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Literal


UserRole = Literal["viewer", "staff", "manager", "admin"]


@dataclass(frozen=True)
class UserContext:
    id: str
    role: UserRole
    department: str
    name: str = "Local MVP User"
    username: str = ""
    email: str = ""
    allowed_restricted_document_ids: FrozenSet[str] = field(
        default_factory=frozenset
    )
