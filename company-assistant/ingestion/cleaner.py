"""Normalize extracted text without discarding document structure."""

from __future__ import annotations

import re
from typing import Iterable, List

from ingestion.parsers import ParsedSection


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
    cleaned_lines: List[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank
    return "\n".join(cleaned_lines).strip()


def clean_sections(sections: Iterable[ParsedSection]) -> List[ParsedSection]:
    cleaned: List[ParsedSection] = []
    for section in sections:
        text = clean_text(section.text)
        if text:
            cleaned.append(
                ParsedSection(
                    text=text,
                    section=section.section,
                    page=section.page,
                )
            )
    return cleaned
