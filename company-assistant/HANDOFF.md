# Phase 12-13 Final Handoff

## Completed

- Added admin-only document upload, required metadata, type/content/size validation, SHA256 hashing, duplicate detection, and staged storage.
- Kept staged uploads out of ChromaDB and SQLite chunks until explicit admin approval and successful indexing.
- Added tracked ingestion states, readable failures, retry, and re-indexing.
- Added audit events for administrator uploads and ingestion runs.
- Replaced the mock `/admin/ingestion` page with the real upload form and job queue.
- Added timestamped local backup with SQLite backup API and SHA256 manifest.
- Added exact-confirmation reset that preserves backups and sample documents by default.
- Finalized Mac setup, full run, ingestion, UI, evaluation, backup, reset, and safety documentation.
- Added admin ingestion and local operations tests while retaining the existing security, retrieval, citation, and prompt-injection coverage.

## Files Changed

- Backend API/config: `backend/api/admin.py`, `models.py`, `health.py`, `backend/main.py`, `backend/config.py`.
- Admin service: `backend/services/__init__.py`, `backend/services/admin_ingestion.py`.
- Database: `backend/db/documents.py`.
- Ingestion: `ingestion/file_validator.py`, `metadata.py`, `service.py`.
- Frontend: `frontend/src/pages/admin/IngestionPage.tsx`, `services/adminApi.ts`, `services/apiClient.ts`, `types/index.ts`.
- Operations: `scripts/backup.py`, `scripts/reset_local_data.py`, `.env.example`, `requirements.txt`.
- Tests: `tests/test_admin_ingestion.py`, `tests/test_local_ops.py`, `tests/test_api_contracts.py`, plus the retained required test files.
- Frontend packaging/polish: `frontend/package.json`, `package-lock.json`, `components/layout/Sidebar.tsx`.
- Evaluation output: `eval/reports/2026-06-12-eval-report.md`, `2026-06-12-eval-results.json`.
- Documentation: `README.md`, `HANDOFF.md`.

Runtime `.env`, source documents, SQLite databases, ChromaDB, processed documents, backups, and logs remain ignored.

## How To Run

```bash
cd company-assistant
source .venv/bin/activate
python scripts/init_db.py
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd company-assistant/frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`.

## How To Ingest Documents

Admin UI:

1. Sign in as `admin`.
2. Open `/admin/ingestion`.
3. Upload a supported file and complete all metadata.
4. Select **Validate and queue**.
5. Select **Approve and index**.
6. Confirm the job reaches `completed` before expecting it in search.

Manual approved-folder ingestion:

```bash
python ingestion/ingest_folder.py
```

## How To Use The UI

- Chat asks grounded questions and streams answers.
- Sources and Details show citations, permissions, model, latency, and audit ID.
- Feedback writes to SQLite and updates the matching audit event.
- Admin Audit Logs inspects persisted chat and admin events.
- Admin Evaluation displays the latest generated benchmark report.
- Admin Ingestion stages, approves, retries, and re-indexes documents.

## How To Run Evaluation

```bash
python eval/run_eval.py
```

The report is generated under `eval/reports/` and appears in Admin Evaluation after refresh.

## How To Back Up Local Data

```bash
python scripts/backup.py
```

Default backups are written below `data/backups/`. Stop active ingestion first. The manifest lists size and SHA256 for every copied file.

## Checks Performed

- Full backend tests: 39 passed.
- Python compile check: passed.
- Frontend TypeScript and Vite production build: passed.
- Ollama health check: version `0.30.7`; configured `gemma3:1b` returned a response.
- Folder ingestion: 4 safe duplicates skipped, 0 failed, 9 vectors retained.
- Retrieval: remote-work policy ranked first with title, file, section, role, department, and scores visible.
- Focused permission/admin/prompt-injection tests: 8 passed.
- Evaluation: 54/55 passed; retrieval 100%; answer 96.8%; citations 100%; refusals 100%; permissions 100%; hallucination 1.8%; average 430 ms; p95 892 ms; no critical leakage.
- Backup: created `data/backups/2026-06-12-190516`; 30 manifest files, SQLite integrity `ok`, `.env` absent.
- Reset: confirmed against temporary data; runtime files were removed while backups and `sample_*` documents were preserved.
- Browser: admin form/queue/re-index controls rendered; historical unlinked jobs had no action; staff navigation hid admin links and direct access showed `Admin access required`.

## Evaluation Summary

- Report: `eval/reports/2026-06-12-eval-report.md`.
- Permission correctness remained 100% with no critical data leakage.
- The only failed case was `Q045`: the correct expense source was cited, but `gemma3:1b` mistranslated “reimbursement” as “reconciliation” in a mixed Indonesian-English answer.

## Known Limitations

- Ingestion is synchronous rather than a persistent background worker.
- Antivirus scanning and OCR are not included.
- Archive controls and restricted-document grant management are not exposed in the admin UI.
- Backup should run while ingestion is stopped for a stable ChromaDB filesystem snapshot.
- Authentication still lacks throttling, password change/reset, lockout, and CSRF tokens.
- The current evaluation corpus is harmless sample data and needs approved representative company fixtures before deployment.
- Repeated manual folder scans retain duplicate-skip job history in the admin queue; these historical records are read-only when they are not linked to a version.

## Next Recommended Step

- Begin post-MVP hardening: background ingestion workers, antivirus/OCR, archive and grant-management workflows, authentication abuse controls, restore verification, and only then the separately specified configurable model upgrade.

## Synthetic Test Corpus Import - June 14, 2026

### Completed

- Added `scripts/import_test_corpus.py` with safe ZIP path checks, a 100 MB extraction limit, required-layout validation, manifest and SHA256 verification, repeat-safe copying, and timestamped evaluation backups.
- Extracted the synthetic archive to `data/test_corpus/company_assistant_test_corpus/`.
- Copied 27 PDF, DOCX, TXT, and Markdown documents into `data/raw/test_corpus/`, preserving the four source folders and nested paths.
- Copied `metadata/document_metadata.csv` to `data/metadata/document_metadata.csv`.
- Added CSV metadata lookup to manual ingestion while preserving `.metadata.json` sidecar precedence.
- Replaced `eval/test_questions.csv` after backing up the previous file and generated a starter `eval/expected_answers.csv` after backing up its predecessor.
- Kept the normal 50-question evaluation quality gate and added `--allow-small-set` for the imported 15-question smoke suite.
- Updated `.gitignore`, `.env.example`, README instructions, importer, metadata, evaluation, and regression tests.

Runtime corpus files, metadata, ZIP archives, database files, ChromaDB, and evaluation backups remain ignored by Git.

### Imported Layout

```text
data/test_corpus/company_assistant_test_corpus/
data/raw/test_corpus/valid_docs/
data/raw/test_corpus/restricted_docs/
data/raw/test_corpus/edge_cases/
data/raw/test_corpus/prompt_injection/
data/metadata/document_metadata.csv
eval/test_questions.csv
eval/expected_answers.csv
eval/backups/
```

All requested metadata fields are supported: title, department, access level, owner, version, effective date, optional expiry date, and document type. The optional corpus SHA256 is also verified before ingestion metadata is accepted.

### Commands

```bash
.venv/bin/python scripts/import_test_corpus.py
.venv/bin/python scripts/init_db.py
.venv/bin/python ingestion/ingest_folder.py
.venv/bin/python scripts/test_retrieval.py --role staff "What is our remote work policy?"
.venv/bin/python eval/run_eval.py --allow-small-set
```

Use `python eval/run_eval.py` only after restoring or expanding the active suite to at least 50 questions.

### Checks Performed

- Importer: 27 documents validated against metadata and SHA256; a second run copied 0 files and reported 27 unchanged.
- SQLite initialization: 12 tables created and four role users present.
- Ingestion: 27 corpus files indexed, four existing samples skipped as exact duplicates, zero failures, 94 Chroma chunks total.
- Metadata verification: representative staff, manager, and admin documents retained CSV title, department, access level, owner, type, version, and dates in SQLite.
- Retrieval: the current remote-work PDF was returned with metadata, though the outdated policy ranked one position higher.
- Permission retrieval: staff did not receive the admin salary-policy chunks; admin ranked the policy first.
- Full Python tests: 44 passed.
- Compile check: passed for backend, ingestion, scripts, evaluation, and tests.
- Normal evaluation command: correctly stopped because 15 questions do not satisfy the 50-question gate.
- Synthetic smoke evaluation: 11/15 passed; retrieval 100%; citations 100%; refusals 80%; permission behavior 93.3%; no critical leakage; 705 ms average and 2580 ms p95.

### Limitations And Risks

- This is synthetic test data, but it must still be handled as company data and remain uncommitted.
- Manual folder ingestion bypasses the admin approval queue; only approved files should be copied into `data/raw/`.
- The imported evaluation set is below the 50-question release threshold and its generated expected answers require manual review.
- The lightweight reranker currently places the outdated remote-work policy above the current policy for a broad query.
- One permission scenario retrieved only authorized but irrelevant chunks; the answer text said evidence was missing but did not set the formal refusal flag. No unauthorized chunks or critical leakage were observed.
- The RAG runtime was intentionally left unchanged, as required by the corpus-import task.

### Next Recommended Step

Review and expand the synthetic evaluation set to at least 50 cases, then address outdated-source ranking and insufficient-evidence refusal behavior in a separately scoped RAG-runtime task.
