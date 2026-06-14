"""Prevent unsafe model output from being returned as an answer."""

from __future__ import annotations

import re
from typing import Optional


_LEAK_PATTERNS = [
    re.compile(r"\b(system prompt|developer message)\s+(is|says|contains)\b", re.I),
    re.compile(r"\b(api[_ -]?key|password|secret token)\s*[:=]", re.I),
    re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.I),
]


def unsafe_output_reason(text: str) -> Optional[str]:
    for pattern in _LEAK_PATTERNS:
        if pattern.search(text):
            return "possible_hidden_configuration_disclosure"
    return None
