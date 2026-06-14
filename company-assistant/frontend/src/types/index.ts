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

export type ConversationSummary = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
};

export type Conversation = ConversationSummary & {
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
  version?: string;
  effectiveDate?: string;
  snippet: string;
  relevanceScore?: number;
  citationRank: number;
};

export type AnswerMetadata = {
  modelName?: string;
  embeddingModel?: string;
  retrievalTopK?: number;
  rerankTopN?: number;
  maxContextChunks?: number;
  reranker?: string;
  latencyMs?: number;
  retrievalMs?: number;
  generationMs?: number;
  auditId?: string;
  refused?: boolean;
  refusalReason?: string;
  permissionFilter?: Record<string, unknown>;
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
  status: "approved" | "pending_ingestion" | "indexing" | "indexed" | "failed" | "archived";
  lastIndexedAt?: string;
  chunkCount?: number;
};

export type AuditLog = {
  id: string;
  timestamp: string;
  user: string;
  role: UserRole;
  eventType: string;
  questionPreview: string;
  question: string;
  sourcesCount: number;
  documentIds: string[];
  chunkIds: string[];
  citations: SourceCitation[];
  permissionFilter: string;
  permissionFilterData: Record<string, unknown>;
  latencyMs: number;
  modelName: string;
  answerHash: string;
  answerText?: string | null;
  feedbackRating?: "up" | "down" | null;
  refused: boolean;
  status: "answered" | "refused" | "error";
};

export type EvaluationFailedCase = {
  id: string;
  category: string;
  role: UserRole;
  question: string;
  expectedBehavior: string;
  actualBehavior: string;
  expectedSource: string;
  sources: string[];
  failures: string[];
  answerPreview: string;
};

export type EvaluationRun = {
  id: string;
  createdAt: string;
  status: string;
  total: number;
  passed: number;
  failed: number;
  retrievalHitRate: number;
  answerAccuracy: number;
  citationCorrectness: number;
  refusalCorrectness: number;
  permissionSafety: number;
  hallucinationRate: number;
  averageLatencyMs: number;
  p95LatencyMs: number;
  criticalLeakage: boolean;
  categoryMetrics: Record<string, { total: number; passed: number; passRate: number }>;
  failedCases: EvaluationFailedCase[];
  reportFile: string;
};

export type IngestionJobStatus =
  | "queued"
  | "validating"
  | "extracting"
  | "chunking"
  | "embedding"
  | "indexing"
  | "completed"
  | "failed"
  | "archived";

export type IngestionJob = {
  id: string;
  documentId: string | null;
  documentVersionId: string | null;
  sourceFile: string;
  title: string;
  department: string;
  accessLevel: AccessLevel;
  owner: string;
  documentType: string;
  version: string;
  effectiveDate?: string | null;
  expiryDate?: string | null;
  fileSizeBytes: number;
  status: IngestionJobStatus;
  documentStatus?: string | null;
  currentStep: string;
  errorMessage?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt: string;
  isCurrentVersion: boolean;
};

export type AdminDocumentUpload = {
  file: File;
  title: string;
  department: string;
  accessLevel: AccessLevel;
  owner: string;
  version: string;
  effectiveDate: string;
  expiryDate?: string;
  documentType: string;
};

export type MockChatResponse = {
  messageId: string;
  answer: string;
  sources: SourceCitation[];
  metadata: AnswerMetadata;
};

export type ChatStreamEvent =
  | { type: "start"; messageId: string; conversationId: string }
  | { type: "status"; stage: string }
  | { type: "token"; content: string }
  | {
      type: "final";
      messageId: string;
      answer: string;
      sources: SourceCitation[];
      metadata: AnswerMetadata;
      status: "complete" | "refused";
    };
