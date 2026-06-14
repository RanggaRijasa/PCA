import type { SourceCitation } from "../types";

export const mockSources: SourceCitation[] = [
  { id: "src_001", documentId: "doc_001", chunkId: "chunk_001_03", title: "Remote Work Policy v2.1.pdf", fileName: "Remote Work Policy v2.1.pdf", fileType: "pdf", department: "HR", accessLevel: "staff", page: 3, section: "Remote Work Eligibility", snippet: "Employees may work remotely up to two days per week with manager approval and team coverage.", relevanceScore: 0.95, citationRank: 1 },
  { id: "src_002", documentId: "doc_002", chunkId: "chunk_002_08", title: "Employee Handbook 2024.pdf", fileName: "Employee Handbook 2024.pdf", fileType: "pdf", department: "People Operations", accessLevel: "public_internal", page: 18, section: "Flexible Working", snippet: "Flexible arrangements require written agreement with the employee's direct manager.", relevanceScore: 0.88, citationRank: 2 },
  { id: "src_003", documentId: "doc_003", chunkId: "chunk_003_02", title: "Flexible Work Guidelines.docx", fileName: "Flexible Work Guidelines.docx", fileType: "docx", department: "HR", accessLevel: "staff", section: "Team Coordination", snippet: "Remote schedules should be recorded in the shared team calendar at least one week ahead.", relevanceScore: 0.81, citationRank: 3 },
];

