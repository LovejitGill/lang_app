"""Checks are evidence filters, not semantic correctness scores."""

import asyncio

import httpx
import pytest

import contextual_conversation as flow


@pytest.mark.parametrize(
    "reply,text",
    [
        ("Describe your train journey.", "She goes to work by train."),
        ("Tell me about your trip to Paris.", "I took a trip."),
        ("Tell me about the train you saw today.", "I want to talk about trains."),
        ("You are very organized.", "I packed a bag."),
    ],
)
def test_detectable_changed_people_or_facts_are_rejected(reply, text):
    with pytest.raises(ValueError):
        flow.validate_question(reply, text, [])


def test_contextual_question_preserves_people_and_activity():
    text = "I cooked rice with my sister."
    reply = "Tell me how you cooked rice with your sister."
    assert flow.validate_question(reply, text, []) == reply


def test_copied_learner_fact_cannot_become_tutors_personal_claim():
    with pytest.raises(ValueError, match="extra_statement_or_first_person"):
        flow.validate_question(
            "Tell me about working from home. It helps me focus, but I miss talking to colleagues.",
            "Working from home helps me focus, but I miss talking to colleagues.",
            [],
        )


@pytest.mark.parametrize(
    "text,reply",
    [
        (
            "My name is Maya and I enjoy hiking.",
            "Tell me what interests you about hiking, with an example.",
        ),
        ("Pottery.", "Tell me what interests you about Pottery, with an example."),
        ("My brother missed his train.", "Tell me more about them and what happened."),
    ],
)
def test_self_introduction_fragments_and_neutral_person_reference(text, reply):
    assert flow.validate_question(reply, text, []) == reply


def test_rejected_raw_output_is_preserved_and_replaced_with_fallback():
    async def exercise():
        transport = httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": "Tell me about your train journey."},
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            return await flow.respond("She goes to work by train.", client=client)

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["rejection"] == "changed_person"
    assert result["raw"]["message"]["content"] == "Tell me about your train journey."
    assert "your train" not in result["reply"]


def test_slow_answer_is_a_failed_answer_not_a_successful_model_reply():
    cancelled = []

    async def slow(_):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
            return await flow.respond(
                "What is the difference between lend and borrow?",
                client=client,
                budget=0.03,
            )

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["support"] == "unsupported_question"
    assert result["raw"] is None
    assert cancelled == [True]


def test_stop_bypasses_generation_entirely():
    async def exercise():
        def forbidden(_):
            raise AssertionError("Stop should not trigger generation")

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(forbidden)
        ) as client:
            return await flow.respond("Let's stop here.", client=client)

    assert asyncio.run(exercise())["path"] == "deterministic"
