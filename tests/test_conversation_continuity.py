"""Check the actual answer changes the next question without borrowing facts."""

import pytest

from conversation_continuity import plan_continuation
from conversation_reference import answer
from dialogue_planner import prepare


def row(text, reply="Tell me more."):
    return {"learner_text": text, "tutor_reply": reply}


@pytest.mark.parametrize("topic", ["painting", "gardening", "chess"])
def test_reason_is_not_part_of_topic_or_asked_again(topic):
    result = plan_continuation(f"I enjoy {topic} because it helps me relax.")
    questions = " ".join(q["question"] for q in result["choices"])
    assert result["known_information"]["interest"] == topic
    assert "because" not in questions and "Why" not in questions


def test_duration_uses_learner_commute_and_avoids_already_asked_activity():
    plan = prepare(
        "The journey takes ten minutes.",
        history=[
            row(
                "I take the tram to school because it costs less.",
                "What do you usually do during your tram journey?",
            )
        ],
    )
    assert plan["known_information"]["duration"] == "ten minutes"
    assert plan["options"] == ["What do you like about travelling by tram?"]


def test_tutor_cannot_supply_a_commute_or_planned_meal():
    history = [row("Hello.", "You will cook noodles tomorrow. You take the bus.")]
    assert plan_continuation("The journey takes ten minutes.", history) is None
    assert plan_continuation("I haven't cooked them yet.", history) is None


def test_future_meal_reason_and_not_yet_preserve_time():
    history = [row("I will bake bread tonight.")]
    statement = "I chose bread because it is easy to share."
    reason = plan_continuation(statement, history)
    assert reason["known_information"]["completed"] is False
    assert all("Why" not in c["question"] for c in reason["choices"])
    current = plan_continuation("I have not made it yet.", history + [row(statement)])
    assert "haven't cooked the bread yet" in current["prefix"]
    assert "taste" not in str(current["choices"])


def test_topic_change_breaks_pronoun_meal_reference():
    history = [row("I will cook beans tomorrow."), row("I bought two books.")]
    assert plan_continuation("I have not made them yet.", history) is None


def test_second_relative_prevents_ambiguous_study_assignment():
    history = [
        row("My niece has an interview at a university tomorrow."),
        row("My brother called me."),
    ]
    assert plan_continuation("She wants to study physics.", history) is None


def test_cancellation_invalidates_old_future_interview_context():
    history = [
        row("My son has an interview at a college tomorrow."),
        row("The interview was cancelled."),
    ]
    assert plan_continuation("He wants to study music.", history) is None
    assert plan_continuation("The interview was cancelled.")["known_information"][
        "interview_cancelled"
    ]


@pytest.mark.parametrize(
    "text",
    [
        "If I enjoy painting because it is quiet, what then?",
        "My sister enjoys chess because it is fun.",
        "Did I take the bus because it costs less?",
        'She said "The interview was cancelled."',
    ],
)
def test_questions_other_people_and_quotes_are_not_first_person_facts(text):
    assert plan_continuation(text) is None


@pytest.mark.parametrize(
    "question, expected",
    [
        ("What made you choose rice?", "Why did you choose rice?"),
        (
            "What would your sister like to have with soup?",
            "What else would your sister like to eat with soup?",
        ),
        (
            "What do you usually do during your train journey?",
            "What do you do while you are on the train?",
        ),
        (
            "What do you like about travelling by bus?",
            "What makes travelling by bus good for you?",
        ),
    ],
)
def test_clarification_simplifies_actual_question_and_respects_no_followup(
    question, expected
):
    history = [row("I travel.", question)]
    assert answer("What do you mean?", history)["reply"] == expected
    assert "?" not in answer("What do you mean? No follow-up.", history)["reply"]


def test_stop_and_no_question_controls_precede_continuity():
    assert prepare("Thanks, that's enough practice for today.")["options"] == []
    assert (
        prepare("I enjoy painting because it is quiet. No follow-up.")["options"] == []
    )


def test_mismatched_pronoun_is_not_assigned_to_relative():
    history = [row("My son has an interview at a college tomorrow.")]
    assert plan_continuation("She wants to study music.", history) is None
    plan = plan_continuation("My son is happy because she caught her bus.", history)
    assert plan["prefix"] == "Your son feels happy."
    assert "son caught" not in plan["prefix"]
