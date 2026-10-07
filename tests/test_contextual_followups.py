"""A stated reason/feeling is not a fact the tutor needs to ask again."""

import pytest

from contextual_followups import plan_context


def questions(plan):
    return [c["question"] for c in plan["choices"]]


@pytest.mark.parametrize("mode", ["bus", "train", "tram"])
def test_transport_reason_is_not_reasked(mode):
    plan = plan_context(f"I take the {mode} because it is cheaper than driving.")
    assert plan["known_information"]["reason"] == "cheaper"
    assert all(mode in q for q in questions(plan))
    assert all("cheaper" not in q and not q.startswith("Why") for q in questions(plan))


def test_future_trip_is_not_described_as_completed():
    plan = plan_context("I'll take the bus tomorrow because it's cheaper than driving.")
    assert plan["known_information"]["time"] == "future"
    assert all("will" in q for q in questions(plan))


def test_completed_trip_does_not_reask_duration():
    plan = plan_context(
        "I took the bus because it was cheaper than driving. The ride took twenty minutes."
    )
    assert plan["known_information"]["time"] == "past"
    assert all("How long" not in q and "will" not in q for q in questions(plan))


@pytest.mark.parametrize(
    "text",
    [
        "I don't take the bus because it is cheaper than driving.",
        "I might take the bus because it is cheaper than driving.",
        "My brother takes the bus because it is cheaper than driving.",
    ],
)
def test_transport_negation_uncertainty_or_other_person_is_not_rewritten(text):
    assert plan_context(text) is None


def test_expected_result_keeps_negated_emotion():
    plan = plan_context("I am not disappointed. I expected this result.")
    assert plan["known_information"]["negated_feeling"] == "disappointed"
    assert "sorry" not in plan["prefix"]
    assert any(c["intent"] == "expectation_reason" for c in plan["choices"])


def test_expected_result_does_not_reask_stated_reason():
    plan = plan_context(
        "I'm not disappointed. I expected this result because I didn't finish the last question."
    )
    assert all(c["intent"] != "expectation_reason" for c in plan["choices"])
    assert any("last question" in q for q in questions(plan))


def test_different_people_keep_different_emotions():
    plan = plan_context(
        "I'm disappointed, but my sister isn't. She expected this result."
    )
    assert plan["known_information"]["learner_feeling"] == "disappointed"
    assert plan["known_information"]["other_disappointed"] is False
    assert all("expect" not in q for q in questions(plan))


def test_interview_completed_is_not_admission_success():
    plan = plan_context(
        "The interview is over now. He feels pleased because he answered every question."
    )
    assert plan["known_information"]["interview_completed"] is True
    assert all("accepted" not in q and "prepare" not in q for q in questions(plan))
    assert "correct" not in str(plan)


def test_upcoming_interview_retains_real_relative_and_purpose():
    history = [
        {
            "learner_text": "My daughter needs the train to reach her college interview this afternoon.",
            "tutor_reply": "Did she catch the train?",
        }
    ]
    plan = plan_context("My daughter caught the train and is relieved.", history)
    assert plan["frame"] == "upcoming_interview"
    assert plan["known_information"]["interview_completed"] is False
    assert all("daughter" in q for q in questions(plan))
    assert any("subject" in q for q in questions(plan))
    assert all("How did" not in q and "Where" not in q for q in questions(plan))


def test_tutor_invented_destination_is_not_context_evidence():
    history = [
        {
            "learner_text": "My son needed to travel.",
            "tutor_reply": "Your son has a college interview.",
        }
    ]
    assert plan_context("My son caught the ferry and is relieved.", history) is None


def test_newer_completed_interview_blocks_old_future_context():
    history = [
        {
            "learner_text": "My son needs the ferry to reach his college interview.",
            "tutor_reply": "Okay.",
        },
        {"learner_text": "His interview is over now.", "tutor_reply": "Okay."},
    ]
    assert plan_context("My son caught the ferry and is relieved.", history) is None


def test_known_study_subject_does_not_get_reasked():
    history = [
        {
            "learner_text": "My son needs the ferry to reach his college interview.",
            "tutor_reply": "What subject does he want to study?",
        },
        {"learner_text": "He wants to study history.", "tutor_reply": "Okay."},
    ]
    plan = plan_context("My son caught the ferry and is relieved.", history)
    assert all(c["intent"] != "study_interest" for c in plan["choices"])


def test_explicit_tomorrow_is_not_an_ordinary_habit():
    plan = plan_context("I take the bus tomorrow because it's cheaper than driving.")
    assert plan["known_information"]["time"] == "future"
    assert all("usual" not in q for q in questions(plan))


def test_brothers_unfinished_question_is_not_learner_work():
    plan = plan_context(
        "I'm not disappointed. I expected this result because my brother didn't finish the last question."
    )
    assert all(c["intent"] != "unfinished_question_help" for c in plan["choices"])


def test_cancelled_interview_invalidates_old_future_plan():
    history = [
        {
            "learner_text": "My son needs the ferry to reach his college interview.",
            "tutor_reply": "Okay.",
        },
        {"learner_text": "His interview was cancelled.", "tutor_reply": "Okay."},
    ]
    assert plan_context("My son caught the ferry and is relieved.", history) is None


def test_other_relative_study_subject_is_not_sons_known_subject():
    history = [
        {
            "learner_text": "My son needs the ferry to reach his college interview.",
            "tutor_reply": "Okay.",
        },
        {"learner_text": "My daughter wants to study history.", "tutor_reply": "Okay."},
    ]
    plan = plan_context("My son caught the ferry and is relieved.", history)
    assert any(c["intent"] == "study_interest" for c in plan["choices"])


def test_feeling_about_someone_elses_interview_does_not_claim_attendance():
    assert (
        plan_context(
            "The interview is over now. She feels happy because he answered every question."
        )
        is None
    )
