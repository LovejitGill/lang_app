"""Mechanical evidence checks; no model or LanguageTool server required."""

import pytest

from grammar_rule_detector import explain_proposal


def evidence(text, word, replacement, rule="MD_BASEFORM"):
    start = text.index(word)
    return {
        "matches": [
            {
                "offset": len(text[:start].encode("utf-16-le")) // 2,
                "length": len(word.encode("utf-16-le")) // 2,
                "rule": {"id": rule},
                "replacements": [{"value": replacement}],
            }
        ]
    }


def test_new_verb_needs_rule_evidence_not_word_whitelist():
    text = "We should investigates."
    result = explain_proposal(
        text, "We should investigate.", evidence(text, "investigates", "investigate")
    )
    assert result["state"] == "provisional"
    assert result["rule_id"] == "MD_BASEFORM"


def test_non_ascii_offsets():
    text = "🙂 We should investigates."
    result = explain_proposal(
        text, "🙂 We should investigate.", evidence(text, "investigates", "investigate")
    )
    assert result["edit"]["original"] == "investigates"


@pytest.mark.parametrize(
    "rule", ["UNKNOWN_RULE", "CAFE_DIACRITIC", "MORFOLOGIK_RULE_EN_US"]
)
def test_unmapped_rules_do_not_authorize_feedback(rule):
    text = "We should investigates."
    assert (
        explain_proposal(
            text,
            "We should investigate.",
            evidence(text, "investigates", "investigate", rule),
        )["state"]
        == "withheld"
    )


def test_exact_whole_sentence_required():
    text = "We should investigates today."
    assert (
        explain_proposal(
            text,
            "We should investigate tomorrow.",
            evidence(text, "investigates", "investigate"),
        )["state"]
        == "withheld"
    )


def test_conflicting_rule_evidence_is_withheld():
    text = "We should investigates."
    raw = evidence(text, "investigates", "investigate")
    raw["matches"] *= 2
    assert explain_proposal(text, "We should investigate.", raw)["state"] == "withheld"


def test_no_evidence_no_feedback():
    assert (
        explain_proposal(
            "We should investigates.", "We should investigate.", {"matches": []}
        )["state"]
        == "withheld"
    )


def test_unchanged_does_not_claim_correctness():
    assert (
        explain_proposal("She walk.", "She walk.", {"matches": []})["state"]
        == "no_proposal"
    )


def test_past_suggestion_does_not_get_present_explanation():
    text = "She bake bread."
    assert (
        explain_proposal(
            text, "She baked bread.", evidence(text, "bake", "baked", "HE_VERB_AGR")
        )["state"]
        == "withheld"
    )


def test_malformed_evidence_rejected():
    with pytest.raises(TypeError):
        explain_proposal("She walk.", "She walks.", {})


def test_suggestion_need_not_be_first():
    text = "She bake bread."
    raw = evidence(text, "bake", "baked", "HE_VERB_AGR")
    raw["matches"][0]["replacements"].append({"value": "bakes"})
    assert explain_proposal(text, "She bakes bread.", raw)["state"] == "provisional"
