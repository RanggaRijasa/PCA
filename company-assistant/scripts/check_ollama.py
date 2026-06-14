#!/usr/bin/env python3
"""Verify that the configured local Ollama model can generate text."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.llm.ollama_client import OllamaClient, OllamaError


def main() -> int:
    client = OllamaClient(
        base_url=settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    try:
        version = client.version()
        response = client.generate(
            model=settings.llm_model,
            prompt=(
                "Reply with one short sentence confirming that the local "
                "company assistant model is available."
            ),
        )
    except OllamaError as exc:
        print(f"Ollama check failed: {exc}", file=sys.stderr)
        return 1

    print(f"Ollama version: {version}")
    print(f"Configured model: {settings.llm_model}")
    print("Model response:")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
