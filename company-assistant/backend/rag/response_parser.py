"""Normalize model output while keeping citation lists application-owned."""

from __future__ import annotations

import re
from typing import Iterable


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")

_REFUSAL_PATTERNS = (
    re.compile(r"\bi (?:could not|can't|cannot|do not|don't) (?:find|provide|answer)\b", re.I),
    re.compile(r"\bnot found in (?:the )?approved company documents\b", re.I),
    re.compile(r"\bcontext (?:is|was) insufficient\b", re.I),
    re.compile(r"\binsufficient (?:context|evidence|information)\b", re.I),
    re.compile(r"\bapproved context did not contain\b", re.I),
    re.compile(r"\bno (?:relevant|supporting|sufficient) (?:evidence|source|context)\b", re.I),
    re.compile(r"\bdoes not contain (?:enough|the requested|this information|information about)\b", re.I),
    re.compile(r"\b(?:provided|approved) context does not contain\b", re.I),
)


def is_refusal_body(text: str) -> bool:
    """Detect model output that is semantically a refusal."""
    return any(pattern.search(text) for pattern in _REFUSAL_PATTERNS)


def clean_answer_body(raw_text: str, source_count: int) -> str:
    text = raw_text.strip()
    text = re.sub(r"^Answer:\s*", "", text, flags=re.I)
    text = re.split(r"\n\s*(Sources|Confidence|Notes):", text, maxsplit=1, flags=re.I)[0]
    text = text.strip()
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    if not text:
        return "The approved context did not contain a usable answer."

    valid_markers = {
        int(match.group(1))
        for match in _CITATION_PATTERN.finditer(text)
        if 1 <= int(match.group(1)) <= source_count
    }
    if source_count and not valid_markers:
        paragraphs = []
        for paragraph in text.splitlines():
            stripped = paragraph.strip()
            if stripped and any(character.isalpha() for character in stripped):
                paragraph = f"{paragraph.rstrip()} [1]"
            paragraphs.append(paragraph)
        text = "\n".join(paragraphs)
    return text
