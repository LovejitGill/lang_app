"""Meaningful boundaries for the proposed low-latency conversation path."""

import asyncio
import json
from time import perf_counter

import httpx
import pytest

import bounded_conversation as flow


@pytest.mark.parametrize("text", ["", "  ", None, "a" * 1001])
def test_invalid_input_fails_before_inference(text):
    with pytest.raises(ValueError):
        asyncio.run(flow.respond(text))


def test_stop_is_not_triggered_by_negation_or_quoted_speech():
    assert (
        flow.prepare("Thanks, that's enough practice for today.")["support"] == "stop"
    )
    assert flow.prepare("I don't want to stop practicing.")["support"] != "stop"
    assert flow.prepare('My friend said "goodbye" and left.')["support"] != "stop"


def test_recall_uses_learner_evidence_not_invented_assistant_facts():
    history = [{"learner_text": "Hello!", "tutor_reply": "Your hobby is skiing."}]
    plan = flow.prepare("What is my hobby?", history=history)
    assert "don't have" in plan["prefix"]
    assert "skiing" not in plan["prefix"]


def test_changed_hobby_is_quoted_with_negation_intact():
    history = [
        {"learner_text": "I enjoy skiing.", "tutor_reply": "Tell me more."},
        {"learner_text": "I don't enjoy skiing anymore.", "tutor_reply": "Understood."},
    ]
    plan = flow.prepare("What do I enjoy? No follow-up.", history=history)
    assert "I don't enjoy skiing anymore." in plan["prefix"]
    assert plan["options"] == []


@pytest.mark.parametrize(
    "source",
    [
        "Imagine my name is Alex.",
        "I said my name is Alex in a play.",
        'My name in the story is "Alex".',
        "Is my name Alex?",
    ],
)
def test_hypothetical_or_quoted_name_not_used_as_personal_evidence(source):
    history = [{"learner_text": source, "tutor_reply": "Okay."}]
    assert "don't have" in flow.prepare("What is my name?", history=history)["prefix"]


def test_topic_change_does_not_reuse_previous_topic():
    plan = flow.prepare("I want to talk about astronomy instead.")
    assert all("astronomy" in q for q in plan["options"])
    assert all("instead" not in q for q in plan["options"])


def test_question_answering_limit_is_explicit_not_counted_as_success():
    plan = flow.prepare("What is the difference between lend and borrow?")
    assert plan["support"] == "unsupported_question"
    assert "doesn't have an answer" in plan["prefix"]


def test_previous_exact_question_removed_if_an_alternative_exists():
    text = "I enjoyed a long walk."
    first = flow.prepare(text)["options"][0]
    plan = flow.prepare(
        text, history=[{"learner_text": "I went outside.", "tutor_reply": first}]
    )
    assert first not in plan["options"]


def test_selector_never_receives_rubric_or_grammar_feedback():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200, json={"done": True, "done_reason": "stop", "message": {"content": "1"}}
        )

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await flow.respond(
                "I packed a bag.",
                history=[
                    {
                        "learner_text": "I am traveling.",
                        "tutor_reply": "Tell me more.",
                        "feedback": ["PRIVATE_RUBRIC"],
                        "expected": "PRIVATE_ANSWER",
                    }
                ],
                client=client,
            )

    result = asyncio.run(exercise())
    assert result["path"] == "model_selected"
    assert result["reply"] == result["plan"]["options"][1]
    assert "PRIVATE_" not in json.dumps(captured)
    assert captured[0]["options"]["num_predict"] == 8
    assert captured[0]["think"] is False


@pytest.mark.parametrize(
    "content,done_reason",
    [
        ("true", "stop"),
        ("99", "stop"),
        ('"0"', "stop"),
        ("0", "length"),
        ("garbage", "stop"),
    ],
)
def test_malformed_or_truncated_selection_keeps_safe_fallback(content, done_reason):
    async def exercise():
        transport = httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "done": True,
                    "done_reason": done_reason,
                    "message": {"content": content},
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            return await flow.respond("Pottery.", client=client)

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["reply"] == result["plan"]["options"][0]


def test_deadline_cancels_slow_request_without_background_task():
    cancelled = []

    async def slow(_):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
            start = perf_counter()
            result = await flow.respond("Pottery.", client=client, budget=0.03)
            assert perf_counter() - start < 0.5
            assert not [
                t
                for t in asyncio.all_tasks()
                if t is not asyncio.current_task() and not t.done()
            ]
            return result

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["selector_error"] == "TimeoutError"
    assert cancelled == [True]


def test_connection_failure_is_visible_and_does_not_fabricate_model_output():
    def fail(_):
        raise httpx.ConnectError("private diagnostic")

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(fail)) as client:
            return await flow.respond("Pottery.", client=client)

    result = asyncio.run(exercise())
    assert result["raw_selector"] is None
    assert result["selector_error"] == "ConnectError"
    assert "private diagnostic" not in json.dumps(result)
