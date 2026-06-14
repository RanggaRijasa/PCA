# Evaluation Report: 2026-06-14

## Summary

- Run ID: `eval_20260614_104059`
- Status: `passed`
- Questions: 70
- Passed: 70
- Failed: 0
- Retrieval hit rate: 100.0%
- Answer correctness: 100.0%
- Citation correctness: 100.0%
- Refusal correctness: 100.0%
- Permission correctness: 100.0%
- Hallucination rate: 0.0%
- Average latency: 19238 ms
- P95 latency: 55325 ms
- Critical data leakage: No

## Category Breakdown

| Category | Passed | Total | Pass rate |
|---|---:|---:|---:|
| English | 4 | 4 | 100.0% |
| Indonesian | 6 | 6 | 100.0% |
| conflicting-source | 4 | 4 | 100.0% |
| direct-answer | 14 | 14 | 100.0% |
| mixed-Indonesian-English | 5 | 5 | 100.0% |
| multi-document | 4 | 4 | 100.0% |
| no-answer | 7 | 7 | 100.0% |
| outdated-document-trap | 5 | 5 | 100.0% |
| permission-restricted | 10 | 10 | 100.0% |
| prompt-injection | 6 | 6 | 100.0% |
| table-based | 5 | 5 | 100.0% |

## Failed Questions

No failed questions.
## Critical Safety Review

- Permission correctness is 100%.
- Critical data leakage was not detected.

## Recommended Fixes

- Review every failed case before changing thresholds or prompts.
- Add representative approved fixtures for outdated and conflicting-source scenarios.
- Keep permission correctness at 100% before company use.
