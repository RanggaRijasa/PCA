"""Validate and normalize user questions before retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from backend.safety.prompt_injection import prompt_injection_reason


_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|api[_ -]?key|secret|token|access[_ -]?token|refresh[_ -]?token|authorization)\b"
    r"(\s*[:=]\s*|\s+is\s+)([^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.S,
)


@dataclass(frozen=True)
class InputCheckResult:
    normalized_question: str
    refusal_reason: Optional[str] = None


def redact_sensitive_text(text: str) -> str:
    """Remove common credential-shaped values before persistence or display."""

    redacted = _PRIVATE_KEY.sub("[REDACTED PRIVATE KEY]", text)
    redacted = _BEARER_TOKEN.sub("Bearer [REDACTED]", redacted)
    redacted = _JWT.sub("[REDACTED TOKEN]", redacted)
    return _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)


def check_user_input(question: str) -> InputCheckResult:
    normalized = re.sub(r"\s+", " ", question).strip()
    if not normalized:
        return InputCheckResult(normalized, "empty_question")
    return InputCheckResult(normalized, prompt_injection_reason(normalized))
