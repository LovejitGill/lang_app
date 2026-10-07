import copy
import json
from unittest.mock import Mock

import pytest

import llm_client
from errors import LLMResponseError
from explanation_eval import evaluate_pair, summary
from explanation_review import parse_review, review_change


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"decision": "yes", "explanation": "Rule"},
        {"decision": "supported", "explanation": ""},
        {"decision": "unsupported", "explanation": " "},
        {"decision": "supported", "explanation": False},
        {"decision": "supported", "explanation": "x" * 241},
        {"decision": "supported", "explanation": "Rule", "corrected_text": "Hi"},
    ],
)
def test_invalid_contract(data):
    with pytest.raises(LLMResponseError):
        parse_review(json.dumps(data))


def test_non_json():
    with pytest.raises(LLMResponseError):
        parse_review("not json")


@pytest.mark.parametrize("decision", ["supported", "unsupported"])
def test_valid_decisions(decision):
    assert (
        parse_review(json.dumps({"decision": decision, "explanation": "A reason."}))[
            "decision"
        ]
        == decision
    )


def test_unchanged_skips_without_certifying_grammar(monkeypatch):
    chat = Mock()
    monkeypatch.setattr(llm_client, "_chat", chat)
    result = review_change("I am engineer.", "I am engineer.")
    assert result["status"] == "skipped" and result["result"] is None
    chat.assert_not_called()


def test_only_text_and_derived_edits_enter_prompt(monkeypatch):
    chat = Mock(
        return_value='{"decision":"supported","explanation":"Use an before a vowel sound."}'
    )
    monkeypatch.setattr(llm_client, "_chat", chat)
    review_change("I am engineer.", "I am an engineer.")
    messages = chat.call_args.args[0]
    payload = json.loads(messages[-1]["content"])
    assert set(payload) == {"original_text", "proposed_text", "edits"}
    assert payload["edits"][0]["original"] == ""
    assert chat.call_args.kwargs["model"] == "qwen3:4b"
    assert chat.call_count == 1


def source():
    return {
        "case_id": "one",
        "status": "valid",
        "seconds": 3.0,
        "result": {
            "corrected_text": "She walks.",
            "explanation": "OLD_REASON",
            "corrections": [],
        },
    }


def test_supported_uses_new_explanation_preserves_source(monkeypatch):
    chat = Mock(
        return_value='{"decision":"supported","explanation":"Use walks with she."}'
    )
    monkeypatch.setattr(llm_client, "_chat", chat)
    before = source()
    snapshot = copy.deepcopy(before)
    row = evaluate_pair("She walk.", before, model="qwen3:4b")
    assert before == snapshot
    assert row["would_offer_correction"] and row["effective_text"] == "She walks."
    assert row["effective_explanation"] == "Use walks with she."
    assert "OLD_REASON" not in str(chat.call_args.args)


def test_unsupported_keeps_miss_visible(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "_chat",
        Mock(return_value='{"decision":"unsupported","explanation":"Cannot justify."}'),
    )
    row = evaluate_pair("She walk.", source(), model="qwen3:4b")
    assert row["feedback_state"] == "withheld"
    assert row["effective_text"] == "She walk."
    assert row["source_result"]["corrected_text"] == "She walks."
    report = {
        "dataset": {
            "cases": [
                {"id": "one", "expected_error": True, "references": ["She walks."]}
            ]
        },
        "rows": [row],
    }
    counts = summary(report)
    assert counts["erroneous_inputs_with_matching_offered_correction"] == 0
    assert counts["withheld_proposals"] == 1


def test_invalid_review_is_unavailable_not_no_error(monkeypatch):
    monkeypatch.setattr(llm_client, "_chat", Mock(return_value="bad JSON"))
    row = evaluate_pair("She walk.", source(), model="qwen3:4b")
    assert row["status"] == "rejected" and row["raw"] == "bad JSON"
    assert row["feedback_state"] == "unavailable"


def test_service_failure_not_supported(monkeypatch):
    monkeypatch.setattr(
        llm_client, "_chat", Mock(side_effect=llm_client.LLMError("Unavailable"))
    )
    row = evaluate_pair("She walk.", source(), model="qwen3:4b")
    assert row["status"] == "error" and not row["would_offer_correction"]


def test_upstream_failure_does_not_call_model(monkeypatch):
    chat = Mock()
    monkeypatch.setattr(llm_client, "_chat", chat)
    row = evaluate_pair(
        "She walk.",
        {"case_id": "one", "status": "rejected", "result": None, "seconds": 3},
        model="qwen3:4b",
    )
    assert row["feedback_state"] == "unavailable"
    chat.assert_not_called()


def test_mechanical_support_is_not_semantic_proof(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "_chat",
        Mock(return_value='{"decision":"supported","explanation":"Invented rule."}'),
    )
    assert (
        review_change("This is fine.", "This are fine.")["result"]["decision"]
        == "supported"
    )


@pytest.mark.parametrize(
    "original,proposed",
    [
        ("", "Hi"),
        ("Hi", ""),
        (None, "Hi"),
        ("Hi", None),
        ("x" * 1001, "Hi"),
        ("Hi", "x" * 1201),
    ],
)
def test_invalid_input_no_call(monkeypatch, original, proposed):
    chat = Mock()
    monkeypatch.setattr(llm_client, "_chat", chat)
    with pytest.raises(ValueError):
        review_change(original, proposed)
    chat.assert_not_called()
