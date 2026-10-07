"""Mechanical correction checks are intentionally separate from semantic grading."""

import json
from unittest.mock import MagicMock

import pytest
from ollama import ChatResponse

import grammar
import llm_client
from errors import LLMResponseError, TutorUnavailable
from grammar_eval import evaluate_grammar, summarize


def output(original="walk", replacement="walks", explanation="Use walks with she."):
    return json.dumps(
        {
            "corrections": [
                {
                    "original": original,
                    "replacement": replacement,
                    "explanation": explanation,
                }
            ]
        }
    )


def test_valid_correction_and_empty_response():
    assert (
        grammar.parse_corrections(output(), "She walk to work.")["corrections"][0][
            "replacement"
        ]
        == "walks"
    )
    assert grammar.parse_corrections('{"corrections":[]}', "She walks to work.") == {
        "corrections": []
    }


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        "null",
        "{}",
        '{"corrections":"none"}',
        '{"corrections":[],"score":100}',
        '{"corrections":[null]}',
        '{"corrections":[{"original":"walk","replacement":"walks"}]}',
        output(explanation=""),
        output(explanation="x" * 241),
        output(replacement=1),
        output(original="invented phrase"),
        output(replacement="walk"),
        output(replacement=" walk "),
    ],
)
def test_invalid_or_unsupported_corrections_rejected(raw):
    with pytest.raises(LLMResponseError):
        grammar.parse_corrections(raw, "She walk to work.")


def test_substring_inside_word_is_not_a_quoted_word():
    with pytest.raises(LLMResponseError, match="exact word"):
        grammar.parse_corrections(output("he", "they"), "The weather is fine.")


def test_case_corrections_allowed_but_unicode_equivalent_changes_rejected():
    assert grammar.parse_corrections(output("i", "I"), "i walk.")
    with pytest.raises(LLMResponseError, match="identical"):
        grammar.parse_corrections(output("café", "cafe\u0301"), "A café.")


def test_duplicates_and_too_many_corrections_rejected():
    correction = json.loads(output())["corrections"][0]
    for count in (2, 3):
        with pytest.raises(LLMResponseError):
            grammar.parse_corrections(
                json.dumps({"corrections": [correction] * count}), "She walk."
            )


def test_mechanically_valid_is_not_semantically_correct():
    # This bad grammar suggestion passes mechanical checks. Review remains necessary.
    result = grammar.parse_corrections(
        output("cycle", "cycles"), "My sister and I cycle to work."
    )
    assert result["corrections"]


@pytest.mark.parametrize("text", ["", "  ", None, 42, "x" * 1001])
def test_invalid_input_never_calls_model(monkeypatch, text):
    chat = MagicMock()
    monkeypatch.setattr(llm_client, "_chat", chat)
    with pytest.raises(ValueError):
        grammar.check_grammar(text)
    chat.assert_not_called()


def test_rejected_output_retains_raw_and_is_not_empty_success(monkeypatch):
    raw = output("walk", "walk")
    chat = MagicMock(return_value=raw)
    monkeypatch.setattr(llm_client, "_chat", chat)
    result = grammar.check_grammar("She walk.")
    assert result["status"] == "rejected"
    assert result["raw"] == raw
    assert result["result"] is None
    chat.assert_called_once()
    assert chat.call_args.kwargs["schema"] == grammar.GRAMMAR_SCHEMA


def test_service_error_propagates_without_retry(monkeypatch):
    chat = MagicMock(side_effect=TutorUnavailable("offline"))
    monkeypatch.setattr(llm_client, "_chat", chat)
    with pytest.raises(TutorUnavailable):
        grammar.check_grammar("She walk.")
    chat.assert_called_once()


def test_labels_and_conversation_context_not_sent(monkeypatch):
    case = {
        "id": "test",
        "text": "She walks.",
        "expected_error": False,
        "expected_issue": "SECRET_LABEL",
    }
    chat = MagicMock(return_value='{"corrections":[]}')
    monkeypatch.setattr(llm_client, "_chat", chat)
    row = evaluate_grammar(case)
    messages = chat.call_args.args[0]
    assert len(messages) == 2
    assert messages[-1] == {"role": "user", "content": "She walks."}
    assert "SECRET_LABEL" not in str(messages)
    assert row["review"] is None


def test_custom_schema_uses_same_transport_settings(monkeypatch):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.chat.return_value = ChatResponse(
        message={"role": "assistant", "content": '{"corrections":[]}'}
    )
    monkeypatch.setattr(llm_client, "Client", factory)
    llm_client._chat([{"role": "user", "content": "Hi"}], schema=grammar.GRAMMAR_SCHEMA)
    kwargs = factory.return_value.__enter__.return_value.chat.call_args.kwargs
    assert kwargs["format"] == grammar.GRAMMAR_SCHEMA
    assert kwargs["options"] == {
        "num_predict": 256,
        "num_ctx": 4096,
        "temperature": 0.2,
    }
    assert kwargs["think"] is False


def test_experimental_model_override_does_not_change_default(monkeypatch):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.chat.return_value = ChatResponse(
        message={"role": "assistant", "content": '{"corrections":[]}'}
    )
    monkeypatch.setattr(llm_client, "Client", factory)
    original = llm_client.MODEL
    grammar.check_grammar("Hello.", model="qwen3:4b")
    assert (
        factory.return_value.__enter__.return_value.chat.call_args.kwargs["model"]
        == "qwen3:4b"
    )
    assert llm_client.MODEL == original
    llm_client.ask_llm("Hello.")
    assert (
        factory.return_value.__enter__.return_value.chat.call_args.kwargs["model"]
        == original
    )


def test_rejections_and_errors_not_counted_as_valid_empty():
    rows = [
        {
            "variant": "grammar_only",
            "status": "rejected",
            "expected_error": False,
            "result": None,
            "seconds": 1,
        },
        {
            "variant": "grammar_only",
            "status": "error",
            "error": "offline",
            "expected_error": True,
            "result": None,
            "seconds": 2,
        },
    ]
    result = summarize(rows)["grammar_only"]
    assert result["attempted"] == 2
    assert result["valid"] == 0
    assert result["rejected"] == result["service_errors"] == 1
