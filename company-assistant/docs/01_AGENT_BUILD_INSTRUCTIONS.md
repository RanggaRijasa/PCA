# Agentic AI Build Instructions

## 1. Source of Truth

Treat these Markdown files as the source of truth for the project:

1. `00_SYSTEM_ARCHITECTURE.md`
2. `01_AGENT_BUILD_INSTRUCTIONS.md`
3. `02_FOLDER_STRUCTURE.md`
4. `03_DATA_INGESTION_SPEC.md`
5. `04_RAG_RUNTIME_SPEC.md`
6. `05_SECURITY_AND_PERMISSIONS.md`
7. `06_EVALUATION_SPEC.md`

If implementation details conflict, follow the files in this priority order:

1. Security and permissions
2. System architecture
3. RAG runtime
4. Data ingestion
5. Folder structure
6. Evaluation

## 2. Implementation Rules

- Build the MVP first.
- Do not add unnecessary features.
- Do not introduce cloud dependencies.
- Do not require paid services.
- Do not fine-tune the model.
- Do not create write actions such as sending email or modifying company databases.
- Keep the system local-first.
- Keep modules separated.
- Use environment variables for configurable paths and model names.
- Do not hardcode secrets.
- Do not log passwords, API keys, raw tokens, or full confidential documents.

## 3. Required MVP Features

The first working version must include:

- Local Ollama LLM integration.
- Local embedding model integration.
- Document ingestion from a local folder.
- PDF, DOCX, TXT, MD support.
- ChromaDB vector indexing.
- SQLite metadata database.
- LlamaIndex-based RAG query flow.
- FastAPI `/chat` endpoint.
- Streaming answer response.
- Streamlit chat UI.
- Source citations.
- Refusal when sources are insufficient.
- Basic user login.
- Role-based document filtering.
- Audit log table.
- Evaluation script.

## 4. Development Approach

Implement in small vertical slices.

### Slice 1: Local LLM Health Check

Goal: prove that the backend can call Ollama.

Required output:

- Script: `scripts/check_ollama.py`
- It sends a short prompt to Ollama.
- It prints the response.
- It fails clearly if Ollama is not running.

### Slice 2: Ingestion Prototype

Goal: index a few test documents.

Required output:

- Script: `ingestion/ingest_folder.py`
- Reads files from `data/raw/`
- Extracts text
- Chunks text
- Creates embeddings
- Stores vectors in ChromaDB
- Stores document/chunk metadata in SQLite

### Slice 3: Terminal RAG Test

Goal: prove retrieval and answer generation work before building UI.

Required output:

- Script: `scripts/rag_query.py`
- Accepts a question
- Retrieves chunks
- Generates answer
- Prints citations

### Slice 4: FastAPI Chat API

Goal: expose RAG through an API.

Required output:

- Endpoint: `POST /chat`
- Accepts `{ "message": "..." }`
- Streams response
- Returns citations
- Writes audit log

### Slice 5: Streamlit UI

Goal: simple user-facing MVP.

Required output:

- Chat input
- Streaming answer
- Source list
- Feedback buttons

### Slice 6: Security Controls

Goal: apply permission filtering.

Required output:

- User table
- Role table
- Document access metadata
- Retrieval filters based on user role
- Refusal when unauthorized

### Slice 7: Evaluation

Goal: validate the assistant.

Required output:

- `eval/test_questions.csv`
- `eval/run_eval.py`
- Report with accuracy, citation correctness, refusal correctness, and latency

## 5. Coding Standards

- Use Python type hints.
- Keep functions small.
- Use clear module boundaries.
- Avoid global state except configuration.
- Add docstrings for important functions.
- Handle errors explicitly.
- Use structured logging.
- Write simple tests for ingestion, retrieval, citation, and permission filtering.

## 6. Configuration

Use `.env` for runtime configuration.

Example:

```env
APP_ENV=development
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma4:12b
EMBED_MODEL=BAAI/bge-m3
CHROMA_PATH=./data/chroma
SQLITE_PATH=./data/app.db
RAW_DOCS_PATH=./data/raw
PROCESSED_DOCS_PATH=./data/processed
DEFAULT_TOP_K=20
RERANK_TOP_K=5
MAX_CONTEXT_CHUNKS=6
```

## 7. Done Definition

The project is done when:

- The app runs locally with one command or a clear two-command process.
- A user can upload or place documents in `data/raw` and run ingestion.
- A user can ask questions in the UI.
- The assistant answers with citations.
- The assistant refuses unsupported questions.
- The assistant respects role-based access.
- Audit logs are written.
- Evaluation script runs successfully.
