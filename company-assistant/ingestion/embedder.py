"""Generate document embeddings with the configured local Ollama model."""

from __future__ import annotations

from typing import Iterable, List

from backend.llm.ollama_client import OllamaClient


class EmbeddingService:
    """Batch text embedding without knowledge of document permissions."""

    def __init__(
        self,
        client: OllamaClient,
        model: str,
        batch_size: int = 16,
    ) -> None:
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        values = list(texts)
        embeddings: List[List[float]] = []
        for start in range(0, len(values), self.batch_size):
            embeddings.extend(
                self.client.embed(self.model, values[start : start + self.batch_size])
            )
        return embeddings
