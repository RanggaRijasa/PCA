---
name: admin-workflow
description: Use after the core MVP works, when implementing admin upload, ingestion queue, document approval, re-indexing, archiving, user role management, or admin pages.
---

# Admin Workflow Skill

## Purpose

Build admin workflows without weakening security or making documents searchable too early.

## Use Only After

Use this skill only after:

- manual folder ingestion works.
- RAG answers with citations.
- permission filtering works.
- audit logging works.

## Admin Routes

Admin-only features:

- document upload.
- metadata entry.
- document approval.
- ingestion queue.
- re-indexing.
- archiving.
- user/role management.
- audit log viewing.
- evaluation runs.

## Upload Requirements

Before indexing, require:

- allowed file extension.
- max file size validation.
- SHA256 hash.
- title.
- department.
- access level.
- owner.
- version.
- effective date.
- document type.
- approval status.

## Ingestion Statuses

Use:

```text
queued
validating
extracting
chunking
embedding
indexing
completed
failed
archived
```

## Critical Rule

Upload does not mean searchable.

Correct flow:

```text
upload -> validate -> metadata -> approval -> ingestion -> indexed -> searchable
```

## Done Criteria

- Non-admin users cannot access admin upload routes.
- Metadata is required.
- Failed jobs show useful errors.
- Re-index and archive actions are admin-only.
- Audit logs capture admin actions.
