---
name: project-architect
description: Use when making structural decisions, creating modules, changing folders, planning implementation order, or resolving conflicts between project specs.
---

# Project Architect Skill

## Purpose

Keep the Private Company Assistant implementation aligned with the project architecture and build order.

## When to Use

Use this skill when asked to:

- Create or modify project structure.
- Decide where files belong.
- Add a new module or feature.
- Resolve conflicting instructions.
- Plan a phase or next build step.
- Refactor across frontend, backend, ingestion, RAG, security, or evaluation.

## Required Context

Read the project docs before making architectural changes:

1. `docs/05_SECURITY_AND_PERMISSIONS.md`
2. `docs/00_SYSTEM_ARCHITECTURE.md`
3. `docs/04_RAG_RUNTIME_SPEC.md`
4. `docs/03_DATA_INGESTION_SPEC.md`
5. `docs/07_UI_BUILD_SPEC.md`
6. `docs/02_FOLDER_STRUCTURE.md`
7. `docs/06_EVALUATION_SPEC.md`
8. `docs/01_AGENT_BUILD_INSTRUCTIONS.md`

Security and permissions override all other specs.

## Architecture Rule

The system must follow this shape:

```text
Frontend UI
-> FastAPI backend
-> Auth + RBAC + audit middleware
-> RAG orchestrator
-> permission-filtered vector retrieval
-> reranking
-> prompt builder
-> Ollama local LLM
-> cited answer
-> audit log
```

Do not collapse these responsibilities into one large file.

## Storage Rule

Keep these responsibilities separate:

- Raw files: `data/raw/`
- Processed files: `data/processed/`
- Vector data: `data/chroma/`
- Metadata database: `data/app.db`
- Backups: `data/backups/`

Do not store operational metadata only inside the vector database.

## Build Order Rule

Build in this order unless the user explicitly changes it:

1. Scaffold.
2. UI-only mock frontend.
3. FastAPI mock endpoints.
4. Ollama health check.
5. SQLite metadata DB.
6. Ingestion.
7. Retrieval-only test.
8. Terminal RAG.
9. Real `/api/chat`.
10. Auth and permission-filtered retrieval.
11. Audit and feedback.
12. Evaluation.
13. Admin upload.
14. Polish.

## Forbidden MVP Changes

Do not add:

- Cloud dependency.
- Fine-tuning.
- Autonomous write actions.
- Email sending.
- ERP/POS/CRM updates.
- Payment approval.
- HR record mutation.
- Multi-tenant deployment.

## Completion Checklist

Before finishing:

- Files are in correct folders.
- Module boundaries are clear.
- No security rule was weakened.
- No premature LLM integration was added.
- The next step is documented.
