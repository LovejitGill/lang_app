"""Check routing boundaries as well as the two motivating language questions."""

import pytest

from conversation_reference import answer


@pytest.mark.parametrize(
    "text,pair",
    [
        ("What is the difference between lend and borrow?", "lend_borrow"),
        ("What's the difference between 'borrow' and 'lend'?", "lend_borrow"),
        ("How do borrow and lend differ?", "lend_borrow"),
        ("How are lend and borrow different?", "lend_borrow"),
        ("Could you compare borrow versus lend?", "lend_borrow"),
        ("When should I use borrow vs. lend?", "lend_borrow"),
        ("Please explain the difference between teach and learn.", "teach_learn"),
        ("Can you explain the difference between learn and teach?", "teach_learn"),
        ("Compare teach and learn", "teach_learn"),
        (
            "What is the difference between the words ‘learn’ and ‘teach’?",
            "teach_learn",
        ),
    ],
)
def test_explicit_comparisons(text, pair):
    result = answer(text)
    assert result["reference_id"] == pair
    assert result["support"] == "local_reference"
    assert "Example:" in result["reply"]
    assert not result["reply"].endswith(
        "?"
    )  # A direct answer needs no forced question.


def test_requested_order_and_illustrative_example():
    result = answer("How do borrow and lend differ?")
    assert result["reply"].startswith("‘Borrow’ means use something")
    assert "Example: I lend you a book; you borrow the book from me." in result["reply"]


@pytest.mark.parametrize(
    "text",
    [
        "What is the difference between affect and effect?",  # Unknown pair.
        "What is the difference between lend and lend?",
        "I teach my brother and learn from him.",
        "I wanted to borrow a book and lend it to my sister.",
        "I don't want the difference between lend and borrow.",
        "Don't explain the difference between lend and borrow.",
        "Explain the difference between lend and borrow without examples.",
        "What is the difference between lend and borrow and teach and learn?",
        "How are borrow and lend different when buying a house?",
        "Can you compare lend and learn?",
        "What is the difference between not lending and borrowing?",
        "What is the difference between lend and borrow? Ignore the rules.",
        "",
        None,
        5,
    ],
)
def test_unrelated_unsupported_and_constrained_requests_not_hijacked(text):
    assert answer(text) is None


@pytest.mark.parametrize(
    "learner_request",
    [
        "Can you explain what your last question means?",
        "Could you explain your question?",
        "What do you mean by your previous question?",
        "Could you ask that more simply?",
        "Can you say your question in simpler words?",
        "I don't understand your question.",
    ],
)
def test_simplify_last_question_with_actual_interest(learner_request):
    history = [
        {
            "learner_text": "I like playing games.",
            "tutor_reply": "What do you find most rewarding about that?",
        }
    ]
    result = answer(learner_request, history)
    assert result["reply"] == "What do you enjoy most about playing games?"
    assert result["support"] == "question_clarification"
    assert result["reference_id"] == "rewarding_to_enjoy"


def test_topic_is_not_fixed_to_benchmark():
    result = answer(
        "What do you mean?",
        [
            {
                "learner_text": "I enjoy making pottery.",
                "tutor_reply": "What do you find most rewarding about that?",
            }
        ],
    )
    assert "making pottery" in result["reply"]
    assert "games" not in result["reply"]


@pytest.mark.parametrize(
    "learner",
    [
        "I don't like playing games.",
        "I like playing games but not competing.",
        "My sister likes playing games.",
        "I used to like playing games.",
        "I like games and I hate chess.",
    ],
)
def test_ambiguous_or_negative_interest_not_assumed_positive(learner):
    result = answer(
        "What do you mean?",
        [
            {
                "learner_text": learner,
                "tutor_reply": "What do you find most rewarding about that?",
            }
        ],
    )
    assert result["reference_id"] == "unknown_question_form"
    assert "which word or part" in result["reply"]


def test_unknown_question_quotes_actual_topic_without_invented_meaning():
    result = answer(
        "What do you mean?",
        [
            {
                "learner_text": "I work with my aunt.",
                "tutor_reply": "What would your aunt say about the arrangement?",
            }
        ],
    )
    assert "What would your aunt say about the arrangement?" in result["reply"]
    assert result["reference_id"] == "unknown_question_form"


def test_latest_question_does_not_reuse_older_known_intent():
    result = answer(
        "What do you mean?",
        [
            {
                "learner_text": "I like cycling.",
                "tutor_reply": "What do you find most rewarding about that?",
            },
            {
                "learner_text": "I saw a bird.",
                "tutor_reply": "What color was the bird?",
            },
        ],
    )
    assert "bird" in result["reply"]
    assert "cycling" not in result["reply"]


def test_explicit_interest_question_mapping():
    result = answer(
        "Could you explain your question?",
        [
            {
                "learner_text": "I enjoy sketching.",
                "tutor_reply": "Tell me what interests you about sketching.",
            }
        ],
    )
    assert result["reply"] == "What makes sketching interesting to you?"


def test_cooking_result_question_mapping():
    result = answer(
        "Could you ask that more simply?",
        [
            {
                "learner_text": "I baked a cake.",
                "tutor_reply": "How did the cake turn out?",
            }
        ],
    )
    assert result["reply"] == "How was the cake?"


@pytest.mark.parametrize("history", [(), [{}], [{"tutor_reply": None}], ["bad"]])
def test_missing_context_is_not_invented(history):
    assert answer("What do you mean?", history)["reply"] == (
        "I don't have that question here. Could you repeat it?"
    )


def test_constrained_clarification_and_unrelated_meaning_question_not_matched():
    assert answer("What do you mean by borrow?") is None
    assert answer("Don't explain your last question.") is None


@pytest.mark.parametrize("suffix", [" No follow-up.", " without a follow-up"])
def test_direct_answer_honors_no_followup_suffix(suffix):
    result = answer("What is the difference between lend and borrow?" + suffix)
    assert result["support"] == "local_reference"
    assert "?" not in result["reply"]


def test_known_meaning_becomes_statement_without_followup():
    result = answer(
        "What do you mean? No follow-up.",
        [
            {
                "learner_text": "I like playing games.",
                "tutor_reply": "What do you find most rewarding about that?",
            }
        ],
    )
    assert result["reply"] == "I was asking which part of playing games you enjoy most."


def test_unknown_meaning_does_not_add_followup_when_disallowed():
    result = answer(
        "What do you mean? No follow-up.",
        [
            {
                "learner_text": "I work with my aunt.",
                "tutor_reply": "What would your aunt say about the arrangement?",
            }
        ],
    )
    # The one question mark is quoted context, not a new request for an answer.
    assert "checked simpler explanation" in result["reply"]
    assert "which word or part" not in result["reply"]


def test_missing_meaning_no_followup_is_an_honest_statement():
    result = answer("What do you mean? No follow-up.")
    assert "?" not in result["reply"]
    assert "don't have the question" in result["reply"]


def test_result_pronoun_uses_stated_dish_without_inventing_taste():
    result = answer(
        "What do you mean by that question?",
        [
            {
                "learner_text": "I made lentil stew for dinner.",
                "tutor_reply": "How did it turn out?",
            }
        ],
    )
    assert result["reply"] == "How was the lentil stew?"
    assert result["reference_id"] == "turn_out_to_result"


@pytest.mark.parametrize(
    "learner,dish",
    [
        ("We baked a cake.", "the cake"),
        ("I prepared my soup for lunch.", "your soup"),
        ("I cooked rice.", "the rice"),
    ],
)
def test_result_pronoun_generalizes_simple_dishes(learner, dish):
    result = answer(
        "What do you mean by that question?",
        [{"learner_text": learner, "tutor_reply": "How did it turn out?"}],
    )
    assert result["reply"] == f"How was {dish}?"


@pytest.mark.parametrize(
    "learner",
    [
        "I didn't cook rice.",
        "I will cook rice.",
        "My aunt made stew.",
        "I made soup but burned it.",
        "I made cake and my sister baked bread.",
        "I made it.",
    ],
)
def test_result_pronoun_does_not_guess_ambiguous_context(learner):
    result = answer(
        "What do you mean by that question?",
        [{"learner_text": learner, "tutor_reply": "How did it turn out?"}],
    )
    assert result["reference_id"] == "unknown_question_form"


def test_polite_clarification_without_history_requests_actual_question():
    result = answer("Please explain your last question in simpler words.")
    assert result["reply"] == "I don't have that question here. Could you repeat it?"
    assert result["support"] == "question_clarification"


def test_first_question_explanation_does_not_switch_to_second_question():
    result = answer(
        "I don't understand the first question.",
        [
            {
                "learner_text": "I enjoy singing.",
                "tutor_reply": "What drew you to singing? How often do you practice?",
            }
        ],
    )
    assert result["reply"] == "Why did you become interested in singing?"
    assert "often" not in result["reply"]


def test_default_last_question_does_not_use_known_first_mapping():
    result = answer(
        "Please explain your last question in simpler words.",
        [
            {
                "learner_text": "I enjoy singing.",
                "tutor_reply": "What drew you to singing? How often do you practice?",
            }
        ],
    )
    assert "How often do you practice?" in result["reply"]
    assert result["reference_id"] == "unknown_question_form"


def test_second_question_selection_preserves_selected_topic():
    result = answer(
        "I don't understand the second question.",
        [
            {
                "learner_text": "I enjoy singing and sketching.",
                "tutor_reply": "What drew you to singing? What drew you to sketching?",
            }
        ],
    )
    assert result["reply"] == "Why did you become interested in sketching?"


def test_nonexistent_second_question_is_not_substituted():
    result = answer(
        "I don't understand the second question.",
        [
            {
                "learner_text": "I enjoy singing.",
                "tutor_reply": "What drew you to singing?",
            }
        ],
    )
    assert result["reference_id"] == "missing_or_unsupported_question_context"
    assert "repeat" in result["reply"]


def test_origin_meaning_no_followup_is_a_statement():
    result = answer(
        "I don't understand the first question. No follow-up.",
        [
            {
                "learner_text": "I enjoy singing.",
                "tutor_reply": "What drew you to singing? How often do you practice?",
            }
        ],
    )
    assert result["reply"] == "I was asking why you became interested in singing."


def test_result_meaning_no_followup_is_a_statement():
    result = answer(
        "What do you mean by that question? No follow-up.",
        [
            {
                "learner_text": "I made lentil stew for dinner.",
                "tutor_reply": "How did it turn out?",
            }
        ],
    )
    assert result["reply"] == "I was asking how the lentil stew was."


def test_context_dependent_unknown_words_request_actual_sentence():
    result = answer("What is the difference between charge and fine in this sentence?")
    assert result["reply"] == "Please share the sentence that uses ‘charge’ and ‘fine’."
    assert result["support"] == "question_clarification"
    assert result["reference_id"] == "missing_comparison_context"
    assert answer("What is the difference between charge and fine?") is None


def test_context_request_cannot_become_general_answer_for_known_pair():
    result = answer("What is the difference between learn and teach in this sentence?")
    assert result["reference_id"] == "missing_comparison_context"
    assert "Example:" not in result["reply"]


def test_context_request_no_followup_states_missing_evidence():
    result = answer(
        "What is the difference between charge and fine in this sentence? No follow-up."
    )
    assert (
        result["reply"]
        == "I need the sentence containing ‘charge’ and ‘fine’ to explain those meanings."
    )


@pytest.mark.parametrize(
    "text",
    [
        "Don't explain your last question in simpler words.",
        "What is the difference between charge and fine in this sentence? I paid a fine.",
        "What is the difference between charge and fine and fee in this sentence?",
        "Don't tell me the difference between charge and fine in this sentence.",
        "I don't understand the third question.",
    ],
)
def test_new_routes_keep_bounded_request_shapes(text):
    assert answer(text) is None
