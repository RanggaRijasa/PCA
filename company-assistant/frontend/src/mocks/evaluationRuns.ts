import type { EvaluationRun } from "../types";

export const mockEvaluationRuns: EvaluationRun[] = [
  { id: "eval_2026_06_11", createdAt: "2026-06-11T10:00:00Z", status: "mock_complete", total: 50, passed: 44, failed: 6, retrievalHitRate: 0.88, answerAccuracy: 0.86, citationCorrectness: 0.9, refusalCorrectness: 0.94, permissionSafety: 1, hallucinationRate: 0.04, averageLatencyMs: 438, p95LatencyMs: 910, criticalLeakage: false, categoryMetrics: {}, failedCases: [], reportFile: "mock-report.md" },
];
