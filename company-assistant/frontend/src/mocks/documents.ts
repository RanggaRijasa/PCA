import type { DocumentSource } from "../types";

export const mockDocuments: DocumentSource[] = [
  { id: "doc_001", title: "Remote Work Policy v2.1.pdf", fileName: "Remote Work Policy v2.1.pdf", fileType: "pdf", department: "HR", accessLevel: "staff", version: "v2.1", owner: "People Operations", status: "indexed", lastIndexedAt: "2026-06-11T04:30:00Z", chunkCount: 24 },
  { id: "doc_002", title: "Employee Handbook 2024.pdf", fileName: "Employee Handbook 2024.pdf", fileType: "pdf", department: "People Operations", accessLevel: "public_internal", version: "2024", owner: "HR Director", status: "indexed", lastIndexedAt: "2026-06-10T03:10:00Z", chunkCount: 86 },
  { id: "doc_003", title: "Flexible Work Guidelines.docx", fileName: "Flexible Work Guidelines.docx", fileType: "docx", department: "HR", accessLevel: "staff", version: "v1.4", owner: "People Operations", status: "approved", lastIndexedAt: "2026-06-09T07:40:00Z", chunkCount: 18 },
  { id: "doc_004", title: "Internship Policy v1.0.pdf", fileName: "Internship Policy v1.0.pdf", fileType: "pdf", department: "HR", accessLevel: "manager", version: "v1.0", owner: "Talent Team", status: "pending_ingestion", chunkCount: 0 },
  { id: "doc_005", title: "IT Security Policy v3.0.pdf", fileName: "IT Security Policy v3.0.pdf", fileType: "pdf", department: "IT", accessLevel: "staff", version: "v3.0", owner: "Security Team", status: "failed", lastIndexedAt: "2026-06-08T06:12:00Z", chunkCount: 0 },
];

