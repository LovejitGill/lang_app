"""Exercise new sentences, extra edits and abstention, not only benchmark cases."""

import pytest

from rule_explanation_eval import replay
from rule_explanations import explain_change


@pytest.mark.parametrize(
    "original,proposed,rule",
    [
        ("We should eats lunch.", "We should eat lunch.", "modal_base"),
        ("Did they played outside?", "Did they play outside?", "do_base"),
        ("She did not played today.", "She did not play today.", "do_base"),
        ("I bought two book.", "I bought two books.", "number_plural"),
        (
            "We have waited since three days.",
            "We have waited for three days.",
            "duration_for",
        ),
        ("The tower is more taller.", "The tower is taller.", "single_comparative"),
    ],
)
def test_supported_families(original, proposed, rule):
    result = explain_change(original, proposed)
    assert result["state"] == "provisional"
    assert result["rule"] == rule
    assert result["explanation"]


@pytest.mark.parametrize(
    "original,proposed",
    [
        ("I am engineer.", "I am an engineer."),  # Not a supported family.
        ("Please give the key to me.", "Please give me the key."),  # Style.
        ("Please give the key to I.", "Please give me the key to I."),  # Still wrong.
        ("The can takes space.", "The can take space."),  # Can is a noun.
        ("I have waited since Monday.", "I have waited for Monday."),
        ("She is more clever.", "She is clever."),  # Meaning change.
        ("He should eats lunch.", "He should eat dinner."),  # Extra edit.
        ("I bought two sheep.", "I bought two sheeps."),  # Unknown morphology.
        ("He could sings.", "He could sing."),  # Explicit vocabulary limit.
    ],
)
def test_withholds_unknown_or_extra_changes(original, proposed):
    assert explain_change(original, proposed)["state"] == "withheld"


def test_unchanged_is_not_a_claim_of_correctness():
    assert explain_change("I am engineer.", "I am engineer.")["state"] == "no_proposal"


@pytest.mark.parametrize(
    "a,b", [(None, "ok"), ("", "ok"), ("ok", " "), ("x" * 1201, "x")]
)
def test_invalid_input(a, b):
    with pytest.raises(ValueError):
        explain_change(a, b)


def test_replay_preserves_full_denominator_and_pending_review():
    report = replay()
    assert report["summary"]["cases"] == 60
    assert report["summary"]["error_denominator"] == 30
    assert report["summary"]["human_useful_feedback"] is None
    assert all(r["human_review"]["useful_feedback"] is None for r in report["rows"])


def test_noun_modifier_is_not_pluralized():
    result = explain_change("We bought three box sets.", "We bought three boxes sets.")
    assert result["state"] == "withheld"


@pytest.mark.parametrize(
    "original,proposed,rule",
    [
        ("He work nearby.", "He works nearby.", "singular_agreement"),
        ("My brother need books.", "My brother needs books.", "singular_agreement"),
        ("The teacher like music.", "The teacher likes music.", "singular_agreement"),
        ("The drivers eats lunch.", "The drivers eat lunch.", "plural_agreement"),
        ("We plays outside.", "We play outside.", "plural_agreement"),
        (
            "There are a chair near the door.",
            "There is a chair near the door.",
            "there_singular",
        ),
    ],
)
def test_new_agreement_examples(original, proposed, rule):
    result = explain_change(original, proposed)
    assert result["state"] == "provisional"
    assert result["rule"] == rule


@pytest.mark.parametrize(
    "original,proposed",
    [
        ("He works nearby.", "He work nearby."),
        ("My aunt and uncle drive a bus.", "My aunt and uncle drives a bus."),
        (
            "The students who work nearby need time.",
            "The students who work nearby needs time.",
        ),
        ("I insist that she work nearby.", "I insist that she works nearby."),
        ('The sign says "She walk".', 'The sign says "She walks".'),
        ("They read yesterday.", "They reads yesterday."),
        ("She walk yesterday.", "She walks yesterday."),
        ("She read books last week.", "She reads books last week."),
        ("He can work nearby.", "He can works nearby."),
        ("She walk to work.", "She walks to school."),
        ("There are a bowl and a cup.", "There is a bowl and a cup."),
        ("There are two bowls.", "There is two bowls."),
        ("The news needs attention.", "The news need attention."),
        ("She swim daily.", "She swims daily."),
    ],
)
def test_agreement_abstains_on_ambiguous_or_unsupported_context(original, proposed):
    assert explain_change(original, proposed)["state"] == "withheld"


def test_read_can_already_be_past_tense():
    assert explain_change("She read books.", "She reads books.")["state"] == "withheld"


def test_fixed_context_challenges():
    from rule_challenge_eval import evaluate

    report = evaluate()
    assert report["summary"]["failed"] == 0, [
        row["id"] for row in report["rows"] if not row["passed"]
    ]
