"""Small synchronous client for the local Ollama HTTP API."""

from __future__ import annotations

import json
from typing import Iterator, List, Set

import httpx


class OllamaError(RuntimeError):
    """Base error for local Ollama operations."""


class OllamaOfflineError(OllamaError):
    """Raised when the configured local Ollama service is unreachable."""


class OllamaModelUnavailableError(OllamaError):
    """Raised when a requested model is not installed."""


class OllamaClient:
    """Call Ollama without coupling model access to documents or retrieval."""

    def __init__(self, base_url: str, timeout_seconds: float = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._verified_models: Set[str] = set()

    def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout_seconds,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise OllamaOfflineError(
                f"Ollama is not reachable. Check that Ollama is running at {self.base_url}."
            ) from exc

        if response.status_code >= 400:
            detail = self._error_detail(response)
            if response.status_code == 404 or "not found" in detail.lower():
                raise OllamaModelUnavailableError(
                    "Configured model is unavailable. Pull the model or update the model name in .env."
                )
            raise OllamaError(f"Ollama request failed ({response.status_code}): {detail}")
        return response

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "Unknown Ollama error"
        return str(payload.get("error") or payload)

    def version(self) -> str:
        payload = self._request("GET", "/api/version").json()
        return str(payload.get("version", "unknown"))

    def list_models(self) -> List[str]:
        payload = self._request("GET", "/api/tags").json()
        return [
            str(model.get("name"))
            for model in payload.get("models", [])
            if model.get("name")
        ]

    def require_model(self, model: str) -> None:
        if not model:
            raise OllamaModelUnavailableError(
                "No model is configured. Set the model name in .env."
            )
        if model in self._verified_models:
            return
        available = self.list_models()
        matches_configured_name = model in available or (
            ":" not in model
            and any(installed.split(":", maxsplit=1)[0] == model for installed in available)
        )
        if not matches_configured_name:
            raise OllamaModelUnavailableError(
                f"Configured model '{model}' is unavailable. "
                f"Run 'ollama pull {model}' or update .env."
            )
        self._verified_models.add(model)

    def generate(self, model: str, prompt: str) -> str:
        self.require_model(model)
        response = self._request(
            "POST",
            "/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
        )
        text = str(response.json().get("response", "")).strip()
        if not text:
            raise OllamaError("Ollama returned an empty response.")
        return text

    def stream_generate(self, model: str, prompt: str) -> Iterator[str]:
        """Yield generation fragments for later runtime phases."""

        self.require_model(model)
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code >= 400:
                    detail = response.read().decode("utf-8", errors="replace")
                    raise OllamaError(
                        f"Ollama streaming request failed ({response.status_code}): {detail}"
                    )
                for line in response.iter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    fragment = payload.get("response")
                    if fragment:
                        yield str(fragment)
        except httpx.RequestError as exc:
            raise OllamaOfflineError(
                f"Ollama is not reachable. Check that Ollama is running at {self.base_url}."
            ) from exc

    def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        self.require_model(model)
        if not texts:
            return []
        response = self._request(
            "POST",
            "/api/embed",
            json={"model": model, "input": texts, "truncate": True},
        )
        embeddings = response.json().get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Ollama returned an invalid embedding response.")
        return embeddings
