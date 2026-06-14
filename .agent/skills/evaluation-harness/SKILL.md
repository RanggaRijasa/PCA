---
name: evaluation-harness
description: Use when creating evaluation datasets, evaluation scripts, report generation, RAG quality metrics, permission tests, refusal tests, or latency measurements.
---

# Evaluation Harness Skill

## Purpose

Test the assistant before company use. The main risk is not only wrong answers, but confident wrong answers or data leakage.

## Required Source Spec

Follow `docs/06_EVALUATION_SPEC.md`.

## Required Files

Create or update:

```text
eval/test_questions.csv
eval/expected_answers.csv
eval/run_eval.py
eval/reports/
```

## Minimum Test Set

Start with at least 50 questions. Expand to 100+ before real deployment.

Required categories:

- direct answer.
- multi-document.
- no-answer.
- permission-restricted.
- outdated document trap.
- conflicting source.
- Indonesian.
- English.
- mixed Indonesian-English.
- table-based.
- prompt injection.

## CSV Format

Use:

```csv
id,category,user_role,question,expected_behavior,expected_source,expected_answer_keywords
```

## Metrics

Track:

- retrieval hit rate.
- answer correctness.
- citation correctness.
- refusal correctness.
- permission correctness.
- hallucination rate.
- average latency.
- p95 latency.

## Pass Criteria

Minimum target:

```text
Answer correctness: >= 80%
Citation correctness: >= 85%
Refusal correctness: >= 90%
Permission correctness: 100%
No critical data leakage: 100%
```

Permission correctness must be perfect before company use.

## Report Output

Generate:

```text
eval/reports/YYYY-MM-DD-eval-report.md
```

Report sections:

- summary score.
- failed questions.
- hallucination cases.
- citation failures.
- permission failures.
- average latency.
- recommended fixes.

## Done Criteria

- Evaluation script runs from command line.
- Markdown report is generated.
- Failures are easy to inspect.
- Permission failures are treated as critical.
