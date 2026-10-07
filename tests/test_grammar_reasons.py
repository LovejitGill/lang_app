"""Check reasoning uses the actual text without altering frozen detections."""

import re

import pytest

from grammar_explanation_reasons import sentence_reason
from grammar_reason_eval import replay


def reason(text, old, new, rule):
    start = re.search(r"(?<!\w)" + re.escape(old) + r"(?!\w)", text).start()
    return sentence_reason(
        text,
        {
            "rule_id": rule,
            "edit": {
                "original": old,
                "replacement": new,
                "start": start,
                "end": start + len(old),
            },
        },
    )


@pytest.mark.parametrize(
    "text,old,new,rule,fragments",
    [
        (
            "He did not danced.",
            "danced",
            "dance",
            "DID_BASEFORM",
            ["already marks the past", "dance"],
        ),
        (
            "Does she cooks?",
            "cooks",
            "cook",
            "DOES_X_HAS",
            ["already matches the subject", "cook"],
        ),
        (
            "They must leaves.",
            "leaves",
            "leave",
            "MD_BASEFORM",
            ["must", "every subject", "leave"],
        ),
        (
            "I saw twelve duck.",
            "duck",
            "ducks",
            "CD_NN",
            ["‘Twelve’ is more than one", "ducks"],
        ),
        ("I saw a honest worker.", "a", "an", "EN_A_VS_AN", ["Honest", "vowel sound"]),
        ("He has an uniform.", "an", "a", "EN_A_VS_AN", ["Uniform", "consonant sound"]),
        (
            "The room is more brighter.",
            "more brighter",
            "brighter",
            "MOST_COMPARATIVE",
            ["already makes a comparison", "repeats"],
        ),
        (
            "I have waited since three days.",
            "since",
            "for",
            "SINCE_FOR",
            ["Three days", "length of time"],
        ),
        (
            "The birds needs water.",
            "needs",
            "need",
            "AGREEMENT_SENT_START",
            ["The birds", "more than one"],
        ),
        (
            "There are a cup on the desk.",
            "are",
            "is",
            "THERE_VBP_NN",
            ["A cup", "one thing"],
        ),
    ],
)
def test_reason_links_context_to_change(text, old, new, rule, fragments):
    result = reason(text, old, new, rule)
    assert all(fragment in result for fragment in fragments)


def test_no_unverified_sound_transcription():
    result = reason("He is an chef.", "an", "a", "EN_A_VS_AN")
    assert "consonant sound" in result
    assert "ch sound" not in result and "/tʃ/" not in result


def test_missing_context_does_not_invent_word():
    assert reason("a", "a", "an", "EN_A_VS_AN") is None


def test_all_saved_decisions_preserved():
    report = replay()
    assert report["summary"] == {
        "cases": 88,
        "detection_changes": 0,
        "offered_explanations": 33,
        "contextual_drafts": 33,
        "needs_context_review": 0,
        "model_calls": 0,
        "checker_calls": 0,
    }
    assert all(r["human_review"]["explains_why"] is None for r in report["rows"])
