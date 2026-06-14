---
name: ui-builder
description: Use when building the React TypeScript UI, dashboard shell, chat page, source panel, admin pages, mock data, UI states, or responsive layout.
---

# UI Builder Skill

## Purpose

Build the Private Company Assistant frontend according to `docs/07_UI_BUILD_SPEC.md`.

## Critical Rule

Build UI-only first. During UI-only phases:

- Do not call Ollama.
- Do not call LlamaIndex.
- Do not call ChromaDB.
- Do not call the real RAG backend.
- Do not implement real authentication.
- Use mock data only.

## Recommended Stack

Use:

- React + TypeScript.
- Vite or Next.js.
- Tailwind CSS.
- shadcn/ui or equivalent reusable components.
- Lucide icons or equivalent.

## Required Layout

Match the provided dashboard mockup:

```text
Left sidebar | Conversation list | Main chat workspace | Right evidence panel
```

Default desktop widths:

- Left sidebar: 240px.
- Conversation list: 300px.
- Chat workspace: flexible, minimum 520px.
- Right panel: 360px.

## Required Pages

Build these pages with mock data first:

- `/chat`
- `/sources`
- `/documents`
- `/reports`
- `/admin/ingestion`
- `/admin/users`
- `/admin/audit-logs`
- `/admin/evaluation`
- `/admin/settings`

## Required Chat Features

- Conversation list.
- New chat button.
- User message bubble.
- Assistant answer card.
- Follow-up suggestions.
- Sticky chat input.
- Department filter.
- Source filter.
- Source panel with tabs: `Sources`, `Context`, `Details`.
- Source cards with rank, file type, title, department, page/section, score, and snippet.
- Copy answer button.
- Like/dislike buttons.
- Empty, loading, and error states.

## Mock Data Location

Create mock data under:

```text
frontend/src/mocks/
```

Include:

- `users.ts`
- `conversations.ts`
- `documents.ts`
- `sources.ts`
- `auditLogs.ts`
- `evaluationRuns.ts`
- `reports.ts`

## State Management

Use local React state and context first:

- `AuthContext`
- `ThemeContext`
- `ChatContext`
- `ToastContext`

Do not add Redux unless requested.

## Role-Based UI Visibility

Hide admin navigation items from non-admin mock users. This is UI-only convenience, not real security. Backend must enforce real permissions later.

## Accessibility Requirements

- Use semantic HTML.
- Buttons must be real `<button>` elements.
- Inputs need labels.
- Sidebar and tabs must be keyboard accessible.
- Do not rely on color alone for status.
- Chat messages must be readable by screen readers.

## Done Criteria

The UI-only MVP is done when:

- Frontend runs locally.
- UI matches the mockup direction.
- User can create/select mock conversations.
- User can submit a mock question.
- Mock assistant response appears.
- Sources, Context, and Details tabs work.
- Admin pages exist with mock data.
- No LLM/backend/vector DB dependency exists.
