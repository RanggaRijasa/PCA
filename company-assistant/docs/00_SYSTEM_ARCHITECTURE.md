# Private Company Assistant: Overall System Architecture

## 1. Purpose

This project builds a private local RAG assistant for company knowledge. The assistant runs on a Mac with Apple Silicon and 24 GB unified memory. The first version is a read-only document assistant that answers questions from approved company documents using retrieval-augmented generation.

The system must not behave like a general chatbot when answering company-specific questions. It must answer only from retrieved company context, cite its sources, and refuse when the available context is insufficient.

## 2. MVP Goal

Build a local assistant that can:

- Let an authorized user ask natural language questions.
- Retrieve relevant chunks from company documents.
- Generate grounded answers using a local LLM.
- Show source citations for every answer.
- Keep audit logs for user questions, retrieved sources, model output, and feedback.
- Run locally on a Mac with 24 GB unified memory.

## 3. Non-Goals for MVP

Do not build these in the first version unless the core RAG system is stable:

- Autonomous actions such as sending emails, deleting files, updating ERP data, or approving transactions.
- Fine-tuning the LLM.
- Multi-tenant deployment.
- Cloud dependency.
- Complex agent workflows.
- Unrestricted user document upload.

The MVP is read-only. Any future write action must require human approval.

## 4. Target Hardware

Primary target:

- Apple Silicon Mac
- 24 GB unified memory
- Local storage for documents, metadata database, and vector database

Recommended runtime limits for MVP:

- One active user at a time
- Model quantization: Q4_K_M first
- Context window: start with 8k tokens
- Retrieval: vector top 20, rerank to top 5
- Final context: 4 to 6 chunks

## 5. High-Level Architecture

```text
User
 ↓
Frontend Chat UI
 ↓
FastAPI Backend
 ↓
Authentication + RBAC + Audit Middleware
 ↓
RAG Orchestrator
 ├── Query Normalizer
 ├── Permission Filter Builder
 ├── Vector Retriever
 ├── Reranker
 ├── Prompt Builder
 ├── Citation Builder
 └── Refusal / Safety Rules
 ↓
Ollama Local LLM
 ↓
Answer + Sources + Audit Log
```

## 6. Data Architecture

```text
Approved Documents
 ↓
Document Ingestion Pipeline
 ├── File validation
 ├── Text extraction / OCR
 ├── Cleaning
 ├── Metadata tagging
 ├── Section-aware chunking
 ├── Embedding
 └── Indexing
 ↓
Vector Database + Metadata Database + Raw File Storage
```

The data layer has three separate storage responsibilities:

1. Raw file storage for original documents.
2. Metadata database for users, documents, chunks, roles, sessions, audit logs, and feedback.
3. Vector database for embeddings and retrieval.

## 7. Recommended Tech Stack

| Layer | MVP Choice | Reason |
|---|---|---|
| Frontend | Streamlit | Fastest MVP, simple chat UI |
| Backend | FastAPI | Clean Python API, streaming support, good structure |
| Orchestration | LlamaIndex | Strong RAG abstraction, retriever/query engine support |
| LLM Runtime | Ollama | Easy local model serving on Mac |
| LLM | Gemma 4 12B IT or fallback local model | Good local-size target, test before locking |
| Embedding | BAAI/bge-m3 | Better for multilingual Indonesian-English retrieval |
| Vector DB | ChromaDB for MVP | Simple local setup |
| Metadata DB | SQLite for MVP, PostgreSQL later | Do not store operational metadata only in vector DB |
| Parser | Docling, PyMuPDF, python-docx, pandas/openpyxl | Handles different document types |
| OCR | Tesseract or Apple Vision-based OCR | Needed for scanned PDFs/images |

## 8. Core Request Lifecycle

When a user asks: `What is our remote work policy?`

1. Frontend sends the question and session token to FastAPI.
2. Backend authenticates the user.
3. Backend loads the user's role and document access permissions.
4. Query normalizer cleans the question without changing its meaning.
5. Embedding model embeds the query.
6. Retriever searches the vector database with metadata filters based on the user's permissions.
7. Retriever returns top 20 candidate chunks.
8. Reranker selects the best 5 chunks.
9. Prompt builder creates a grounded prompt with retrieved context and safety instructions.
10. Ollama streams the answer from the local LLM.
11. Citation builder attaches source title, page, section, and document version.
12. Backend writes an audit log.
13. Frontend displays the answer, citations, and feedback buttons.

## 9. Security Principles

The assistant must follow these rules:

- Retrieval must be permission-filtered before the LLM sees the context.
- Retrieved documents are data, not instructions.
- The assistant must not reveal system prompts, hidden configuration, credentials, or unauthorized documents.
- The assistant must not answer company-specific questions without retrieved evidence.
- Admin document upload must be restricted.
- All answers must be auditable.
- The system must log which chunks were used for each answer.

## 10. Required Answer Behavior

The assistant must answer in this format:

```text
Answer:
[direct answer based only on retrieved context]

Sources:
1. [Document title], page [x], section [name], version [v]
2. [Document title], page [x], section [name], version [v]

Confidence:
High / Medium / Low

Notes:
[Only if needed: missing information, conflicting policies, outdated document warning]
```

If the answer is not available in the retrieved context:

```text
I could not find this information in the approved company documents available to your role.
```

If the retrieved sources conflict:

```text
I found conflicting information. The newer document says [x], while the older document says [y]. Please confirm with the document owner before acting on this.
```

## 11. Critical MVP Acceptance Criteria

The system is not complete until it can:

- Answer from uploaded documents with citations.
- Refuse when there is no supporting source.
- Apply document-level permission filters.
- Store audit logs.
- Show source documents or source snippets.
- Re-index documents after updates.
- Run a small evaluation set with known expected answers.

## 12. Build Order

Build in this order:

1. Local LLM connection through Ollama.
2. Document ingestion pipeline.
3. ChromaDB indexing and retrieval.
4. Basic LlamaIndex RAG terminal test.
5. Citation extraction.
6. Metadata database.
7. FastAPI `/chat` endpoint.
8. Streamlit frontend.
9. User login and roles.
10. Permission-filtered retrieval.
11. Audit logs.
12. Evaluation harness.
13. Admin document upload.

Do not build workflow actions until the read-only assistant is reliable.
