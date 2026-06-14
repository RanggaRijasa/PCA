import type { ChatStreamEvent, Conversation, ConversationSummary, MockChatResponse, User } from "../types";
import { API_BASE_URL, ApiError, apiRequest, useLocalMocks } from "./apiClient";
import { localMockApi } from "./mockApi";

export async function getCurrentUser(): Promise<User> {
  return useLocalMocks ? localMockApi.getCurrentUser() : apiRequest<User>("/api/me");
}

export async function loginUser(username: string, password: string): Promise<User> {
  const response = await apiRequest<{ user: User }>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
  return response.user;
}

export async function logoutUser(): Promise<void> {
  await apiRequest<{ status: string }>("/api/auth/logout", { method: "POST" });
}

export async function listConversations(): Promise<ConversationSummary[]> {
  if (useLocalMocks) return localMockApi.listConversations();
  const response = await apiRequest<{ items: ConversationSummary[] }>("/api/conversations");
  return response.items;
}

export async function getConversation(id: string): Promise<Conversation> {
  return useLocalMocks ? localMockApi.getConversation(id) : apiRequest<Conversation>(`/api/conversations/${id}`);
}

export async function createConversation(title = "New chat"): Promise<ConversationSummary> {
  if (useLocalMocks) return localMockApi.createConversation(title);
  return apiRequest<ConversationSummary>("/api/conversations", { method: "POST", body: JSON.stringify({ title }) });
}

export async function sendMockChat(payload: { conversationId: string; message: string; departmentFilter: string; sourceFilter: string }): Promise<MockChatResponse> {
  if (useLocalMocks) return localMockApi.sendMockChat();
  return apiRequest<MockChatResponse>("/api/chat/mock", { method: "POST", body: JSON.stringify(payload) });
}

export async function streamRealChat(
  payload: { conversationId: string; message: string; departmentFilter: string; sourceFilter: string },
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError("The local backend is not reachable. Check that FastAPI is running.", "BACKEND_OFFLINE", 0);
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(error.error || "The chat request failed.", error.code || "CHAT_ERROR", response.status);
  }
  if (!response.body) throw new ApiError("The backend returned no response stream.", "EMPTY_STREAM", 502);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const processBlock = (block: string) => {
    const lines = block.split(/\r?\n/);
    const eventName = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
    const data = lines.filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n");
    if (!eventName || !data) return;
    const payloadData = JSON.parse(data);
    if (eventName === "error") {
      throw new ApiError(payloadData.error || "The RAG stream failed.", payloadData.code || "RAG_ERROR", 502);
    }
    onEvent({ type: eventName, ...payloadData } as ChatStreamEvent);
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    for (const block of blocks) processBlock(block);
    if (done) break;
  }
  if (buffer.trim()) processBlock(buffer);
}

export async function submitFeedback(messageId: string, rating: "up" | "down", auditId?: string) {
  if (useLocalMocks) return localMockApi.submitFeedback();
  return apiRequest<{ status: string; feedbackId: string }>("/api/feedback", { method: "POST", body: JSON.stringify({ messageId, rating, auditId }) });
}
