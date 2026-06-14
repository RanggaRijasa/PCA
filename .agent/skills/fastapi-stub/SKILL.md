---
name: fastapi-stub
description: Use when creating FastAPI mock endpoints, API contracts, stub JSON responses, or connecting the frontend to backend stubs before real RAG exists.
---

# FastAPI Stub Skill

## Purpose

Create backend API contracts before connecting real LLM, RAG, ChromaDB, or authentication.

## Critical Rule

This skill is for mock/stub endpoints only.

Do not call:

- Ollama.
- LlamaIndex.
- ChromaDB.
- Embedding models.
- Real RAG services.

## Required Endpoints

Implement:

```text
GET  /api/health
GET  /api/me
GET  /api/conversations
GET  /api/conversations/{conversation_id}
POST /api/conversations
POST /api/chat/mock
POST /api/feedback
GET  /api/documents
GET  /api/audit-logs
GET  /api/evaluation/runs
```

## Response Shape Rule

Responses must match `docs/07_UI_BUILD_SPEC.md` API contracts.

Use static JSON or simple in-memory mock stores.

## Error Handling

Return readable JSON errors:

```json
{
  "error": "message",
  "code": "ERROR_CODE"
}
```

## Frontend Integration

After endpoints exist, update the frontend API client so the UI can load mock data from FastAPI instead of local TypeScript objects.

## Done Criteria

- FastAPI app starts.
- `/api/health` returns ok.
- UI can call stub endpoints.
- `/api/chat/mock` returns a mock answer, mock sources, and mock metadata.
- No real LLM or vector DB is used.
