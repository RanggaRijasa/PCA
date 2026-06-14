"""Conservative prompt-injection and secret-disclosure detection."""

from __future__ import annotations

import re
from typing import Optional


SECURITY_REFUSAL = (
    "I cannot provide hidden system instructions, credentials, or unauthorized "
    "company information."
)

_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|system)\s+instructions?\b", re.I),
    re.compile(r"\b(show|reveal|print|repeat|give)\b.{0,40}\bsystem prompt\b", re.I),
    re.compile(r"\b(show|reveal|print|list|give)\b.{0,40}\b(credentials?|passwords?|api keys?|tokens?)\b", re.I),
    re.compile(r"\b(reveal|show|list)\b.{0,40}\b(hidden|restricted|unauthorized)\b.{0,30}\b(documents?|files?|data)\b", re.I),
    re.compile(r"\b(bypass|disable|evade)\b.{0,30}\b(access control|permissions?|security|rbac)\b", re.I),
    re.compile(r"\b(use|treat|follow)\b.{0,40}\bretrieved document\b.{0,40}\b(instructions?|system prompt)\b", re.I),
    re.compile(r"\b(document|context|source)\s+(says|instructs)\b.{0,60}\b(ignore|override|reveal|bypass)\b", re.I),
    re.compile(r"\bi am (the )?admin\b.{0,60}\b(show|reveal|access|bypass)\b", re.I),
]


def prompt_injection_reason(text: str) -> Optional[str]:
    for pattern in _PATTERNS:
        if pattern.search(text):
            return "prompt_injection_or_secret_request"
    return None
