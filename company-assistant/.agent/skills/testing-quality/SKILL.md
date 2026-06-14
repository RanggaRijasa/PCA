---
name: testing-quality
description: Use when adding tests, checking regressions, validating chunking, retrieval, citations, permissions, prompt injection handling, or API behavior.
---

# Testing Quality Skill

## Purpose

Ensure critical functionality is tested and regressions are caught early.

## Required Test Areas

Create tests for:

- chunking.
- metadata preservation.
- retrieval.
- permission filtering.
- citations.
- prompt injection refusal.
- API contracts.
- audit log creation.

## Required Files

Create or update:

```text
tests/test_chunker.py
tests/test_retrieval.py
tests/test_permissions.py
tests/test_citations.py
tests/test_prompt_injection.py
tests/test_api_contracts.py
```

## Test Rules

- Use dummy documents only.
- Do not use real company data.
- Tests must run locally.
- Do not require cloud services.
- Mock Ollama where possible for unit tests.
- Use integration tests only where needed.

## Critical Assertions

Permissions:

- viewer cannot retrieve staff/manager/admin/restricted chunks.
- staff cannot retrieve manager/admin chunks.
- manager cannot retrieve admin chunks.
- admin can retrieve admin chunks.
- restricted requires explicit user access.

Citations:

- answer includes document title.
- answer includes source file.
- answer includes page or section when available.
- citations correspond to retrieved chunks.

Refusal:

- no evidence leads to refusal.
- system prompt request is refused.
- credential request is refused.
- prompt injection request is refused.

## Done Criteria

- Tests run with one command.
- Critical security and citation tests pass.
- Failures are documented before handing off.
