# Private Company Assistant: Gemma 4 12B IT QAT Q4 and Multimodal Upgrade Specification

## 1. Purpose

This document defines the post-MVP upgrade path for moving the Private Company Assistant from a lightweight development model such as `gemma3:1b` to a smarter local production-quality model target: **Gemma 4 12B IT QAT Q4**.

It also defines the future **vision and audio upgrade path** for the assistant.

This file must be implemented only after the main MVP is complete, including:

1. UI-only MVP
2. FastAPI mock/stub backend
3. Ollama health check
4. SQLite metadata database
5. document ingestion
6. retrieval-only test
7. terminal RAG
8. real `/api/chat` streaming
9. real authentication and permission-filtered retrieval
10. audit logs and feedback
11. evaluation harness
12. admin upload and ingestion management
13. backup, reset, tests, README, and local packaging

Do not implement this file before the final MVP prompt is completed.

## 2. Source of Truth Relationship

This file extends the existing project documentation:

1. `00_SYSTEM_ARCHITECTURE.md`
2. `01_AGENT_BUILD_INSTRUCTIONS.md`
3. `02_FOLDER_STRUCTURE.md`
4. `03_DATA_INGESTION_SPEC.md`
5. `04_RAG_RUNTIME_SPEC.md`
6. `05_SECURITY_AND_PERMISSIONS.md`
7. `06_EVALUATION_SPEC.md`
8. `07_UI_BUILD_SPEC.md`
9. `08_MODEL_UPGRADE_MULTIMODAL_SPEC.md`

If this file conflicts with security, permissions, audit logging, or source-grounding rules, follow:

1. `05_SECURITY_AND_PERMISSIONS.md`
2. `04_RAG_RUNTIME_SPEC.md`
3. `00_SYSTEM_ARCHITECTURE.md`
4. this file

Security and permission filtering always take priority over model capability.

## 3. Upgrade Goals

The upgrade has three goals:

1. Replace the development model with **Gemma 4 12B IT QAT Q4** or the closest available local runtime tag.
2. Keep the model configurable through `.env` and backend settings, not hardcoded in UI or backend logic.
3. Add future-ready vision and audio processing capability without breaking the text RAG MVP.

## 4. Non-Goals

Do not implement these as part of the first model upgrade:

- fine-tuning Gemma 4
- cloud inference
- automatic decision-making
- autonomous company workflow actions
- sending emails
- modifying ERP/POS/CRM records
- deleting files
- approving HR, finance, or operational actions
- replacing document permission filtering with model-based refusal
- using the LLM as an embedding model

The assistant remains a grounded, permission-aware RAG system.

## 5. Model Configuration Rules

The active LLM must be configurable through environment variables.

Example `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma4:12b
LLM_TARGET_FAMILY=gemma4
LLM_TARGET_VARIANT=12b-it-qat-q4
EMBED_MODEL=BAAI/bge-m3
```

Example `.env.example`:

```env
# Fast development model
# LLM_MODEL=gemma3:1b

# Recommended local quality model for the Private Company Assistant
LLM_MODEL=gemma4:12b
LLM_TARGET_FAMILY=gemma4
LLM_TARGET_VARIANT=12b-it-qat-q4

# Embeddings stay separate from the LLM
EMBED_MODEL=BAAI/bge-m3
```

Important rules:

- Do not hardcode `gemma3:1b`, `gemma4:12b`, or any specific model name inside UI components.
- Do not hardcode model names inside backend business logic.
- Backend config must load the model from `.env`.
- UI Details panel must display the model name returned by backend metadata.
- If the installed Ollama tag differs from `gemma4:12b`, document the exact tag in `README.md` and `.env.example`.

## 6. Runtime Model Selection

The backend should expose active model metadata through every real chat response.

Example response metadata:

```json
{
  "metadata": {
    "mode": "Local RAG",
    "modelName": "gemma4:12b",
    "modelTargetVariant": "12b-it-qat-q4",
    "embeddingModel": "BAAI/bge-m3",
    "retrievalTopK": 20,
    "rerankTopN": 5,
    "maxContextChunks": 6,
    "supportsVision": true,
    "supportsAudio": true,
    "latencyMs": 4820,
    "auditId": "audit_xxx"
  }
}
```

The UI Details tab should display:

```text
Mode: Local RAG
Model: gemma4:12b
Target Variant: 12B IT QAT Q4
Embedding: bge-m3
Initial top-k: 20
Rerank top-n: 5
Vision: Available / Disabled / Not configured
Audio: Available / Disabled / Not configured
Retrieval: [x] ms
Generation: [x] ms
Latency: [x] ms
Conversation: [id]
Audit ID: [id]
```

## 7. Hardware Target

Primary target:

- Apple Silicon Mac
- 24 GB unified memory
- local model runtime through Ollama or equivalent local inference runtime

Recommended first settings:

```text
Model: Gemma 4 12B IT QAT Q4 or available local equivalent
Quantization: Q4 first
Context window: 8k first
Initial vector retrieval: top 20
Rerank: top 5
Final context chunks: 4 to 6
Active users: 1 at a time for MVP/local deployment
```

Only increase context size after measuring memory and latency.

## 8. Model Upgrade Implementation Plan

### Phase 8A: Config-Only Model Switch

Goal: switch from development model to Gemma 4 12B without changing RAG logic.

Tasks:

1. Update `.env.example` with Gemma 4 12B target values.
2. Confirm `backend/config.py` reads model values from environment variables.
3. Confirm `backend/llm/ollama_client.py` uses `LLM_MODEL` from config.
4. Confirm no UI component hardcodes the model name.
5. Confirm the Details tab displays model metadata returned by the backend.
6. Add README instructions for installing/pulling the target model.

Acceptance criteria:

- changing `LLM_MODEL` in `.env` changes the active model without code changes
- `/api/chat` metadata shows the active model
- `scripts/check_ollama.py` tests the configured model
- UI Details tab displays the configured model name
- all previous text RAG tests still pass

### Phase 8B: Quality Regression Test

Goal: verify that Gemma 4 improves answer quality without breaking grounding or permissions.

Tasks:

1. Run the existing evaluation suite using the old model.
2. Save report as `eval/reports/YYYY-MM-DD-old-model.md`.
3. Switch to Gemma 4 12B.
4. Run the same evaluation suite again.
5. Save report as `eval/reports/YYYY-MM-DD-gemma4-12b.md`.
6. Compare:
   - answer correctness
   - citation correctness
   - refusal correctness
   - permission correctness
   - latency
   - hallucination rate

Acceptance criteria:

- permission correctness remains 100%
- no critical data leakage
- citation correctness does not regress
- refusal behavior does not regress
- latency is documented
- memory/performance notes are added to README

### Phase 8C: Prompt Compatibility Review

Goal: make sure Gemma 4 follows the project answer format.

Required answer format remains:

```text
Answer:
Sources:
Confidence:
Notes:
```

Tasks:

1. Test direct policy questions.
2. Test no-answer questions.
3. Test permission-restricted questions.
4. Test prompt injection attempts.
5. Test Indonesian, English, and mixed-language questions.
6. Test longer multi-document questions.

Acceptance criteria:

- Gemma 4 follows answer format consistently
- no unsupported company-specific claims are added
- hidden prompts, credentials, and restricted documents are not exposed
- retrieved documents are treated as reference data, not instructions

## 9. Vision Upgrade Scope

Vision support is a post-MVP feature.

It must not replace the text document RAG system.

Vision support should be added for these use cases:

1. User uploads an image and asks a question about it.
2. User uploads a screenshot of a company system and asks for explanation.
3. User uploads an image of a form, label, receipt, machine panel, whiteboard, or document page.
4. Admin optionally ingests image-derived text into the knowledge base after approval.

Do not allow image uploads to become searchable company knowledge automatically.

## 10. Vision Request Flow

For ad-hoc image questions:

```text
User uploads image
 ↓
Backend validates file type and size
 ↓
Backend checks user authentication
 ↓
Backend stores temporary media record
 ↓
Backend sends image + text prompt to multimodal model
 ↓
Model returns answer
 ↓
Backend writes audit log with media reference
 ↓
UI displays answer and media attachment reference
```

For image-to-knowledge ingestion:

```text
Admin uploads image
 ↓
Backend validates file
 ↓
OCR or model-assisted extraction runs
 ↓
Extracted text is shown for admin review
 ↓
Admin provides metadata and approves
 ↓
Text is chunked and embedded
 ↓
Chunks are indexed in vector DB
 ↓
Metadata is stored in SQLite
```

## 11. Vision Security Rules

- Image upload must obey the same authentication and role rules as document upload.
- Non-admin ad-hoc image uploads must not be added to the searchable company knowledge base.
- Admin image ingestion must require metadata and approval.
- Temporary media must have retention controls.
- Audit logs must record image usage without storing secrets or unnecessary raw content in logs.
- If an image contains credentials, private customer data, payroll data, or restricted documents, the assistant must apply permission and safety rules.
- The model must not infer private identity, protected traits, or sensitive personal details from images unless explicitly required for a valid company workflow and allowed by policy.

## 12. Vision Backend Additions

Recommended new modules:

```text
backend/media/
├── __init__.py
├── models.py
├── storage.py
├── validator.py
├── image_processor.py
└── retention.py
```

Recommended API endpoints:

```text
POST /api/chat/with-image
POST /api/media/upload-temp
GET  /api/media/{media_id}
DELETE /api/media/{media_id}
POST /api/admin/media/ingest-image
```

Recommended database tables:

```text
media_assets
media_audit_events
media_extractions
```

Example `media_assets` fields:

```text
id
uploaded_by_user_id
file_name
mime_type
file_hash
storage_path
purpose: chat_temp | admin_ingestion | evaluation
access_level
department
created_at
expires_at
status
```

## 13. Vision UI Additions

Chat input:

- enable image attachment after backend support exists
- show selected image preview
- show remove attachment button
- show upload validation errors
- show clear note when image is used only for the current chat and not added to knowledge base

Right Details panel:

```text
Input type: Text + Image
Image count: 1
Model: gemma4:12b
Vision: enabled
Audit ID: audit_xxx
```

Admin ingestion page:

- add image file type support only for admin
- show extracted text preview
- require metadata before indexing
- require approval before searchable indexing

## 14. Audio Upgrade Scope

Audio support is also post-MVP.

Audio support should be added for these use cases:

1. User uploads a meeting audio file and asks for a summary.
2. User uploads a training audio clip and asks for key points.
3. User uploads audio from a company event and asks for action items.
4. Admin optionally converts approved audio transcripts into searchable knowledge.

Do not add audio to the searchable company knowledge base automatically.

## 15. Audio Request Flow

For ad-hoc audio questions:

```text
User uploads audio
 ↓
Backend validates file type, size, and duration
 ↓
Backend checks user authentication
 ↓
Backend stores temporary media record
 ↓
Backend sends audio + text prompt to multimodal model or transcription pipeline
 ↓
Model returns answer or transcript summary
 ↓
Backend writes audit log with media reference
 ↓
UI displays answer and media attachment reference
```

For audio-to-knowledge ingestion:

```text
Admin uploads audio
 ↓
Backend validates file
 ↓
Audio transcription runs
 ↓
Transcript is shown for admin review
 ↓
Admin corrects transcript if needed
 ↓
Admin provides metadata and approves
 ↓
Transcript is chunked and embedded
 ↓
Chunks are indexed in vector DB
 ↓
Metadata is stored in SQLite
```

## 16. Audio Security Rules

- Audio upload must require authentication.
- Admin audio ingestion must require metadata and approval.
- Meeting audio may contain sensitive personal or business data.
- Audio transcripts must inherit the same access level and department metadata as documents.
- Audio files and transcripts must have retention and deletion rules.
- Audit logs must record audio use without storing secrets unnecessarily.
- If audio contains restricted information, the assistant must not expose it to unauthorized users.

## 17. Audio Backend Additions

Recommended modules:

```text
backend/media/
├── audio_processor.py
├── transcription.py
└── diarization.py
```

Recommended API endpoints:

```text
POST /api/chat/with-audio
POST /api/media/upload-audio-temp
POST /api/admin/media/ingest-audio
```

Recommended database fields for audio media:

```text
mime_type
duration_seconds
transcript_status
transcript_path
speaker_count optional
language optional
```

## 18. Audio UI Additions

Chat input:

- enable audio attachment after backend support exists
- show selected audio file name
- show duration if available
- show remove attachment button
- show upload validation errors
- show note that audio is not added to the knowledge base unless an admin ingests it

Right Details panel:

```text
Input type: Text + Audio
Audio count: 1
Duration: [x] seconds
Model: gemma4:12b
Audio: enabled
Audit ID: audit_xxx
```

Admin ingestion page:

- add audio upload support only for admin
- show transcript preview
- allow transcript correction before indexing
- require metadata before indexing
- require approval before searchable indexing

## 19. Multimodal RAG Policy

The text RAG system remains the primary source of company knowledge.

For multimodal chat:

```text
User question + uploaded media
 ↓
Permission check
 ↓
Optional retrieval from company documents if user asks company-specific question
 ↓
Multimodal model receives media plus retrieved context
 ↓
Answer includes citations for retrieved company documents
 ↓
Answer references uploaded media separately
 ↓
Audit log records both document sources and media references
```

Important rules:

- Uploaded media is not automatically a trusted company source.
- Uploaded media cannot override approved company documents.
- If the user asks a company policy question with an image or audio file, the answer must still use approved company sources.
- If media content conflicts with approved documents, mention the conflict.
- If retrieved context is missing, refuse company-specific claims even if the model thinks it can infer them from the media.

## 20. Evaluation Additions

Create a new evaluation file:

```text
eval/multimodal_test_cases.csv
```

Recommended columns:

```csv
id,category,user_role,input_type,media_file,question,expected_behavior,expected_source,expected_answer_keywords
```

Required categories:

```text
image_ocr
image_screenshot
image_form
image_no_answer
audio_transcription
audio_summary
audio_action_items
audio_permission_restricted
multimodal_prompt_injection
company_policy_with_media
```

Required metrics:

```text
media_processing_success
answer_correctness
citation_correctness
refusal_correctness
permission_correctness
latency
media_retention_correctness
```

Acceptance criteria:

- text RAG evaluation still passes
- permission correctness remains 100%
- no critical data leakage
- media files are not indexed unless admin-approved
- media audit logs are written
- uploaded media can be deleted according to retention policy

## 21. Files to Update When Implementing This Spec

Update:

```text
.env.example
README.md
backend/config.py
backend/llm/ollama_client.py
backend/api/chat.py
backend/rag/service.py
backend/db/schema.py
backend/db/audit.py
frontend/src/types/
frontend/src/components/chat/ChatInput.tsx
frontend/src/components/sources/SourcePanel.tsx
frontend/src/pages/admin/IngestionPage.tsx
eval/run_eval.py
```

Add:

```text
backend/media/
eval/multimodal_test_cases.csv
tests/test_model_config.py
tests/test_media_validation.py
tests/test_multimodal_permissions.py
tests/test_media_retention.py
```

## 22. Implementation Order After Final MVP

Implement in this order:

1. Config-only Gemma 4 model switch
2. Model health check update
3. UI Details model metadata update
4. Text RAG regression evaluation with Gemma 4
5. Prompt compatibility fixes
6. Vision ad-hoc chat support
7. Vision admin ingestion support
8. Audio ad-hoc chat support
9. Audio admin ingestion support
10. Multimodal evaluation harness
11. Media retention and backup integration
12. Documentation and final handoff

Do not start vision or audio until the text model switch is stable and evaluation passes.

## 23. Agentic AI Handoff Prompt

Use this prompt only after the final MVP build is complete.

```text
Read AGENTS.md, all docs/*.md files, and all .agent/skills/**/SKILL.md files before continuing.

Now read docs/08_MODEL_UPGRADE_MULTIMODAL_SPEC.md.

Implement only Phase 8A, 8B, and 8C first:

1. Make the LLM model fully configurable through .env.
2. Update .env.example and README for the Gemma 4 12B IT QAT Q4 target.
3. Confirm the backend uses LLM_MODEL from config everywhere.
4. Confirm the UI Details panel displays the active model from backend metadata.
5. Run evaluation before and after switching models.
6. Document answer quality, citation correctness, refusal correctness, permission correctness, and latency.

Do not implement vision or audio yet.
Stop after the text model upgrade and write a handoff note.
```

## 24. Definition of Done for Model Upgrade

The Gemma 4 model upgrade is done when:

- active model is controlled by `.env`
- backend uses the configured model
- UI displays the configured model from backend metadata
- `scripts/check_ollama.py` tests the configured model
- text RAG evaluation passes
- permission correctness remains 100%
- no critical data leakage occurs
- latency is documented
- README explains how to switch models

## 25. Definition of Done for Multimodal Upgrade

The vision/audio upgrade is done when:

- image upload works for ad-hoc chat
- audio upload works for ad-hoc chat
- admin image/audio ingestion requires metadata and approval
- media is not automatically added to searchable knowledge
- media audit logs are written
- media retention/deletion rules exist
- multimodal evaluation runs
- permission correctness remains 100%
- no critical data leakage occurs
- README explains limitations and supported media types

