import { mockAuditLogs } from "../mocks/auditLogs";
import { mockAnswer, mockConversations } from "../mocks/conversations";
import { mockDocuments } from "../mocks/documents";
import { mockEvaluationRuns } from "../mocks/evaluationRuns";
import { mockSources } from "../mocks/sources";
import { mockUsers } from "../mocks/users";
import type { Conversation, ConversationSummary, MockChatResponse } from "../types";

const conversations: Conversation[] = structuredClone(mockConversations);
const delay = (milliseconds = 350) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export const localMockApi = {
  async getCurrentUser() {
    await delay(180);
    return structuredClone(mockUsers[3]);
  },
  async listConversations() {
    await delay(260);
    return conversations.map(({ messages: _messages, ...summary }) => summary);
  },
  async getConversation(id: string) {
    await delay(220);
    const conversation = conversations.find((item) => item.id === id);
    if (!conversation) throw new Error("Conversation not found");
    return structuredClone(conversation);
  },
  async createConversation(title: string): Promise<ConversationSummary> {
    await delay(220);
    const now = new Date().toISOString();
    const conversation: Conversation = { id: `conv_${crypto.randomUUID().slice(0, 8)}`, title, createdAt: now, updatedAt: now, messages: [] };
    conversations.unshift(conversation);
    const { messages: _messages, ...summary } = conversation;
    return summary;
  },
  async sendMockChat(): Promise<MockChatResponse> {
    await delay(520);
    return { messageId: `msg_${crypto.randomUUID().slice(0, 8)}`, answer: mockAnswer, sources: structuredClone(mockSources), metadata: { modelName: "mock-model", embeddingModel: "mock-embedding", retrievalTopK: 20, rerankTopN: 5, latencyMs: 520, auditId: `audit_mock_${crypto.randomUUID().slice(0, 8)}` } };
  },
  async submitFeedback() {
    await delay(160);
    return { status: "ok" };
  },
  async listDocuments() {
    await delay(260);
    return structuredClone(mockDocuments);
  },
  async listAuditLogs() {
    await delay(260);
    return structuredClone(mockAuditLogs);
  },
  async listEvaluationRuns() {
    await delay(260);
    return structuredClone(mockEvaluationRuns);
  },
};

