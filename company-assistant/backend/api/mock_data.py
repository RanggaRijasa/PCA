"""In-memory data used only by the Phase 2 FastAPI stubs."""

from __future__ import annotations

from copy import deepcopy


CURRENT_USER = {
    "id": "user_004",
    "name": "Maya Putri",
    "email": "maya@company.local",
    "role": "admin",
    "department": "Operations",
    "status": "active",
}

REMOTE_WORK_SOURCES = [
    {
        "id": "src_001",
        "documentId": "doc_001",
        "chunkId": "chunk_001_03",
        "title": "Remote Work Policy v2.1.pdf",
        "fileName": "Remote Work Policy v2.1.pdf",
        "fileType": "pdf",
        "department": "HR",
        "accessLevel": "staff",
        "page": 3,
        "section": "Remote Work Eligibility",
        "snippet": "Employees may work remotely up to two days per week with manager approval and team coverage.",
        "relevanceScore": 0.95,
        "citationRank": 1,
    },
    {
        "id": "src_002",
        "documentId": "doc_002",
        "chunkId": "chunk_002_08",
        "title": "Employee Handbook 2024.pdf",
        "fileName": "Employee Handbook 2024.pdf",
        "fileType": "pdf",
        "department": "People Operations",
        "accessLevel": "public_internal",
        "page": 18,
        "section": "Flexible Working",
        "snippet": "Flexible arrangements require written agreement with the employee's direct manager.",
        "relevanceScore": 0.88,
        "citationRank": 2,
    },
    {
        "id": "src_003",
        "documentId": "doc_003",
        "chunkId": "chunk_003_02",
        "title": "Flexible Work Guidelines.docx",
        "fileName": "Flexible Work Guidelines.docx",
        "fileType": "docx",
        "department": "HR",
        "accessLevel": "staff",
        "section": "Team Coordination",
        "snippet": "Remote schedules should be recorded in the shared team calendar at least one week ahead.",
        "relevanceScore": 0.81,
        "citationRank": 3,
    },
]

ANSWER_TEXT = """Answer:
Employees are eligible to work remotely up to two days per week with manager approval. The schedule should maintain team coverage and be recorded in the shared calendar in advance.

Sources:
1. Remote Work Policy v2.1, Remote Work Policy v2.1.pdf, page 3, section Remote Work Eligibility, version v2.1
2. Employee Handbook 2024, Employee Handbook 2024.pdf, page 18, section Flexible Working, version 2024

Confidence:
High

Notes:
This is mock Phase 2 data for interface and API contract testing only."""

CONVERSATIONS = [
    {
        "id": "conv_001",
        "title": "Remote work policy",
        "createdAt": "2026-06-12T03:24:00Z",
        "updatedAt": "2026-06-12T03:26:00Z",
        "messages": [
            {
                "id": "msg_001",
                "role": "user",
                "content": "What is our policy on remote work?",
                "createdAt": "2026-06-12T03:24:00Z",
                "status": "complete",
            },
            {
                "id": "msg_002",
                "role": "assistant",
                "content": ANSWER_TEXT,
                "createdAt": "2026-06-12T03:24:01Z",
                "status": "complete",
                "sources": deepcopy(REMOTE_WORK_SOURCES),
                "metadata": {
                    "modelName": "mock-model",
                    "embeddingModel": "mock-embedding",
                    "retrievalTopK": 20,
                    "rerankTopN": 5,
                    "latencyMs": 420,
                    "auditId": "audit_mock_001",
                    "refused": False,
                },
            },
        ],
    },
    {
        "id": "conv_002",
        "title": "Overtime reimbursement",
        "createdAt": "2026-06-11T08:14:00Z",
        "updatedAt": "2026-06-11T08:17:00Z",
        "messages": [],
    },
    {
        "id": "conv_003",
        "title": "Sick leave entitlement",
        "createdAt": "2026-06-10T02:05:00Z",
        "updatedAt": "2026-06-10T02:10:00Z",
        "messages": [],
    },
    {
        "id": "conv_004",
        "title": "Laptop procurement process",
        "createdAt": "2026-06-09T06:45:00Z",
        "updatedAt": "2026-06-09T06:48:00Z",
        "messages": [],
    },
    {
        "id": "conv_005",
        "title": "Code of conduct questions",
        "createdAt": "2026-06-08T04:22:00Z",
        "updatedAt": "2026-06-08T04:26:00Z",
        "messages": [],
    },
    {
        "id": "conv_006",
        "title": "Benefits for new employees",
        "createdAt": "2026-06-07T09:12:00Z",
        "updatedAt": "2026-06-07T09:14:00Z",
        "messages": [],
    },
    {
        "id": "conv_007",
        "title": "Data retention policy",
        "createdAt": "2026-06-06T01:30:00Z",
        "updatedAt": "2026-06-06T01:34:00Z",
        "messages": [],
    },
]

DOCUMENTS = [
    {"id": "doc_001", "title": "Remote Work Policy v2.1.pdf", "fileName": "Remote Work Policy v2.1.pdf", "fileType": "pdf", "department": "HR", "accessLevel": "staff", "version": "v2.1", "owner": "People Operations", "status": "indexed", "lastIndexedAt": "2026-06-11T04:30:00Z", "chunkCount": 24},
    {"id": "doc_002", "title": "Employee Handbook 2024.pdf", "fileName": "Employee Handbook 2024.pdf", "fileType": "pdf", "department": "People Operations", "accessLevel": "public_internal", "version": "2024", "owner": "HR Director", "status": "indexed", "lastIndexedAt": "2026-06-10T03:10:00Z", "chunkCount": 86},
    {"id": "doc_003", "title": "Flexible Work Guidelines.docx", "fileName": "Flexible Work Guidelines.docx", "fileType": "docx", "department": "HR", "accessLevel": "staff", "version": "v1.4", "owner": "People Operations", "status": "approved", "lastIndexedAt": "2026-06-09T07:40:00Z", "chunkCount": 18},
    {"id": "doc_004", "title": "Internship Policy v1.0.pdf", "fileName": "Internship Policy v1.0.pdf", "fileType": "pdf", "department": "HR", "accessLevel": "manager", "version": "v1.0", "owner": "Talent Team", "status": "pending_ingestion", "chunkCount": 0},
    {"id": "doc_005", "title": "IT Security Policy v3.0.pdf", "fileName": "IT Security Policy v3.0.pdf", "fileType": "pdf", "department": "IT", "accessLevel": "staff", "version": "v3.0", "owner": "Security Team", "status": "failed", "lastIndexedAt": "2026-06-08T06:12:00Z", "chunkCount": 0},
]

AUDIT_LOGS = [
    {"id": "audit_001", "timestamp": "2026-06-12T03:24:01Z", "user": "Maya Putri", "role": "admin", "eventType": "mock_chat", "questionPreview": "What is our policy on remote work?", "sourcesCount": 3, "permissionFilter": "public_internal, staff, manager, admin", "latencyMs": 420, "status": "answered"},
    {"id": "audit_002", "timestamp": "2026-06-11T08:14:10Z", "user": "Andrew Davis", "role": "manager", "eventType": "mock_chat", "questionPreview": "Can I approve my own overtime?", "sourcesCount": 0, "permissionFilter": "public_internal, staff, manager", "latencyMs": 306, "status": "refused"},
]

EVALUATION_RUNS = [
    {"id": "eval_2026_06_11", "createdAt": "2026-06-11T10:00:00Z", "status": "mock_complete", "total": 50, "passed": 44, "failed": 6, "answerAccuracy": 0.86, "citationCorrectness": 0.9, "refusalCorrectness": 0.94, "permissionSafety": 1.0, "averageLatencyMs": 438},
]

FEEDBACK: list[dict[str, str | None]] = []
