# Data Ingestion Specification

## 1. Purpose

The ingestion pipeline converts approved company files into searchable, permission-aware chunks for RAG.

The pipeline must preserve provenance. Every chunk must be traceable back to its original document, page, section, version, and access level.

## 2. Supported File Types for MVP

Required:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

Optional after MVP:

- `.xlsx`
- `.csv`
- `.pptx`
- scanned image files

## 3. Ingestion Flow

```text
File discovered in data/raw
 ↓
Validate file type and size
 ↓
Calculate file hash
 ↓
Check duplicate/version status
 ↓
Extract text and structure
 ↓
Clean extracted content
 ↓
Apply document metadata
 ↓
Chunk by section and token length
 ↓
Generate embeddings
 ↓
Store chunks in ChromaDB
 ↓
Store metadata in SQLite
 ↓
Write ingestion log
```

## 4. Required Metadata

Each document must have:

```json
{
  "document_id": "stable unique id",
  "title": "Human-readable title",
  "source_file": "original filename",
  "file_hash": "sha256 hash",
  "document_type": "policy | sop | manual | faq | report | other",
  "department": "HR | Finance | Sales | Operations | General",
  "access_level": "public_internal | staff | manager | admin | restricted",
  "owner": "document owner or department",
  "version": "v1.0",
  "effective_date": "YYYY-MM-DD or null",
  "expiry_date": "YYYY-MM-DD or null",
  "created_at": "timestamp",
  "indexed_at": "timestamp"
}
```

Each chunk must have:

```json
{
  "chunk_id": "stable unique id",
  "document_id": "parent document id",
  "title": "document title",
  "source_file": "original filename",
  "page": 1,
  "section": "section heading if available",
  "chunk_index": 0,
  "access_level": "staff",
  "department": "HR",
  "version": "v1.0",
  "effective_date": "YYYY-MM-DD or null"
}
```

## 5. Parsing Rules

### PDF

- Prefer structured extraction.
- Preserve page numbers.
- Preserve headings where possible.
- Detect tables if possible.
- If text extraction is poor, mark the document as requiring OCR.

### DOCX

- Preserve headings.
- Preserve paragraphs.
- Preserve simple tables as Markdown tables where possible.

### TXT / MD

- Preserve headings.
- Preserve lists.
- Normalize excessive whitespace.

### Excel / CSV after MVP

- Do not blindly chunk spreadsheets.
- Convert each sheet/table into a structured text representation.
- Preserve sheet name, column names, and row ranges.

## 6. Chunking Rules

Do not chunk only by fixed character length.

Use this priority:

1. Split by document sections/headings.
2. If a section is too long, split by token length.
3. Keep overlap between chunks.
4. Keep metadata on every chunk.

Recommended defaults:

```text
Target chunk size: 300–800 tokens
Overlap: 50–100 tokens
Maximum chunk size: 1,000 tokens
```

## 7. Embedding Rules

Recommended embedding model:

```text
BAAI/bge-m3
```

Reason:

- Better multilingual support for Indonesian-English documents.
- Good long-text retrieval capability.
- More suitable than English-only small embeddings for local companies using mixed language documents.

Do not use the main LLM to create embeddings.

## 8. Duplicate and Version Handling

Use file hash to detect exact duplicates.

If a document with the same title but different hash is added:

- Treat it as a new version.
- Keep the old version unless admin archives it.
- Prefer newer effective date during answer generation when sources conflict.

## 9. Failed Ingestion Handling

If a file cannot be parsed:

- Do not partially index unreliable chunks.
- Mark ingestion status as `failed`.
- Store error message in ingestion log.
- Show the failure in admin UI or CLI output.

## 10. Admin Approval Rule

For MVP, documents may be placed manually into `data/raw`.

For any `/upload_docs` endpoint:

- Upload must be admin-only.
- File must be validated.
- Metadata must be provided before indexing.
- Document should be approved before becoming searchable.
