# Private Company Assistant

A local-first company RAG assistant with permission-filtered retrieval, grounded Ollama answers, citations, audit logs, evaluation, and secured administrator ingestion.

The MVP is complete through Phase 13. It supports:

- React + TypeScript administration and chat UI.
- FastAPI with password login and opaque HttpOnly sessions.
- `viewer`, `staff`, `manager`, and `admin` roles.
- PDF, DOCX, TXT, and Markdown ingestion.
- SQLite metadata plus ChromaDB vectors.
- Permission filters applied before vector retrieval.
- Local Ollama embeddings and answer generation.
- Streaming chat, citations, refusals, feedback, and audit logs.
- An evaluation harness with a 50-question production quality gate.
- Admin-only upload, approval, ingestion status, retry, and re-indexing.
- Local backup and confirmation-safe reset scripts.

## Requirements

- macOS on Apple Silicon or Intel
- Python 3.9 or newer
- Node.js 20 or newer
- Ollama
- Enough local disk space for models, documents, vectors, and backups

## Mac Setup

Using Homebrew:

```bash
brew install python@3.11 node ollama
brew services start ollama
```

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Change `SEED_USER_PASSWORD` in `.env`. Keep `.env` private. Install the configured models:

```bash
ollama pull gemma3:1b
ollama pull bge-m3
python scripts/check_ollama.py
python scripts/init_db.py
```

Seeded usernames are `viewer`, `staff`, `manager`, and `admin`. The configured seed password is hashed before storage.

## Sample Documents

Generate harmless PDF, DOCX, TXT, and Markdown documents plus metadata sidecars:

```bash
python scripts/create_dummy_documents.py
python ingestion/ingest_folder.py
```

The generator is the committed sample-document source. Generated files live under ignored `data/raw/` and must not be committed.

## Synthetic Test Corpus

Place `company_assistant_test_corpus.zip` in the project root, `downloads/`, or `data/`, then run from the project directory:

```bash
.venv/bin/python scripts/import_test_corpus.py
```

The importer validates archive paths, required folders, the manifest, document counts, and SHA256 hashes before it prepares the corpus. It extracts the original archive below `data/test_corpus/company_assistant_test_corpus/`, copies only document folders to `data/raw/test_corpus/`, copies metadata to `data/metadata/document_metadata.csv`, and installs the evaluation questions under `eval/`. Existing evaluation files are backed up with timestamped names in `eval/backups/` before replacement. Re-running the importer leaves matching files unchanged.

Initialize and ingest the imported corpus:

```bash
.venv/bin/python scripts/init_db.py
.venv/bin/python ingestion/ingest_folder.py
```

Verify permission-filtered retrieval:

```bash
.venv/bin/python scripts/test_retrieval.py --role staff "What is our remote work policy?"
```

The imported archive includes a 15-question starter suite. This repository keeps the active evaluation files expanded to 70 questions by combining those synthetic cases with the existing sample-document production gate. Re-running the importer preserves an existing 50+ question active set instead of shrinking it back to the starter suite.

Run the active production-sized evaluation with:

```bash
.venv/bin/python eval/run_eval.py
```

Real company documents, metadata exports, archives, vectors, databases, and evaluation backups must not be committed.

## Run Everything

Start FastAPI from the project root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start React in another terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Use the same hostname for frontend and API so the HttpOnly session cookie remains first-party.

## Use The UI

1. Sign in with a seeded local account.
2. Use Chat for permission-filtered RAG questions.
3. Inspect Sources, Context, and Details for evidence and runtime metadata.
4. Submit answer feedback with the thumbs buttons.
5. Sign in as `admin` to view Audit Logs, Evaluation, and Ingestion.

Backend authorization is the source of truth. Hiding admin navigation in React is only a convenience.

## Admin Ingestion

Open `/admin/ingestion` as an administrator.

1. Choose a PDF, DOCX, TXT, or Markdown file.
2. Enter title, department, access level, owner, version, effective date, optional expiry date, and document type.
3. Select **Validate and queue**.
4. Review the queued job. At this point it has no Chroma vectors and is not searchable.
5. Select **Approve and index**.
6. Wait for `completed`. Failed extraction, embedding, or indexing jobs retain a readable error and can be retried.
7. Use **Re-index** on the current completed version when the index needs rebuilding.

Admin endpoints:

```text
POST /api/admin/documents/upload
POST /api/admin/ingestion/run
GET  /api/admin/ingestion/jobs
```

All three require a real authenticated admin session. Upload validation checks extension, content signature/encoding, size, SHA256, metadata, duplicate hashes, and duplicate version labels.

Manual folder ingestion remains available for local operators:

```bash
python ingestion/ingest_folder.py
```

Each manually placed source file needs either a matching `.metadata.json` sidecar or a row in the configured metadata CSV. Sidecars take precedence when both exist. Manual folder ingestion is an operator command and bypasses the UI approval queue, so only place already-approved documents in `data/raw/`.

## Retrieval And RAG

Retrieval without answer generation:

```bash
python scripts/test_retrieval.py --role staff "What is our remote work policy?"
python scripts/test_retrieval.py --role viewer "What is our remote work policy?"
```

Grounded terminal RAG:

```bash
python scripts/rag_query.py --role staff "What is our remote work policy?"
```

The permission matrix is:

- `viewer`: `public_internal`
- `staff`: `public_internal`, `staff`
- `manager`: `public_internal`, `staff`, `manager`
- `admin`: `public_internal`, `staff`, `manager`, `admin`
- `restricted`: explicit user-document grant only

## Evaluation

Ensure Ollama is running and the corpus is indexed. The active evaluation set contains 70 questions across direct answer, multi-document, no-answer, permission-restricted, outdated-document trap, conflicting-source, Indonesian, English, mixed-language, table-based, and prompt-injection categories.

Run the production-sized gate with:

```bash
python eval/run_eval.py
```

Reports are written to:

```text
eval/reports/YYYY-MM-DD-eval-report.md
eval/reports/YYYY-MM-DD-eval-results.json
```

The Admin Evaluation page reads the JSON report through `/api/evaluation/runs`. Permission correctness must remain 100% and critical leakage must remain zero before company use.

`expected_answer_keywords` supports both the original format and mixed-language alias groups:

```text
manager|manajer;review|meninjau;reimbursement|penggantian
```

For alias-aware rows, `;` separates required concept groups and `|` separates acceptable aliases inside one group. Keyword correctness uses the existing 60% matched-concept threshold. Rows without `;` retain the legacy behavior where commas or pipes separate independently expected keywords.

Latest Gemma 4 12B evaluation on June 14, 2026: 70/70 passed with 100% retrieval hit rate, answer correctness, citation correctness, refusal correctness, and permission correctness; hallucination rate 0%; no critical leakage; 19,238 ms average latency and 55,325 ms p95. Alias groups resolved the four prior semantically-correct mixed Indonesian-English mismatches without changing retrieval, permissions, citations, refusals, prompt-injection handling, or leakage checks.

## Backup

Stop active ingestion before copying ChromaDB, then run:

```bash
python scripts/backup.py
```

The default destination is `data/backups/YYYY-MM-DD-HHMMSS/`. A backup contains raw and processed documents, ChromaDB, a consistent SQLite snapshot, evaluation files, safe templates, and a SHA256 manifest. It deliberately excludes `.env`.

Use a different parent directory when needed:

```bash
python scripts/backup.py --destination /path/to/private/backups
```

Backups can contain company documents and must be stored securely. They are ignored by Git.

## Reset Local Data

First create a backup. A command without the exact phrase changes nothing:

```bash
python scripts/reset_local_data.py
python scripts/reset_local_data.py --confirm RESET_LOCAL_DATA
```

Reset removes SQLite runtime databases, processed files, ChromaDB, archived runtime files, admin uploads, and non-sample raw documents. It preserves source code, docs, `.env.example`, backups, and generated `sample_*` documents.

To explicitly remove sample documents too:

```bash
python scripts/reset_local_data.py \
  --confirm RESET_LOCAL_DATA \
  --include-sample-documents
```

After reset:

```bash
python scripts/init_db.py
python scripts/create_dummy_documents.py
python ingestion/ingest_folder.py
```

## Tests And Checks

```bash
.venv/bin/pytest -q
.venv/bin/python -m compileall backend ingestion scripts tests
cd frontend && npm run build
```

Focused security checks:

```bash
.venv/bin/pytest -q \
  tests/test_admin_ingestion.py \
  tests/test_auth_security.py \
  tests/test_permissions.py \
  tests/test_prompt_injection.py \
  tests/test_audit_feedback.py
```

## Data Safety

The `.gitignore` excludes `.env`, ZIP archives, raw, processed, extracted test-corpus and metadata files, SQLite databases and WAL files, ChromaDB, backups, evaluation backups, frontend dependencies/build output, audit logs, and chat logs. Never commit company documents or runtime stores.

## Known Limitations

- Ingestion runs synchronously in the FastAPI worker; large files should move to a background worker in a later release.
- There is no antivirus or malware scanner; validation covers supported type signatures, encoding, and parsing.
- Scanned PDFs require a future OCR workflow.
- Admin archiving and restricted-grant management do not yet have UI/API workflows.
- Seeded users share the initialization password until password-change and user-management features are added.
- Login throttling, account lockout, password reset, and CSRF tokens are not implemented.
- Chroma backup is a filesystem copy; stop active ingestion for the cleanest snapshot.
- The lightweight reranker is not a cross-encoder.
- The imported archive contributes 15 cases; the active production gate expands this to 70 synthetic and sample-document questions.
- Evaluation quality still depends on the configured local model and indexed corpus, and the 12B run has a measured p95 latency above 55 seconds.

See [HANDOFF.md](HANDOFF.md) for the final Phase 12-13 implementation inventory and measured checks.
