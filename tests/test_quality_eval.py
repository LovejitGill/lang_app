"""Dataset separation, label isolation, and honest evaluation accounting."""

from unittest.mock import MagicMock

import pytest

import llm_client
from prompts import LEVELS, SCENARIOS, build_system_prompt
from quality_eval import evaluate_case, load_cases, summarize


def test_balanced_distinct_splits_cover_settings():
    development, _ = load_cases("development")
    heldout, _ = load_cases("heldout")
    regression, _ = load_cases("regression")
    all_text = [row["text"] for row in development + heldout + regression]
    assert len(all_text) == len(set(all_text))
    for cases in (development, heldout):
        assert len(cases) == 20
        assert sum(row["expected_error"] for row in cases) == 10
        assert {row["level"] for row in cases} == set(LEVELS)
        assert {row["scenario"] for row in cases} == set(SCENARIOS)


def test_labels_never_enter_model_messages(monkeypatch):
    case = load_cases("development")[0][1]
    case = {**case, "expected_issue": "PRIVATE_GRADING_LABEL"}
    chat = MagicMock(return_value='{"reply":"Tell me about it.","feedback":[]}')
    monkeypatch.setattr(llm_client, "_chat", chat)
    result = evaluate_case(case, "conservative")
    messages = chat.call_args.args[0]
    assert "PRIVATE_GRADING_LABEL" not in str(messages)
    assert messages[-1]["content"] == case["text"]
    assert len(messages) == 2
    assert result["review"] is None
    assert result["attempts"] == 1


def test_bad_json_retries_are_counted(monkeypatch):
    case = load_cases("development")[0][0]
    monkeypatch.setattr(
        llm_client,
        "_chat",
        MagicMock(side_effect=["bad", '{"reply":"Hi","feedback":[]}']),
    )
    assert evaluate_case(case, "baseline")["attempts"] == 2


def test_failures_and_abstentions_are_not_counted_as_corrected():
    rows = [
        {
            "variant": "baseline",
            "expected_error": True,
            "seconds": 1,
            "attempts": 1,
            "result": {"feedback": []},
        },
        {
            "variant": "baseline",
            "expected_error": False,
            "seconds": 2,
            "attempts": 1,
            "error": "offline",
        },
    ]
    result = summarize(rows)["baseline"]
    assert result["attempted"] == 2
    assert result["completed"] == 1
    assert result["correct_inputs_completed"] == 0
    assert result["incorrect_inputs_with_feedback"] == 0


def test_prompt_variants_are_explicit_and_baseline_stays_default():
    assert build_system_prompt("beginner", "introductions") == build_system_prompt(
        "beginner", "introductions", variant="baseline"
    )
    with pytest.raises(ValueError, match="variant"):
        build_system_prompt("beginner", "introductions", variant="unknown")
