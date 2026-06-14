# Folder Structure

## 1. Target Project Structure

```text
company-assistant/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── logging_config.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── health.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── password.py
│   │   ├── permissions.py
│   │   └── session.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   ├── prompt_builder.py
│   │   ├── citation_builder.py
│   │   ├── response_parser.py
│   │   └── service.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── ollama_client.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.py
│   │   ├── documents.py
│   │   ├── users.py
│   │   ├── audit.py
│   │   └── feedback.py
│   │
│   └── safety/
│       ├── __init__.py
│       ├── input_checks.py
│       ├── prompt_injection.py
│       └── output_checks.py
│
├── frontend/
│   ├── streamlit_app.py
│   └── components/
│       ├── chat_message.py
│       └── sources.py
│
├── ingestion/
│   ├── __init__.py
│   ├── ingest_folder.py
│   ├── file_validator.py
│   ├── parsers.py
│   ├── cleaner.py
│   ├── chunker.py
│   ├── metadata.py
│   ├── embedder.py
│   └── indexer.py
│
├── scripts/
│   ├── check_ollama.py
│   ├── init_db.py
│   ├── rag_query.py
│   ├── backup.py
│   └── reset_local_data.py
│
├── eval/
│   ├── test_questions.csv
│   ├── expected_answers.csv
│   ├── run_eval.py
│   └── reports/
│
├── tests/
│   ├── test_chunker.py
│   ├── test_retrieval.py
│   ├── test_permissions.py
│   └── test_citations.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── archived/
│   ├── chroma/
│   ├── app.db
│   └── backups/
│
└── docs/
    ├── 00_SYSTEM_ARCHITECTURE.md
    ├── 01_AGENT_BUILD_INSTRUCTIONS.md
    ├── 02_FOLDER_STRUCTURE.md
    ├── 03_DATA_INGESTION_SPEC.md
    ├── 04_RAG_RUNTIME_SPEC.md
    ├── 05_SECURITY_AND_PERMISSIONS.md
    └── 06_EVALUATION_SPEC.md
```

## 2. Folder Responsibilities

### `backend/`

Holds the FastAPI application, API routes, RAG runtime logic, authentication, database access, and safety controls.

### `frontend/`

Holds the Streamlit user interface for the MVP.

### `ingestion/`

Holds document parsing, cleaning, chunking, embedding, and indexing logic. This must be runnable without starting the chat app.

### `scripts/`

Holds local utility scripts for setup, testing, backup, and health checks.

### `eval/`

Holds evaluation questions, expected answers, and test reports.

### `tests/`

Holds automated tests.

### `data/`

Holds local runtime data. This folder should be excluded from Git except `.gitkeep` files.

### `docs/`

Holds project context and build instructions for humans and AI coding agents.

## 3. Git Rules

Do not commit:

- `data/raw/*`
- `data/processed/*`
- `data/chroma/*`
- `data/app.db`
- `data/backups/*`
- `.env`
- company documents
- audit logs
- chat logs

Commit:

- source code
- docs
- `.env.example`
- tests
- sample dummy documents only if they contain no private company data
