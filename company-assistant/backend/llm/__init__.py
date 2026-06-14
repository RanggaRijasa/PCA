"""Local model clients kept separate from retrieval and application routes."""

from backend.llm.ollama_client import (
    OllamaClient,
    OllamaError,
    OllamaModelUnavailableError,
    OllamaOfflineError,
)

__all__ = [
    "OllamaClient",
    "OllamaError",
    "OllamaModelUnavailableError",
    "OllamaOfflineError",
]
