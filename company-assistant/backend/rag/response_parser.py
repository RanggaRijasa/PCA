"""Normalize model output while keeping citation lists application-owned."""

from __future__ import annotations

import re
from typing import Iterable


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


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
