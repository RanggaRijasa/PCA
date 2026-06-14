---
name: data-ingestion
description: Use when building document validation, parsing, cleaning, metadata extraction, chunking, embedding, ChromaDB indexing, SQLite metadata storage, or ingestion logs.
---

# Data Ingestion Skill

## Purpose

Convert approved company documents into searchable, permission-aware chunks for RAG.

## Required Source Spec

Follow `docs/03_DATA_INGESTION_SPEC.md`.

## Supported MVP File Types

Support:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

Optional later:

- `.xlsx`
- `.csv`
- `.pptx`
- scanned images

## Required Files

Create or update:

```text
ingestion/ingest_folder.py
ingestion/file_validator.py
ingestion/parsers.py
ingestion/cleaner.py
ingestion/chunker.py
ingestion/metadata.py
ingestion/embedder.py
ingestion/indexer.py
```

## Ingestion Flow

Implement:

```text
file discovered in data/raw
-> validate file type and size
-> calculate SHA256 hash
-> check duplicate/version status
-> extract text and structure
-> clean extracted content
-> apply metadata
-> chunk by section and token length
-> generate embeddings
-> store vectors in ChromaDB
-> store metadata in SQLite
-> write ingestion log
```

## Metadata Rule

Every document must include:

- document id.
- title.
- source file.
- file hash.
- document type.
- department.
- access level.
- owner.
- version.
- effective date.
- expiry date when available.
- created at.
- indexed at.

Every chunk must include:

- chunk id.
- document id.
- title.
- source file.
- page when available.
- section when available.
- chunk index.
- access level.
- department.
- version.
- effective date.

## Chunking Rule

Do not chunk only by fixed character length.

Use:

1. Split by document sections/headings.
2. If a section is too long, split by token length.
3. Use overlap.
4. Preserve metadata on every chunk.

Recommended defaults:

```text
Target chunk size: 300-800 tokens
Overlap: 50-100 tokens
Maximum chunk size: 1000 tokens
```

## Embedding Rule

Use a dedicated embedding model. Do not use the main LLM for embeddings.

Default:

```text
EMBED_MODEL=BAAI/bge-m3
```

## Failure Rule

If parsing fails, do not index unreliable partial chunks. Mark the ingestion job as failed and store the error.

## Done Criteria

- Files in `data/raw/` can be ingested.
- Chunks are stored in ChromaDB.
- Metadata is stored in SQLite.
- File hash duplicate detection exists.
- Failed ingestion is visible in logs or database.
