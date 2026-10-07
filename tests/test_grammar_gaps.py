"""Gap mapping, evidence provenance and a small real local-rule integration check."""

import copy

import pytest

from grammar_gap_detector import (
    CLI,
    COUNT_RULE,
    JAVA,
    collect_count_evidence,
    explain_with_gaps,
    split_count_matches,
)


def match(text, word, replacement, rule):
    start = text.index(word)
    return {
        "offset": len(text[:start].encode("utf-16-le")) // 2,
        "length": len(word.encode("utf-16-le")) // 2,
        "rule": {"id": rule},
        "replacements": [{"value": replacement}],
    }


def test_did_past_keeps_rule_identity_and_reason():
    text = "Did you visited the castle?"
    raw = {"matches": [match(text, "visited", "visit", "DID_PAST")]}
    before = copy.deepcopy(raw)
    result = explain_with_gaps(text, "Did you visit the castle?", raw, {"matches": []})
    assert result["state"] == "provisional"
    assert result["rule_id"] == "DID_PAST"
    assert result["canonical_rule_id"] == "DID_BASEFORM"
    assert "already marks the past" in result["explanation"]
    assert raw == before


def test_custom_evidence_stays_distinguishable():
    text = "I packed seven bottle."
    result = explain_with_gaps(
        text,
        "I packed seven bottles.",
        {"matches": []},
        {"matches": [match(text, "bottle", "bottles", COUNT_RULE)]},
    )
    assert result["state"] == "provisional"
    assert result["rule_id"] == COUNT_RULE
    assert result["evidence_source"] == "supplemental"
    assert "Seven" in result["explanation"]


def test_builtin_support_is_not_duplicated():
    text = "I packed seven bottle."
    base = {"matches": [match(text, "bottle", "bottles", "CD_NN")]}
    custom = {"matches": [match(text, "bottle", "bottles", COUNT_RULE)]}
    assert (
        explain_with_gaps(text, "I packed seven bottles.", base, custom)[
            "evidence_source"
        ]
        == "builtin"
    )


def test_extra_change_still_withheld():
    text = "I packed seven bottle."
    custom = {"matches": [match(text, "bottle", "bottles", COUNT_RULE)]}
    assert (
        explain_with_gaps(text, "I packed eight bottles.", {"matches": []}, custom)[
            "state"
        ]
        == "withheld"
    )


def test_quoted_text_still_withheld():
    text = '"I packed seven bottle."'
    custom = {"matches": [match(text, "bottle", "bottles", COUNT_RULE)]}
    assert (
        explain_with_gaps(text, '"I packed seven bottles."', {"matches": []}, custom)[
            "state"
        ]
        == "withheld"
    )


def test_noncustom_supplement_is_rejected():
    text = "Did you visited?"
    raw = {"matches": [match(text, "visited", "visit", "DID_PAST")]}
    with pytest.raises(ValueError, match="Unexpected supplemental"):
        explain_with_gaps(text, "Did you visit?", {"matches": []}, raw)


def test_unicode_batch_offsets():
    texts = ["🙂 Hi.", "We found eight coin."]
    raw = {"matches": [match("\n".join(texts), "coin", "coins", COUNT_RULE)]}
    separated = split_count_matches(texts, raw)
    assert separated[0]["matches"] == []
    assert separated[1]["matches"][0]["offset"] == texts[1].index("coin")


def test_crossing_match_rejected():
    with pytest.raises(ValueError, match="boundary"):
        split_count_matches(
            ["One.", "Two."],
            {"matches": [match("One.\nTwo.", ".\nT", "x", COUNT_RULE)]},
        )


@pytest.mark.parametrize("texts", [[], [""], ["two\nlines"], ["x" * 1201]])
def test_invalid_batch(texts):
    with pytest.raises(ValueError):
        collect_count_evidence(texts)


@pytest.mark.skipif(
    not JAVA.exists() or not CLI.exists(),
    reason="Optional local LanguageTool installation unavailable",
)
def test_real_count_rule_positive_and_negative_controls():
    texts = [
        "I packed seven bottle.",
        "We found eight coin.",
        "I packed seven bottles.",
        "We found eight coins.",
        "I drank two water.",
        "We saw two deer.",
        "I caught three fish.",
        "We ordered three box sets.",
    ]
    result = collect_count_evidence(texts)
    assert [len(r["matches"]) for r in result["per_input"]] == [1, 1, 0, 0, 0, 0, 0, 0]
    assert result["per_input"][0]["matches"][0]["replacements"][0]["value"] == "bottles"
    assert result["per_input"][1]["matches"][0]["replacements"][0]["value"] == "coins"
