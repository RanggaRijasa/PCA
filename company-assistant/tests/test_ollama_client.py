"""Ollama client configuration behavior without network access."""

from backend.llm.ollama_client import OllamaClient


def test_model_name_accepts_implicit_latest_tag(monkeypatch) -> None:
    client = OllamaClient("http://localhost:11434")
    monkeypatch.setattr(client, "list_models", lambda: ["bge-m3:latest"])

    client.require_model("bge-m3")

    assert "bge-m3" in client._verified_models
