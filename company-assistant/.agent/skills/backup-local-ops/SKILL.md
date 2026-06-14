---
name: backup-local-ops
description: Use when adding local backup, reset scripts, .env.example, .gitignore rules, Mac setup instructions, or local operations documentation.
---

# Backup and Local Ops Skill

## Purpose

Make the local MVP safe to run, reset, and back up on a Mac without committing private data.

## Required Files

Create or update:

```text
scripts/backup.py
scripts/reset_local_data.py
.env.example
.gitignore
README.md
```

## Backup Targets

Back up:

- `data/raw/`
- `data/processed/`
- `data/chroma/`
- `data/app.db`
- `eval/`
- safe config templates.

Default backup path:

```text
data/backups/YYYY-MM-DD-HHMMSS/
```

## Reset Rules

`reset_local_data.py` may remove local runtime data only after clear confirmation.

Do not delete:

- source code.
- docs.
- `.env.example`.
- sample dummy docs unless explicitly requested.

## Gitignore Rules

Do not commit:

- `.env`
- `data/raw/*`
- `data/processed/*`
- `data/chroma/*`
- `data/app.db`
- `data/backups/*`
- audit logs.
- chat logs.
- company documents.

## Done Criteria

- Backup script creates timestamped backup.
- Reset script is safe.
- `.gitignore` protects private data.
- README explains local setup.
