import json
from unittest.mock import Mock

import pytest

import llm_client
from benchmark import apply_edits
from errors import LLMResponseError
from sentence_grammar import check_sentence, derive_edits, parse_sentence


@pytest.mark.parametrize(
    "original,corrected",
    [
        ("I am engineer.", "I am an engineer."),
        ("This route is more shorter.", "This route is shorter."),
        ("I enjoy to swim.", "I enjoy swimming."),
        ("This is hers coat.", "This is her coat."),
        ("😀 She walk.", "😀 She walks."),
        ("She is is here.", "She is here."),
        ("Hello", "Hello!"),
        ("Hello!", "Hello"),
        ("I  live here.", "I live here."),
        ("Cafe", "Café"),
        ("It is fine.", "It is fine."),
    ],
)
def test_exact_offsets_reconstruct(original, corrected):
    edits = derive_edits(original, corrected)
    assert apply_edits(original, edits) == corrected
    for edit in edits:
        assert original[edit["start"] : edit["end"]] == edit["original"]


def test_article_is_insertion_not_guessed_replacement():
    edits = derive_edits("I am engineer.", "I am an engineer.")
    assert len(edits) == 1
    assert edits[0]["original"] == ""
    assert edits[0]["replacement"] == "an "
    assert edits[0]["start"] == edits[0]["end"] == 5


def test_word_boundary_does_not_replace_is_inside_this():
    edits = derive_edits("This is hers coat.", "This is her coat.")
    assert edits[0]["original"] == "hers"
    assert edits[0]["start"] == 8


@pytest.mark.parametrize(
    "data",
    [
        [],
        {"corrected_text": "Hi"},
        {"corrected_text": "Hi", "explanation": "", "extra": 1},
        {"corrected_text": None, "explanation": ""},
        {"corrected_text": "", "explanation": ""},
        {"corrected_text": "Hi", "explanation": []},
        {"corrected_text": "Hi", "explanation": "x" * 241},
        {"corrected_text": "Hi", "explanation": "No error"},
        {"corrected_text": "Hello", "explanation": ""},
    ],
)
def test_bad_contract_rejected(data):
    with pytest.raises(LLMResponseError):
        parse_sentence(json.dumps(data), "Hi")


def test_more_than_two_regions_rejected():
    with pytest.raises(LLMResponseError, match="two"):
        parse_sentence(
            json.dumps(
                {
                    "corrected_text": "We walk and they run but birds fly.",
                    "explanation": "Agreement.",
                }
            ),
            "We walks and they runs but birds flies.",
        )


def test_wrong_grammar_can_pass_mechanical_check():
    result = parse_sentence(
        json.dumps(
            {
                "corrected_text": "This route the more shorter.",
                "explanation": "Use the.",
            }
        ),
        "This route is more shorter.",
    )
    assert result["corrected_text"] == "This route the more shorter."


def test_raw_rejection_is_not_an_empty_success(monkeypatch):
    raw = '{"corrected_text":"She walk.","explanation":"No error."}'
    fake = Mock(return_value=raw)
    monkeypatch.setattr(llm_client, "_chat", fake)
    row = check_sentence("She walk.")
    assert row["status"] == "rejected" and row["raw"] == raw and row["result"] is None
    assert fake.call_count == 1


def test_input_and_model_are_passed_without_labels(monkeypatch):
    fake = Mock(
        return_value='{"corrected_text":"She walks.","explanation":"Use walks with she."}'
    )
    monkeypatch.setattr(llm_client, "_chat", fake)
    assert check_sentence("She walk.")["status"] == "valid"
    assert fake.call_args.args[0][-1] == {"role": "user", "content": "She walk."}
    assert fake.call_args.kwargs["model"] == "qwen3:4b"


@pytest.mark.parametrize("text", [None, "", "   ", "x" * 1001])
def test_invalid_input_never_calls_model(monkeypatch, text):
    fake = Mock()
    monkeypatch.setattr(llm_client, "_chat", fake)
    with pytest.raises(ValueError):
        check_sentence(text)
    fake.assert_not_called()
