import type { AuditLog } from "../types";

export const mockAuditLogs: AuditLog[] = [
  { id: "audit_001", timestamp: "2026-06-12T03:24:01Z", user: "Maya Putri", role: "admin", eventType: "mock_chat", questionPreview: "What is our policy on remote work?", question: "What is our policy on remote work?", sourcesCount: 0, documentIds: [], chunkIds: [], citations: [], permissionFilter: "admin", permissionFilterData: {}, latencyMs: 420, modelName: "mock-model", answerHash: "mock", refused: false, status: "answered" },
  { id: "audit_002", timestamp: "2026-06-11T08:14:10Z", user: "Andrew Davis", role: "manager", eventType: "mock_chat", questionPreview: "Can I approve my own overtime?", question: "Can I approve my own overtime?", sourcesCount: 0, documentIds: [], chunkIds: [], citations: [], permissionFilter: "manager", permissionFilterData: {}, latencyMs: 306, modelName: "mock-model", answerHash: "mock", refused: true, status: "refused" },
];
