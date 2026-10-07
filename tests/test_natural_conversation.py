"""Regression checks for the owner's partial review, without model inference.

These checks protect observable behavior; passing them is not a human quality
score, a broad grammar claim, or evidence of two-second spoken interaction.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

import natural_conversation as flow
import timely_corrections

CASES = json.loads(
    (
        Path(flow.__file__).parent
        / "evaluation/conversation_quality/contextual_v2/cases.json"
    ).read_text()
)["cases"]


def _history(*inputs):
    return [{"learner_text": text, "tutor_reply": "Tell me more."} for text in inputs]


def _checker_match(text, original, replacement, rule_id):
    # ASCII fixtures keep code-point and UTF-16 offsets identical here.
    offset = text.index(original)
    return {
        "software": {"version": "6.6"},
        "warnings": {"incompleteResults": False},
        "matches": [
            {
                "offset": offset,
                "length": len(original),
                "context": {
                    "text": text,
                    "offset": offset,
                    "length": len(original),
                },
                "rule": {"id": rule_id},
                "replacements": [{"value": replacement}],
            }
        ],
    }


@pytest.mark.parametrize(
    "text,dish",
    [
        ("I cooked rice with my sister.", "rice"),
        ("I cooked pasta with my brother.", "pasta"),
        ("We prepared noodles with our cousin.", "noodles"),
    ],
)
def test_completed_cooking_retains_stated_food_without_a_sentence_whitelist(text, dish):
    plan = flow.prepare(text)
    assert plan["frame"] == "cooking_result"
    assert dish in plan["options"][0]
    assert "turn out" in plan["options"][0]
    assert "delicious" not in plan["options"][0]


def test_future_cooking_does_not_assume_an_already_tasted_meal():
    plan = flow.prepare("I will cook rice with my sister tomorrow.")
    assert plan["frame"] != "cooking_result"
    assert "How did the rice turn out?" not in plan["options"]


def test_negated_commute_is_neither_positive_train_trip_nor_goes_correction():
    text = "She doesn't go to work by train."
    plan = flow.prepare(text)
    assert plan["frame"] != "commute_duration"
    assert all("her train journey" not in option for option in plan["options"])
    # Even if a checker supplied this inappropriate suggestion, context rejects it.
    raw = _checker_match(text, "go", "goes", "HE_VERB_AGR")
    assert timely_corrections._select(text, raw)["state"] == "no_supported_correction"


def test_habitual_and_completed_walks_keep_their_time_meaning():
    habit = flow.prepare("I take a short walk because it helps me relax.")
    completed = flow.prepare("I took a short walk because it helps me relax.")
    assert habit["frame"] == "habitual_walk"
    assert completed["frame"] == "completed_walk"
    assert "How did" not in habit["options"][0]
    assert "How did" in completed["options"][0]
    with pytest.raises(ValueError, match="changed_habit_to_past"):
        flow.validate("How did your walk feel?", habit, [])


def test_habitual_take_is_not_changed_to_took_by_the_fast_adapter():
    text = "I take a short walk because it helps me relax."
    raw = _checker_match(text, "take", "took", "HE_VERB_AGR")
    assert timely_corrections._select(text, raw)["state"] == "no_supported_correction"


def test_unspecified_walk_does_not_become_a_short_walk():
    plan = flow.prepare("I take a walk.")
    assert "short" not in plan["options"][0].casefold()


def test_food_preference_article_does_not_follow_your():
    plan = flow.prepare("I would like a salad.", scenario="ordering food")
    assert "salad" in plan["options"][0]
    assert "your a salad" not in plan["options"][0]


def test_unknown_workplace_keeps_uncle_and_work_relation():
    plan = flow.prepare("Where does my uncle work?")
    assert plan["frame"] == "relative_fact"
    assert "I don't know where your uncle works." in plan["prefix"]
    assert "uncle" in plan["prefix"] and "work" in plan["prefix"]
    assert "that person or place" not in plan["prefix"]


def test_latest_job_change_invalidates_older_known_workplace():
    plan = flow.prepare(
        "Where does my uncle work?",
        history=_history(
            "My uncle works at a library.",
            "My uncle used to work at a library, but he changed jobs.",
        ),
    )
    assert "I don't know where your uncle works." in plan["prefix"]
    assert "You said" not in plan["prefix"]
    assert "works at a library" not in plan["prefix"]


@pytest.mark.parametrize(
    "question,evidence",
    [
        ("Where does my uncle work?", "My uncle works at a library."),
        ("Where does my cousin live?", "My cousin lives in Leeds."),
    ],
)
def test_known_location_uses_actual_learner_evidence(question, evidence):
    plan = flow.prepare(question, history=_history(evidence))
    assert evidence in plan["prefix"]
    assert "I don't know" not in plan["prefix"]


def test_tutor_claim_alone_cannot_establish_relative_workplace():
    plan = flow.prepare(
        "Where does my uncle work?",
        history=[
            {"learner_text": "Hello!", "tutor_reply": "Your uncle works at a library."}
        ],
    )
    assert "I don't know where your uncle works." in plan["prefix"]
    assert "library" not in plan["prefix"]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_all_prepared_fallback_options_remove_automatic_padding(case):
    plan = flow.prepare(
        case["text"],
        history=case["history"],
        level=case["level"],
        scenario=case["scenario"],
    )
    for piece in [plan["prefix"], *plan["options"]]:
        assert "with an example" not in piece.casefold()
        assert "with one example" not in piece.casefold()
        assert "with a few details" not in piece.casefold()
        assert "in more detail" not in piece.casefold()


def test_c01_retains_exact_approved_direction_without_example_tail():
    plan = flow.prepare(
        "My name is Luis and I enjoy sketching.", scenario="introductions"
    )
    assert plan["options"] == ["Tell me what interests you about sketching."]


@pytest.mark.parametrize(
    "reply",
    ["How did the rice turn out?", "What type of rice did you cook?"],
)
def test_natural_how_and_what_questions_are_accepted(reply):
    plan = flow.prepare("I cooked rice with my sister.")
    assert flow.validate(reply, plan, []) == reply


def test_third_person_commute_cannot_become_the_learners_journey():
    plan = flow.prepare("She go to work by train.")
    assert flow.validate("How long does her train journey take?", plan, [])
    with pytest.raises(ValueError, match="changed_person"):
        flow.validate("How long does your journey by train take?", plan, [])


def test_first_person_commute_can_ask_about_the_learners_journey():
    plan = flow.prepare("I go to work by train.")
    reply = "How long does your train journey take?"
    assert flow.validate(reply, plan, []) == reply


@pytest.mark.parametrize(
    "reply",
    [
        "What happened next?",
        "How did the rice turn out, with an example?",
        "Describe your rice in more detail.",
        "I love rice. How did yours turn out?",
        "My favorite food is rice. How did yours turn out?",
        "We love rice. How did yours turn out?",
        "Our favorite dish is rice. How did yours turn out?",
    ],
)
def test_lost_topic_padding_and_invented_tutor_perspective_are_rejected(reply):
    with pytest.raises(ValueError):
        flow.validate(reply, flow.prepare("I cooked rice with my sister."), [])


@pytest.mark.parametrize(
    "text,corrected,explanation,model_reply",
    [
        (
            "Did you visited the castle?",
            "Did you visit the castle?",
            "Use visit after did.",
            "Which castle would you like to visit?",
        ),
        (
            "She go to work by train.",
            "She goes to work by train.",
            "Use goes with she in the present tense.",
            "How long does her train journey to work take?",
        ),
    ],
)
def test_verified_correction_is_displayed_before_conversation(
    monkeypatch, text, corrected, explanation, model_reply
):
    correction_calls = []
    checker_client = object()

    async def correction(input_text, *, client):
        correction_calls.append((input_text, client))
        return {
            "state": "offered",
            "corrected_text": corrected,
            "explanation": explanation,
        }

    monkeypatch.setattr(flow, "get_correction", correction)

    async def exercise():
        def answer(_):
            return httpx.Response(
                200,
                json={
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": model_reply},
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(answer)) as client:
            return await flow.respond(
                text, client=client, correction_client=checker_client
            )

    result = asyncio.run(exercise())
    assert correction_calls == [(text, checker_client)]
    assert result["display_text"] == f"“{corrected}” {explanation} {result['reply']}"
    assert result["correction"]["state"] == "offered"
    assert result["seconds"] >= 0
    assert result["reply"] != result["display_text"]


@pytest.mark.parametrize("state", ["unavailable", "no_supported_correction"])
def test_no_correction_is_invented_when_checker_abstains(monkeypatch, state):
    async def correction(_, *, client):
        return {"state": state}

    monkeypatch.setattr(flow, "get_correction", correction)

    async def exercise():
        transport = httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": "How do you feel after your walk?"},
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            return await flow.respond(
                "I take a short walk because it helps me relax.", client=client
            )

    result = asyncio.run(exercise())
    assert result["display_text"] == result["reply"]
    assert result["correction"]["state"] == state
    assert "took" not in result["display_text"]


def test_slow_generation_is_cancelled_and_keeps_verified_correction(monkeypatch):
    cancelled = []

    async def correction(_, *, client):
        return {
            "state": "offered",
            "corrected_text": "She goes to work by train.",
            "explanation": "Use goes with she.",
        }

    async def slow(_):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)

    monkeypatch.setattr(flow, "get_correction", correction)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
            return await flow.respond(
                "She go to work by train.", client=client, budget=0.02
            )

    result = asyncio.run(exercise())
    assert cancelled == [True]
    assert result["path"] == "local_fallback"
    assert result["rejection"] == "TimeoutError"
    assert "her train journey" in result["reply"]
    assert result["display_text"].startswith(
        "“She goes to work by train.” Use goes with she. "
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "My name is Luis and I enjoy sketching.",
            "Tell me what interests you about sketching.",
        ),
        ("Let's stop here.", "Thanks for practicing. Goodbye!"),
    ],
)
def test_accepted_interest_question_and_stop_do_not_need_generation(
    monkeypatch, text, expected
):
    async def correction(_, *, client):
        return {"state": "no_supported_correction"}

    monkeypatch.setattr(flow, "get_correction", correction)

    async def exercise():
        def forbidden(_):
            raise AssertionError("This response should not request model inference")

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(forbidden)
        ) as client:
            return await flow.respond(text, client=client)

    result = asyncio.run(exercise())
    assert result["path"] == "deterministic"
    assert result["reply"] == expected


def test_cooking_question_asks_about_result_or_type():
    plan = flow.prepare("I cooked rice with my sister.")
    with pytest.raises(ValueError, match="cooking_question_needs_result_or_type"):
        flow.validate("Did you enjoy the rice?", plan, [])
    assert flow.validate("How did the rice taste?", plan, [])
    assert flow.validate("What kind of rice did you cook?", plan, [])


def test_unknown_hobby_is_named_instead_of_generic_missing_information():
    plan = flow.prepare("What hobby did I mention?")
    assert "hobby" in plan["prefix"]
    assert "enjoy doing" in plan["prefix"]
    assert "that information" not in plan["prefix"]


def test_continue_request_does_not_invent_feeling_stuck():
    plan = flow.prepare("I don't want to stop practicing.")
    assert plan["frame"] == "continue_practice"
    assert "keep practicing" in plan["prefix"]
    assert "stuck" not in plan["prefix"]


def test_relaxing_habit_question_develops_the_stated_reason():
    plan = flow.prepare("I take a short walk because it helps me relax.")
    assert plan["options"] == ["What about the walk helps you relax?"]
    assert plan["frame"] == "habitual_walk"


def test_meal_question_preserves_dish_not_just_a_modifier():
    plan = flow.prepare("I would like vegetable soup.", scenario="ordering food")
    with pytest.raises(ValueError, match="lost_topic"):
        flow.validate("What kind of vegetables do you prefer?", plan, [])
    assert flow.validate("What would you like to have with your soup?", plan, [])


@pytest.mark.parametrize(
    "raw",
    [
        [],
        None,
        {"message": None},
        {"message": {"content": None}},
        {"message": {"content": 42}},
        {"message": []},
    ],
)
def test_malformed_successful_http_response_keeps_authored_fallback(raw):
    async def exercise():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=json.dumps(raw))
            )
        ) as client:
            return await flow._reply(flow.prepare("I cooked rice."), [], 0.1, client)

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["reply"] == "How did the rice turn out?"
    assert result["raw"] == raw
    assert result["rejection"] == "TypeError"


def test_synchronous_validation_overrun_discards_late_model_output(monkeypatch):
    clock = {"now": 0.0}
    validate = flow.validate

    def slow_validation(*args):
        answer = validate(*args)
        clock["now"] = 0.3
        return answer

    monkeypatch.setattr(flow, "perf_counter", lambda: clock["now"])
    monkeypatch.setattr(flow, "validate", slow_validation)

    async def exercise():
        raw = {"done": True, "message": {"content": "How did your rice taste?"}}
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=json.dumps(raw))
            )
        ) as client:
            return await flow._reply(flow.prepare("I cooked rice."), [], 0.1, client)

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["rejection"] == "TimeoutError"
    assert result["raw"]["message"]["content"] == "How did your rice taste?"
