"""Tests for facts, unanswered question choices, and bounded local selection."""

import asyncio
import json

import httpx
import pytest

import dialogue_planner as flow


def history(learner, tutor):
    return [{"learner_text": learner, "tutor_reply": tutor}]


@pytest.mark.parametrize(
    "text", ["I packed seven bottle.", "I have packed my notebooks."]
)
def test_packing_does_not_invent_a_container(text):
    plan = flow.prepare(text)
    assert plan["frame"] == "packing"
    assert all("bag" not in q and "suitcase" not in q for q in plan["options"])
    assert "packing_purpose" in plan["question_intents"]


def test_packing_does_not_reask_explicit_purpose():
    plan = flow.prepare("I packed my notebooks for school.")
    assert "packing_purpose" not in plan["question_intents"]


@pytest.mark.parametrize(
    "text", ["I didn't pack the notebooks.", "If I packed my coat, would I need a bag?"]
)
def test_negated_or_hypothetical_packing_does_not_become_a_completed_event(text):
    assert flow.prepare(text)["frame"] != "packing"


def test_unfinished_task_keeps_negation_and_emotion():
    plan = flow.prepare("I couldn't finish my assignment and I feel disappointed.")
    assert plan["known_information"]["finished"] is False
    assert plan["known_information"]["feeling"] == "disappointed"
    assert "disappointed" in plan["prefix"]
    assert all("your assignment" in q for q in plan["options"])
    assert "obstacle" in plan["question_intents"]


def test_unfinished_task_without_feeling_does_not_invent_one():
    plan = flow.prepare("I did not finish my painting.")
    assert not plan["prefix"]
    assert plan["known_information"]["feeling"] is None


@pytest.mark.parametrize(
    "text",
    [
        "I finished my assignment.",
        "I couldn't finish my assignment yesterday, but I finished it today.",
    ],
)
def test_completed_or_updated_task_not_declared_unfinished(text):
    assert flow.prepare(text)["frame"] != "unfinished_task"


@pytest.mark.parametrize(
    "text,dish",
    [
        ("I will cook rice with my sister tomorrow.", "rice"),
        ("I am going to bake a cake tonight.", "a cake"),
        ("I will prepare pasta next week.", "pasta"),
    ],
)
def test_future_food_questions_do_not_reask_the_plan_or_past_result(text, dish):
    plan = flow.prepare(text)
    assert plan["known_information"]["dish"] == dish
    assert plan["known_information"]["completed"] is False
    assert "preparation_method" in plan["question_intents"]
    assert all(
        "taste" not in q and not q.startswith("Will you") for q in plan["options"]
    )


@pytest.mark.parametrize(
    "text", ["I won't cook rice tomorrow.", "I might cook rice tomorrow."]
)
def test_absent_or_uncertain_plan_not_treated_as_a_commitment(text):
    assert flow.prepare(text)["frame"] != "planned_meal"


def test_known_relief_is_not_reasked_or_made_into_a_missed_train():
    plan = flow.prepare("My sister is relieved because she caught her bus.")
    assert plan["known_information"]["caught"] is True
    assert all("sister" in q and "bus" in q for q in plan["options"])
    assert all("feel" not in q and "miss" not in q for q in plan["options"])


def test_missed_transport_not_declared_caught():
    assert (
        flow.prepare("My brother is upset because he missed his train.")["frame"]
        != "caught_transport"
    )


def test_recall_followup_names_actual_hobby():
    plan = flow.prepare(
        "What is my name and what hobby did I mention?",
        history=history("My name is Zoë and I enjoy weaving.", "Tell me more."),
    )
    assert "Zoë" in plan["prefix"]
    assert all("weaving" in q for q in plan["options"])
    assert plan["frame"] == "recalled_interest"


def test_changed_interest_not_resurrected():
    plan = flow.prepare(
        "What do I enjoy?",
        history=[
            {"learner_text": "I enjoy swimming.", "tutor_reply": "Tell me more."},
            {
                "learner_text": "I don't enjoy swimming anymore.",
                "tutor_reply": "Understood.",
            },
        ],
    )
    assert plan["frame"] == "changed_interest"
    assert "don't enjoy swimming anymore" in plan["prefix"]
    assert all("swimming" not in q for q in plan["options"])


def test_assistant_claim_does_not_become_learner_interest():
    plan = flow.prepare(
        "What is my hobby?", history=history("Hello!", "Your hobby is skiing.")
    )
    assert plan["frame"] != "recalled_interest"
    assert "skiing" not in plan["prefix"]


def test_previously_asked_question_is_removed_from_choices():
    plan = flow.prepare(
        "I packed seven bottles.",
        history=history("I am getting ready.", "What were you packing for?"),
    )
    assert "packing_purpose" not in plan["question_intents"]


def test_recall_without_followup_keeps_only_answer():
    plan = flow.prepare(
        "What is my hobby? No follow-up.",
        history=history("I enjoy painting.", "Tell me more."),
    )
    assert plan["options"] == []
    assert "painting" in plan["prefix"]


async def no_correction(*args, **kwargs):
    return {"state": "no_supported_correction"}


def test_selector_only_chooses_authored_text_and_does_not_receive_test_labels(
    monkeypatch,
):
    requests = []
    monkeypatch.setattr(flow, "get_correction", no_correction)

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"done": True, "message": {"content": "1"}})

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            return await flow.respond(
                "I packed seven bottles.",
                history=[
                    {
                        "learner_text": "Hello!",
                        "tutor_reply": "Hello!",
                        "expectation": "PRIVATE_LABEL",
                    }
                ],
                client=client,
            )

    result = asyncio.run(exercise())
    assert result["path"] == "model_selected"
    assert result["reply"] == result["plan"]["options"][1]
    assert result["question_intent"] == "packing_choice"
    assert "PRIVATE_LABEL" not in json.dumps(requests)
    assert requests[0]["options"]["num_predict"] == 8


@pytest.mark.parametrize(
    "raw",
    [
        [],
        None,
        {"done": True, "message": {"content": None}},
        {"done": True, "message": {"content": "true"}},
        {"done": True, "message": {"content": "99"}},
        {"done": True, "done_reason": "length", "message": {"content": "0"}},
    ],
)
def test_invalid_selection_preserves_raw_and_falls_back(raw):
    async def exercise():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=json.dumps(raw))
            )
        ) as client:
            return await flow._reply(
                flow.prepare("I packed seven bottles."), [], 0.1, client
            )

    result = asyncio.run(exercise())
    assert result["path"] == "local_fallback"
    assert result["raw"] == raw
    assert result["reply"] == "What were you packing for?"


def test_slow_selector_is_cancelled_without_losing_supported_correction(monkeypatch):
    cancelled = []

    async def slow(_):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)

    async def correction(*args, **kwargs):
        return {
            "state": "offered",
            "corrected_text": "I packed seven bottles.",
            "explanation": "More than one needs the plural.",
        }

    monkeypatch.setattr(flow, "get_correction", correction)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
            return await flow.respond(
                "I packed seven bottle.", client=client, budget=0.02
            )

    result = asyncio.run(exercise())
    assert cancelled == [True]
    assert result["path"] == "local_fallback"
    assert result["display_text"].startswith("“I packed seven bottles.”")


def test_varied_repair_action_keeps_object_and_prior_feeling():
    plan = flow.prepare("I couldn't repair the chair, and I feel frustrated.")
    assert plan["known_information"]["action"] == "repair"
    assert all("chair" in q for q in plan["options"])
    assert "frustrated" in plan["prefix"]
    assert all("your chair" not in q for q in plan["options"])


def test_future_contraction_and_already_given_choice_reason():
    plan = flow.prepare(
        "I'm going to bake bread with my neighbor on Sunday.",
        history=history(
            "We chose a rye bread recipe because my neighbor likes rye.",
            "When are you planning to bake it?",
        ),
    )
    assert plan["known_information"]["dish"] == "bread"
    assert plan["question_intents"] == ["preparation_method"]
    assert "Sunday" not in plan["options"][0]


def test_known_transport_purpose_is_not_reasked():
    plan = flow.prepare(
        "My son caught the ferry and is relieved.",
        history=history(
            "My son needs the ferry to reach his college interview.", "Did he catch it?"
        ),
    )
    assert plan["known_information"]["caught"] is True
    assert "destination" not in plan["question_intents"]
    assert "feel" not in plan["options"][0]


def test_changed_hobby_and_another_question_control_together():
    plan = flow.prepare(
        "What hobby do I enjoy now? Please don't ask another question.",
        history=history(
            "I don't enjoy jogging anymore. Now I enjoy making jewelry.",
            "What do you like making?",
        ),
    )
    assert "Now I enjoy making jewelry." in plan["prefix"]
    assert plan["options"] == []
    assert "?" not in plan["prefix"]


def test_reference_answer_precedes_old_unsupported_route():
    plan = flow.prepare("What is the difference between lend and borrow?")
    assert plan["support"] == "local_reference"
    assert "lend" in plan["prefix"].lower() and "borrow" in plan["prefix"].lower()
    assert plan["options"] == []


def test_clarification_explains_referenced_first_question():
    plan = flow.prepare(
        "I don't understand the first question.",
        history=history(
            "I joined a choir last month.",
            "What drew you to singing? How often do you practice?",
        ),
    )
    assert plan["support"] == "question_clarification"
    assert "interested in singing" in plan["prefix"]
    assert "often" not in plan["prefix"]


def test_explicit_past_walk_avoids_invented_scenery_without_changing_habit():
    past = flow.prepare("Yesterday I take a short walk.")
    habitual = flow.prepare("I take a short walk because it helps me relax.")
    assert past["frame"] == "past_walk"
    assert all("scenery" not in q and "fresh air" not in q for q in past["options"])
    assert habitual["frame"] == "habitual_walk"


@pytest.mark.parametrize(
    "text", ["I cooked rice. Do not ask questions.", "Don't ask another question."]
)
def test_broader_no_question_control_never_returns_empty_reply(text):
    plan = flow.prepare(text)
    assert plan["options"] == []
    assert plan["prefix"].strip()
    assert "?" not in plan["prefix"]


def test_dairy_constraint_survives_in_prefix_before_soup_followup():
    plan = flow.prepare(
        "I'd like soup, but I can't eat dairy.", scenario="ordering food"
    )
    assert plan["frame"] == "food_constraint"
    assert "can't eat dairy" in plan["prefix"]
    assert all("soup" in q for q in plan["options"])
    assert "safe" not in str(plan).lower()


def test_other_person_diet_is_not_assigned_to_learner():
    plan = flow.prepare(
        "My sister can't eat dairy. I'd like soup, and she wants a sandwich.",
        scenario="ordering food",
    )
    assert "Your sister can't eat dairy." in plan["prefix"]
    assert "You can't eat dairy" not in plan["prefix"]


def test_person_revision_overrides_older_food_constraint():
    plan = flow.prepare(
        "Actually, the dairy-free meal is for my brother, not me. I want soup.",
        scenario="ordering food",
        history=history("I need a dairy-free meal.", "What would you like?"),
    )
    assert "for your brother" in plan["prefix"]
    assert "for you." not in plan["prefix"]


def test_exhausted_constraint_questions_do_not_reenter_free_generation():
    text = "I'd like soup, but I can't eat dairy."
    first = flow.prepare(text, scenario="ordering food")
    turns = [{"learner_text": text, "tutor_reply": q} for q in first["options"]]
    plan = flow.prepare(text, scenario="ordering food", history=turns)
    assert plan["support"] == "context_acknowledgment"
    assert plan["options"] == []
    assert "dairy" in plan["prefix"]


def test_constraint_planning_keeps_no_followup_control():
    plan = flow.prepare(
        "I'd like soup, but I can't eat dairy. No follow-up.", scenario="ordering food"
    )
    assert plan["options"] == []
    assert plan["prefix"].strip()


def test_food_planner_does_not_interpret_general_requests_as_meals():
    plan = flow.prepare("I want a new job.", scenario="daily activities")
    assert plan["frame"] != "food_constraint"
