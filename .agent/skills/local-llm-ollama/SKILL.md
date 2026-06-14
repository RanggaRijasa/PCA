---
name: local-llm-ollama
description: Use when adding Ollama health checks, local LLM client code, streaming response handling, model configuration, or LLM error handling.
---

# Local LLM Ollama Skill

## Purpose

Integrate with Ollama as the local LLM runtime without mixing LLM code with retrieval, ingestion, or UI code.

## Required Configuration

Read from `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma4:12b
OLLAMA_TIMEOUT_SECONDS=120
```

Never hardcode model names or URLs outside config defaults.

## Required Files

Create or update:

```text
scripts/check_ollama.py
backend/llm/ollama_client.py
backend/config.py
```

## Health Check Script

`scripts/check_ollama.py` must:

- Load `.env`.
- Check the Ollama base URL.
- Send a short prompt.
- Print the response.
- Fail clearly if Ollama is offline or the model is unavailable.

## Ollama Client Rules

The client must:

- Support normal generation.
- Support streaming generation.
- Handle timeouts.
- Surface clear errors to callers.
- Not know anything about ChromaDB or document retrieval.

## Error Messages

Use clear errors such as:

```text
Ollama is not reachable. Check that Ollama is running at OLLAMA_BASE_URL.
```

```text
Configured model is unavailable. Pull the model or update LLM_MODEL in .env.
```

## Done Criteria

- `python scripts/check_ollama.py` works.
- `backend/llm/ollama_client.py` can stream tokens.
- No document ingestion or retrieval is coupled into this module.
