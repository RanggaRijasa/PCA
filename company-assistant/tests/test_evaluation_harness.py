from pathlib import Path

import pytest

from eval.run_eval import CaseResult, build_summary, load_cases


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_dataset_is_a_valid_small_corpus_but_keeps_quality_gate() -> None:
    with pytest.raises(ValueError, match="at least 50"):
        load_cases(
            PROJECT_ROOT / "eval/test_questions.csv",
            PROJECT_ROOT / "eval/expected_answers.csv",
        )

    cases = load_cases(
        PROJECT_ROOT / "eval/test_questions.csv",
        PROJECT_ROOT / "eval/expected_answers.csv",
        minimum_questions=1,
    )
    categories = {case.category for case in cases}
    assert len(cases) == 15
    assert categories == {
        "direct",
        "outdated",
        "permission",
        "table",
        "indonesian",
        "prompt_injection",
        "no_answer",
        "mixed",
    }
    assert cases[0].expected_keywords == ("2 days", "manager approval", "3 months")
    assert cases[5].expected_keywords == ("idr 1,500,000",)


def test_summary_treats_permission_and_leakage_as_explicit_metrics() -> None:
    case = load_cases(
        PROJECT_ROOT / "eval/test_questions.csv",
        PROJECT_ROOT / "eval/expected_answers.csv",
        minimum_questions=1,
    )[0]
    result = CaseResult(
        case=case,
        passed=True,
        retrieval_hit=True,
        answer_correct=True,
        citation_correct=True,
        refusal_correct=True,
        permission_correct=True,
        hallucinated=False,
        critical_leakage=False,
        latency_ms=100,
        actual_behavior="answer",
        sources=(case.expected_source,),
        answer_preview="Expected",
        failures=(),
    )
    summary = build_summary([result], "report.md")
    assert summary["permissionSafety"] == 1.0
    assert summary["criticalLeakage"] is False
    assert summary["p95LatencyMs"] == 100
