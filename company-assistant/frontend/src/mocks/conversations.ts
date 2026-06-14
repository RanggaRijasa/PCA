import type { Conversation } from "../types";
import { mockSources } from "./sources";

export const mockAnswer = `Answer:
Employees are eligible to work remotely up to two days per week with manager approval. The schedule should maintain team coverage and be recorded in the shared calendar in advance.

Sources:
1. Remote Work Policy v2.1, Remote Work Policy v2.1.pdf, page 3, section Remote Work Eligibility, version v2.1
2. Employee Handbook 2024, Employee Handbook 2024.pdf, page 18, section Flexible Working, version 2024

Confidence:
High

Notes:
This is mock Phase 2 data for interface and API contract testing only.`;

export const mockConversations: Conversation[] = [
  {
    id: "conv_001",
    title: "Remote work policy",
    createdAt: "2026-06-12T03:24:00Z",
    updatedAt: "2026-06-12T03:26:00Z",
    messages: [
      { id: "msg_001", role: "user", content: "What is our policy on remote work?", createdAt: "2026-06-12T03:24:00Z", status: "complete" },
      { id: "msg_002", role: "assistant", content: mockAnswer, createdAt: "2026-06-12T03:24:01Z", status: "complete", sources: mockSources, metadata: { modelName: "mock-model", embeddingModel: "mock-embedding", retrievalTopK: 20, rerankTopN: 5, latencyMs: 420, auditId: "audit_mock_001", refused: false } },
    ],
  },
  ...[
    ["conv_002", "Overtime reimbursement"],
    ["conv_003", "Sick leave entitlement"],
    ["conv_004", "Laptop procurement process"],
    ["conv_005", "Code of conduct questions"],
    ["conv_006", "Benefits for new employees"],
    ["conv_007", "Data retention policy"],
  ].map(([id, title], index) => ({
    id,
    title,
    createdAt: `2026-06-${String(11 - index).padStart(2, "0")}T08:14:00Z`,
    updatedAt: `2026-06-${String(11 - index).padStart(2, "0")}T08:17:00Z`,
    messages: [],
  })),
];

