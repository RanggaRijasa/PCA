# Private Company Assistant: UI Build Specification

## 1. Purpose

This file defines the user interface build specification for the Private Company Assistant.

It must be read together with:

1. `00_SYSTEM_ARCHITECTURE.md`
2. `01_AGENT_BUILD_INSTRUCTIONS.md`
3. `02_FOLDER_STRUCTURE.md`
4. `03_DATA_INGESTION_SPEC.md`
5. `04_RAG_RUNTIME_SPEC.md`
6. `05_SECURITY_AND_PERMISSIONS.md`
7. `06_EVALUATION_SPEC.md`

This UI spec fills the missing frontend context. The first UI milestone must be built before adding the LLM. The UI must work with mock data first, then API stubs, then the real RAG backend.

## 2. Product Goal

Build a local-first web UI for a private company RAG assistant.

The UI must help a company user:

- Ask questions about approved company documents.
- See grounded assistant answers.
- Review source citations used by the assistant.
- Filter answers by department and source collection.
- Browse previous conversations.
- Upload and manage documents if the user is an admin.
- Review ingestion jobs, audit logs, and evaluation results.

The UI must make trust visible. The user should always understand:

- Which documents were used.
- How confident the retrieval was.
- Whether the answer came from company sources.
- Whether the assistant refused due to missing context or permissions.

## 3. UI Technology Choice

### 3.1 Recommended UI Stack

Use this stack for the polished UI shown in the mockup:

- React + TypeScript
- Vite or Next.js
- Tailwind CSS
- shadcn/ui or equivalent reusable components
- Lucide icons or equivalent icon set
- Fetch API or Axios for backend calls

Reason: the target UI has a dashboard layout, left navigation, chat panel, source panel, admin pages, tables, filters, and responsive behavior. React is better suited than Streamlit for this final interface.

### 3.2 Streamlit Alternative

Streamlit may be used only for an internal throwaway prototype. If Streamlit is used, it must not block the React UI. The final MVP UI should follow this specification.

## 4. UI Build Order

The agentic AI must build the UI in this order.

### Phase UI-1: Static UI Only, No Backend, No LLM

Goal: reproduce the dashboard layout from the mockup using hardcoded mock data.

Build:

- App shell
- Left sidebar
- Top header
- Conversation list
- Main chat panel
- Right source panel
- Chat input box
- Filter dropdowns
- Admin navigation items
- Dark mode toggle UI
- Responsive layout

Do not call Ollama.
Do not call LlamaIndex.
Do not call ChromaDB.
Do not implement real ingestion.
Do not implement real authentication.

Use local mock JSON or TypeScript objects.

Acceptance criteria:

- App opens locally.
- Layout matches the provided mockup closely.
- User can type a message and see it appear in the chat using mock behavior.
- Mock assistant response appears after a short simulated delay.
- Source cards display mock source documents.
- No backend is required.

### Phase UI-2: UI State and Mock Interactions

Goal: make the UI feel like a real product while still using mock data.

Build:

- Conversation switching
- New chat creation
- Message streaming simulation
- Source tab switching: `Sources`, `Context`, `Details`
- Department/source filter state
- Follow-up suggestion buttons
- Copy answer button
- Like/dislike feedback buttons
- Source card open/expand state
- Empty states
- Loading states
- Error states

Acceptance criteria:

- Multiple conversations can be selected from mock data.
- The user can start a new chat.
- Follow-up suggestions can populate the input or submit a new mock message.
- Loading skeletons appear before mock responses.
- The UI handles empty conversations gracefully.

### Phase UI-3: API Contract Integration, Still No LLM

Goal: connect the UI to FastAPI mock/stub endpoints.

Build frontend calls to these endpoints:

- `GET /api/health`
- `GET /api/me`
- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `POST /api/conversations`
- `POST /api/chat/mock`
- `POST /api/feedback`
- `GET /api/documents`
- `GET /api/audit-logs`
- `GET /api/evaluation/runs`

The backend may return static JSON at this phase.

Acceptance criteria:

- UI no longer depends only on local mock files.
- API errors display readable UI messages.
- The chat can call `/api/chat/mock` and render the returned answer and sources.
- No LLM call is made yet.

### Phase UI-4: Real RAG Runtime Integration

Goal: connect the UI to the real RAG backend defined in `04_RAG_RUNTIME_SPEC.md`.

Use:

- `POST /api/chat`
- Server-sent events or streaming response if available
- Real citations from the citation builder
- Real permission-aware source filtering
- Real audit logging

Acceptance criteria:

- User question is sent to the backend.
- Backend authenticates user.
- Backend retrieves permission-filtered chunks.
- Assistant answer streams back to the UI.
- Source cards display real documents, pages, sections, and retrieval scores.
- Audit log is written on the backend.

### Phase UI-5: Admin and Evaluation Pages

Goal: expose admin workflows without weakening security.

Build:

- Documents page
- Ingestion page
- Users & Roles page
- Audit Logs page
- Evaluation page
- Settings page

Acceptance criteria:

- Admin pages are visible only to admin users.
- Non-admin users do not see admin navigation items.
- Upload actions are admin-only.
- Evaluation page can show test status, pass/fail counts, and failed cases.

## 5. Visual Design Direction

Follow the uploaded UI mockup.

### 5.1 Overall Style

- Clean enterprise dashboard.
- Light main workspace with dark navy sidebar.
- Purple/blue accent color.
- Rounded cards.
- Soft borders.
- Minimal shadows.
- Dense but readable information layout.
- Professional, not playful.

### 5.2 Main Layout

Desktop layout uses four zones:

```text
┌────────────────────────────────────────────────────────────────────┐
│ Left Sidebar │ Conversation List │ Chat Workspace │ Right Sources │
└────────────────────────────────────────────────────────────────────┘
```

Recommended widths:

```text
Left sidebar: 240px
Conversation list: 300px
Chat workspace: flexible, minimum 520px
Right panel: 360px
```

The UI must remain usable on smaller screens:

- Collapse left sidebar into icon-only or drawer.
- Hide right source panel behind a `Sources` button.
- Conversation list can become a drawer.
- Chat input remains sticky at bottom.

### 5.3 Color Tokens

Use design tokens instead of hardcoded random colors.

```ts
const colors = {
  sidebar: "#06152F",
  sidebarMuted: "#0A1E42",
  primary: "#5B4DFF",
  primaryHover: "#493EE6",
  primarySoft: "#EEF0FF",
  background: "#F8FAFC",
  surface: "#FFFFFF",
  surfaceAlt: "#F4F6FB",
  border: "#E2E8F0",
  text: "#0F172A",
  textMuted: "#64748B",
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444"
}
```

### 5.4 Typography

Use a modern sans-serif font stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Text sizes:

```text
Page title: 28px / 700
Section title: 18px / 700
Card title: 14px / 600
Body: 14px / 400
Small/meta: 12px / 400
Button: 14px / 500
```

### 5.5 Spacing and Radius

```text
Base spacing: 4px
Card padding: 16px to 20px
Panel gap: 16px
Card radius: 12px
Button radius: 10px
Input radius: 10px
```

## 6. App Navigation

### 6.1 Main Navigation

The left sidebar must contain:

Main:

- Chat
- Sources
- Documents
- Reports

Admin:

- Ingestion
- Users & Roles
- Settings
- Audit Logs
- Evaluation

Footer:

- Current user card
- Dark mode toggle
- App version

### 6.2 Role-Based Navigation

Use role-based visibility.

| Route | viewer | staff | manager | admin |
|---|---:|---:|---:|---:|
| Chat | yes | yes | yes | yes |
| Sources | yes | yes | yes | yes |
| Documents | yes | yes | yes | yes |
| Reports | no | yes | yes | yes |
| Ingestion | no | no | no | yes |
| Users & Roles | no | no | no | yes |
| Settings | no | no | no | yes |
| Audit Logs | no | no | no | yes |
| Evaluation | no | no | no | yes |

This is UI visibility only. Backend permissions must still enforce access.

## 7. Required Pages

## 7.1 Chat Page

Route:

```text
/chat
```

Purpose:

Primary interface for asking questions and reviewing grounded answers.

Layout:

```text
Top Bar
- Page title: Chat
- Department filter
- Source filter
- New Chat button
- Expand/focus button
- Notifications icon
- User avatar

Left Conversation Panel
- Search conversations input
- Sort/filter button
- Today section
- Recent conversations
- View all conversations link

Main Chat Workspace
- User message bubble
- Assistant answer card
- Follow-up suggestions card
- Sticky chat input
- Disclaimer text

Right Evidence Panel
- Tabs: Sources, Context, Details
- Top 5 sources used
- Source cards with confidence/relevance score
- View all sources button
```

### 7.1.1 Chat Input Behavior

The input must support:

- Plain text question
- Submit with Enter
- New line with Shift+Enter
- Attach file button visible but disabled in MVP unless admin upload is implemented
- Source scope dropdown
- Send button
- Disabled state while response is streaming

Placeholder:

```text
Ask a question about company policies, procedures, documents...
```

### 7.1.2 Assistant Answer Card

The answer card must show:

- Assistant icon
- Answer text
- Key points if the answer has bullet points
- Timestamp
- Copy button
- Like button
- Dislike button
- Optional `View citations` action

For company-specific answers, the UI must show sources. If no sources exist, show a warning:

```text
No company source was found for this answer. Verify before using.
```

### 7.1.3 Source Cards

Each source card must show:

- Rank number
- File type icon
- Document title
- Department
- Page or section
- Relevance score
- Snippet
- Access level badge if admin user

Example:

```text
1  Remote Work Policy v2.1.pdf      95%
   HR Department • Page 3
   "Employees are eligible to work remotely up to 2 days per week..."
```

### 7.1.4 Right Panel Tabs

`Sources` tab:

- Shows top cited documents.
- Shows relevance score.
- Shows snippets.

`Context` tab:

- Shows retrieved chunk text.
- For admin/debug mode only, show chunk ID and retrieval metadata.
- Hide restricted debug details from normal users.

`Details` tab:

- Shows answer metadata:
  - model name
  - embedding model
  - retrieval top-k
  - reranker used
  - latency
  - conversation ID
  - audit ID

Normal users may see simplified details. Admins may see full details.

## 7.2 Sources Page

Route:

```text
/sources
```

Purpose:

Browse indexed company knowledge sources.

Required UI:

- Search input
- Department filter
- Access level filter
- File type filter
- Status filter
- Table or card list of sources

Columns:

```text
Document title
Department
Access level
Version
Status
Last indexed
Chunk count
Owner
Actions
```

Actions:

- View details
- View chunks
- Re-index, admin only
- Archive, admin only

## 7.3 Documents Page

Route:

```text
/documents
```

Purpose:

Document library view for approved files.

Required UI:

- Document cards/table
- Document preview drawer
- Metadata panel
- Version history
- Source status

Statuses:

```text
approved
pending_ingestion
indexed
failed
archived
```

## 7.4 Reports Page

Route:

```text
/reports
```

Purpose:

Show usage and answer quality summaries.

MVP mock widgets:

- Total questions asked
- Answered with sources
- Refusals
- Average latency
- Top departments queried
- Top documents used
- Feedback summary

Do not invent analytics from real users. Before backend integration, use mock data clearly marked as mock.

## 7.5 Ingestion Page, Admin Only

Route:

```text
/admin/ingestion
```

Purpose:

Admin uploads and monitors document ingestion.

Required UI:

- Upload area
- Required metadata form
- Ingestion queue
- Job status table
- Failed job error details
- Re-index button

Required metadata fields:

```text
title
department
access_level
owner
version
effective_date
expiry_date optional
document_type
```

Ingestion statuses:

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

Rules:

- Upload is admin-only.
- File upload must be disabled for non-admin users.
- UI must show that upload does not mean immediately approved.
- The backend must still validate file type, size, metadata, and permissions.

## 7.6 Users & Roles Page, Admin Only

Route:

```text
/admin/users
```

Purpose:

Manage users, roles, and document access.

Required UI:

- User table
- Role badge
- Department badge
- Status badge
- Last active
- User detail drawer
- Role assignment form
- Explicit restricted document access list

Roles:

```text
viewer
staff
manager
admin
```

## 7.7 Audit Logs Page, Admin Only

Route:

```text
/admin/audit-logs
```

Purpose:

Review who asked what, which sources were retrieved, and what answer was given.

Required UI:

- Search/filter bar
- Date range filter
- User filter
- Role filter
- Event type filter
- Table of audit events
- Detail drawer

Audit event columns:

```text
timestamp
user
role
event_type
question_preview
sources_count
permission_filter
latency_ms
status
```

Detail drawer:

- Full question
- Final answer
- Retrieved source IDs
- Citation list
- Model name
- Safety/refusal status
- Feedback if provided

Do not show raw confidential chunk text to unauthorized admin subroles if future subroles are added.

## 7.8 Evaluation Page, Admin Only

Route:

```text
/admin/evaluation
```

Purpose:

Display evaluation results from `06_EVALUATION_SPEC.md`.

Required UI:

- Run evaluation button
- Latest run summary
- Pass/fail chart or cards
- Category breakdown
- Failed cases table
- Export results button

Metrics shown:

```text
answer_accuracy
retrieval_accuracy
citation_correctness
refusal_correctness
permission_safety
average_latency_ms
```

## 7.9 Settings Page, Admin Only

Route:

```text
/admin/settings
```

Purpose:

Configure safe runtime settings.

Settings groups:

- Model settings
- Retrieval settings
- UI settings
- Security settings
- Backup settings

Fields:

```text
LLM model name
embedding model name
retrieval top_k
rerank top_n
max context chunks
max upload size
allowed file types
audit logging enabled
```

For MVP, settings may be read-only if backend config is environment-based.

## 8. Component Specification

Build reusable components.

### 8.1 Layout Components

```text
AppShell
Sidebar
TopBar
PageContainer
ResizablePanel optional
Drawer
Modal
```

### 8.2 Chat Components

```text
ConversationList
ConversationListItem
ChatThread
UserMessageBubble
AssistantAnswerCard
ChatInput
FollowUpSuggestions
TypingIndicator
StreamingText
FeedbackButtons
```

### 8.3 Source Components

```text
SourcePanel
SourceTabs
SourceCard
SourceSnippet
CitationBadge
ConfidenceBadge
DocumentIcon
```

### 8.4 Admin Components

```text
DocumentTable
DocumentMetadataForm
UploadDropzone
IngestionStatusBadge
UserRoleBadge
AuditLogTable
EvaluationSummaryCards
EvaluationFailedCasesTable
```

### 8.5 Common Components

```text
Button
IconButton
Input
Textarea
Select
Badge
Card
Tabs
Table
Toast
Skeleton
EmptyState
ErrorState
```

## 9. Frontend Data Models

Use TypeScript types.

```ts
export type UserRole = "viewer" | "staff" | "manager" | "admin";

export type AccessLevel =
  | "public_internal"
  | "staff"
  | "manager"
  | "admin"
  | "restricted";

export type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  department: string;
  avatarUrl?: string;
  status: "active" | "disabled";
};

export type Conversation = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
  sources?: SourceCitation[];
  metadata?: AnswerMetadata;
  status?: "pending" | "streaming" | "complete" | "error" | "refused";
};

export type SourceCitation = {
  id: string;
  documentId: string;
  chunkId?: string;
  title: string;
  fileName: string;
  fileType: "pdf" | "docx" | "txt" | "md" | "xlsx" | "csv" | "pptx" | "image";
  department: string;
  accessLevel: AccessLevel;
  page?: number;
  section?: string;
  snippet: string;
  relevanceScore?: number;
  citationRank: number;
};

export type AnswerMetadata = {
  modelName?: string;
  embeddingModel?: string;
  retrievalTopK?: number;
  rerankTopN?: number;
  latencyMs?: number;
  auditId?: string;
  refused?: boolean;
  refusalReason?: string;
};

export type DocumentSource = {
  id: string;
  title: string;
  fileName: string;
  fileType: string;
  department: string;
  accessLevel: AccessLevel;
  version: string;
  owner: string;
  status: "approved" | "pending_ingestion" | "indexed" | "failed" | "archived";
  lastIndexedAt?: string;
  chunkCount?: number;
};
```

## 10. API Contracts for UI

The UI must be built against these contracts. During UI-only phases, mock these responses.

### 10.1 Health

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "mode": "mock"
}
```

### 10.2 Current User

```http
GET /api/me
```

Response:

```json
{
  "id": "user_001",
  "name": "Andrew Davis",
  "email": "andrew@company.local",
  "role": "manager",
  "department": "HR",
  "status": "active"
}
```

### 10.3 Conversations

```http
GET /api/conversations
```

Response:

```json
{
  "items": [
    {
      "id": "conv_001",
      "title": "Remote work policy",
      "createdAt": "2026-06-12T10:24:00Z",
      "updatedAt": "2026-06-12T10:24:00Z"
    }
  ]
}
```

### 10.4 Conversation Detail

```http
GET /api/conversations/{conversation_id}
```

Response:

```json
{
  "id": "conv_001",
  "title": "Remote work policy",
  "createdAt": "2026-06-12T10:24:00Z",
  "updatedAt": "2026-06-12T10:24:00Z",
  "messages": []
}
```

### 10.5 Create Conversation

```http
POST /api/conversations
```

Request:

```json
{
  "title": "New chat"
}
```

Response:

```json
{
  "id": "conv_002",
  "title": "New chat",
  "createdAt": "2026-06-12T10:30:00Z",
  "updatedAt": "2026-06-12T10:30:00Z"
}
```

### 10.6 Mock Chat, Before LLM

```http
POST /api/chat/mock
```

Request:

```json
{
  "conversationId": "conv_001",
  "message": "What is our policy on remote work?",
  "departmentFilter": "all",
  "sourceFilter": "all"
}
```

Response:

```json
{
  "messageId": "msg_002",
  "answer": "According to the company's current policy, employees are eligible to work remotely up to 2 days per week with manager approval.",
  "sources": [
    {
      "id": "src_001",
      "documentId": "doc_001",
      "title": "Remote Work Policy v2.1.pdf",
      "fileName": "Remote Work Policy v2.1.pdf",
      "fileType": "pdf",
      "department": "HR Department",
      "accessLevel": "staff",
      "page": 3,
      "section": "Remote Work Eligibility",
      "snippet": "Employees are eligible to work remotely up to 2 days per week with manager approval...",
      "relevanceScore": 0.95,
      "citationRank": 1
    }
  ],
  "metadata": {
    "modelName": "mock-model",
    "embeddingModel": "mock-embedding",
    "retrievalTopK": 20,
    "rerankTopN": 5,
    "latencyMs": 420,
    "auditId": "audit_mock_001"
  }
}
```

### 10.7 Real Chat, After RAG Backend Exists

```http
POST /api/chat
```

Request:

```json
{
  "conversationId": "conv_001",
  "message": "What is our policy on remote work?",
  "departmentFilter": "all",
  "sourceFilter": "all"
}
```

Response may be JSON or streaming events.

Final response shape must resolve to:

```json
{
  "messageId": "msg_003",
  "answer": "...",
  "sources": [],
  "metadata": {}
}
```

### 10.8 Feedback

```http
POST /api/feedback
```

Request:

```json
{
  "messageId": "msg_002",
  "rating": "up",
  "comment": "Useful answer"
}
```

Response:

```json
{
  "status": "ok"
}
```

## 11. Mock Data Requirements

Create mock data in:

```text
frontend/src/mocks/
├── users.ts
├── conversations.ts
├── documents.ts
├── sources.ts
├── auditLogs.ts
├── evaluationRuns.ts
└── reports.ts
```

Mock conversations must include at least:

- Remote work policy
- Overtime reimbursement
- Sick leave entitlement
- Laptop procurement process
- Code of conduct questions
- Benefits for new employees
- Data retention policy

Mock sources must include:

- Remote Work Policy v2.1.pdf
- Employee Handbook 2024.pdf
- Flexible Work Guidelines.docx
- Internship Policy v1.0.pdf
- IT Security Policy v3.0.pdf

## 12. State Management

For MVP, use React local state and context.

Recommended structure:

```text
AuthContext
ThemeContext
ChatContext
ToastContext
```

Do not add Redux unless the app becomes complex enough to justify it.

Required state:

```text
currentUser
activeConversationId
conversations
messages
selectedDepartmentFilter
selectedSourceFilter
rightPanelTab
darkMode
isStreaming
error
```

## 13. Error and Empty States

Every major panel must have empty and error states.

Examples:

### Empty Conversation

```text
Ask your first question about company documents.
```

### No Sources Found

```text
No company sources were found for this answer. Try changing the source filter or ask an admin to check the indexed documents.
```

### Permission Refusal

```text
I cannot answer this because your current role does not have access to the required documents.
```

### No Context Refusal

```text
I could not find enough information in the approved company documents to answer this confidently.
```

### Backend Offline

```text
The local backend is not reachable. Check that FastAPI is running.
```

### Ollama Offline, After LLM Integration

```text
The local LLM service is not reachable. Check that Ollama is running.
```

## 14. Accessibility Requirements

The UI must be keyboard usable and screen-reader friendly.

Minimum requirements:

- Use semantic HTML where possible.
- Buttons must be actual `<button>` elements.
- Inputs must have labels, even if visually hidden.
- Sidebar navigation must be keyboard accessible.
- Tab panels must use accessible tab behavior.
- Modals and drawers must trap focus.
- Color contrast must be readable.
- Do not rely on color alone for statuses.
- Chat messages must be readable by screen readers.
- Streaming answer updates should not constantly interrupt screen reader users.

## 15. Security-Related UI Rules

The UI must not pretend to enforce security by itself. Backend security is the source of truth.

Still, the UI must:

- Hide admin menus from non-admin users.
- Disable restricted actions for non-admin users.
- Never store raw auth tokens in insecure places if real auth is added.
- Never display full restricted chunks to unauthorized users.
- Show clear refusal messages for permission restrictions.
- Show source access labels for admin users.
- Not expose hidden prompts, system messages, or backend config.

Prompt injection content inside retrieved chunks must be treated as source text, not UI instructions.

## 16. Performance Requirements

MVP performance targets on local machine:

```text
Initial UI load: under 2 seconds after dev server starts
Conversation switch: under 300 ms with mock data
Mock response delay: 300 to 800 ms
Chat input typing: no lag
Source panel render: under 300 ms for top 5 sources
Documents page: support at least 500 document rows with pagination or virtualized table
Audit logs page: support pagination
```

After LLM integration:

```text
Show streaming token output as soon as backend starts responding
Show source skeletons while retrieval is running
Show final sources when available
Never freeze the UI while waiting for the LLM
```

## 17. Recommended Frontend Folder Structure

If using React + Vite:

```text
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes.tsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   ├── chat/
│   │   ├── sources/
│   │   ├── admin/
│   │   └── common/
│   │
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── SourcesPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── ReportsPage.tsx
│   │   ├── admin/
│   │   │   ├── IngestionPage.tsx
│   │   │   ├── UsersRolesPage.tsx
│   │   │   ├── AuditLogsPage.tsx
│   │   │   ├── EvaluationPage.tsx
│   │   │   └── SettingsPage.tsx
│   │
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── chatApi.ts
│   │   ├── documentsApi.ts
│   │   └── adminApi.ts
│   │
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useConversations.ts
│   │   ├── useCurrentUser.ts
│   │   └── useTheme.ts
│   │
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   ├── ChatContext.tsx
│   │   └── ThemeContext.tsx
│   │
│   ├── mocks/
│   ├── types/
│   ├── utils/
│   └── styles/
│       └── globals.css
```

Update `02_FOLDER_STRUCTURE.md` later to include this structure if the project uses React as final frontend.

## 18. UI Acceptance Checklist

Before adding the LLM, the UI must pass this checklist:

- [ ] App shell is complete.
- [ ] Sidebar navigation is complete.
- [ ] Chat page matches the mockup.
- [ ] Conversation list works with mock data.
- [ ] User can create a new mock chat.
- [ ] User can submit a mock question.
- [ ] Mock assistant response appears.
- [ ] Right source panel shows top sources.
- [ ] Source, Context, and Details tabs work.
- [ ] Follow-up suggestions work.
- [ ] Copy answer button works.
- [ ] Feedback buttons work.
- [ ] Empty states are implemented.
- [ ] Loading states are implemented.
- [ ] Error states are implemented.
- [ ] Role-based menu visibility works with mock users.
- [ ] Admin pages exist with mock data.
- [ ] Responsive layout is usable.
- [ ] Basic accessibility requirements are met.
- [ ] No LLM calls are made.
- [ ] No ChromaDB calls are made.
- [ ] No Ollama calls are made.

## 19. Handoff Rule for Agentic AI

When using an agentic AI coding tool, give it this instruction:

```text
Read all Markdown files in the project context, especially 07_UI_BUILD_SPEC.md.
Build the UI in phases.
First implement Phase UI-1 and Phase UI-2 only.
Use mock data.
Do not connect to Ollama, LlamaIndex, ChromaDB, or the real RAG backend yet.
Do not add real authentication yet.
Create a clean React + TypeScript frontend that matches the provided mockup.
After the UI-only version works, document what was completed and what remains before API integration.
```

## 20. Definition of Done for UI-Only MVP

The UI-only MVP is done when:

- A reviewer can run the frontend locally.
- The dashboard visually matches the provided design direction.
- Chat interactions work with mock data.
- Source citations are represented in the UI.
- Admin pages are present but clearly mock-only.
- Role-based visibility is simulated.
- The code is organized by components, pages, services, types, mocks, and contexts.
- There is no dependency on a running LLM.
- There is no dependency on backend RAG services.

