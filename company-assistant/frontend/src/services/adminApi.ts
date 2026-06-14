import type { AdminDocumentUpload, AuditLog, EvaluationRun, IngestionJob } from "../types";
import { apiRequest, useLocalMocks } from "./apiClient";
import { localMockApi } from "./mockApi";

export async function listAuditLogs(): Promise<AuditLog[]> {
  if (useLocalMocks) return localMockApi.listAuditLogs();
  const response = await apiRequest<{ items: AuditLog[] }>("/api/audit-logs");
  return response.items;
}

export async function listEvaluationRuns(): Promise<EvaluationRun[]> {
  if (useLocalMocks) return localMockApi.listEvaluationRuns();
  const response = await apiRequest<{ items: EvaluationRun[] }>("/api/evaluation/runs");
  return response.items;
}

export async function listIngestionJobs(): Promise<IngestionJob[]> {
  const response = await apiRequest<{ items: IngestionJob[] }>("/api/admin/ingestion/jobs");
  return response.items;
}

export async function uploadAdminDocument(payload: AdminDocumentUpload): Promise<void> {
  const form = new FormData();
  form.set("file", payload.file);
  form.set("title", payload.title);
  form.set("department", payload.department);
  form.set("access_level", payload.accessLevel);
  form.set("owner", payload.owner);
  form.set("version", payload.version);
  form.set("effective_date", payload.effectiveDate);
  form.set("expiry_date", payload.expiryDate || "");
  form.set("document_type", payload.documentType);
  await apiRequest("/api/admin/documents/upload", { method: "POST", body: form });
}

export async function runAdminIngestion(payload: {
  jobId?: string;
  documentVersionId?: string;
  reindex?: boolean;
}): Promise<{ job: IngestionJob; searchable: boolean }> {
  return apiRequest("/api/admin/ingestion/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
