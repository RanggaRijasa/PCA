import type { DocumentSource } from "../types";
import { apiRequest, useLocalMocks } from "./apiClient";
import { localMockApi } from "./mockApi";

export async function listDocuments(): Promise<DocumentSource[]> {
  if (useLocalMocks) return localMockApi.listDocuments();
  const response = await apiRequest<{ items: DocumentSource[] }>("/api/documents");
  return response.items;
}

