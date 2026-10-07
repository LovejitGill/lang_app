"""Check experiment isolation, raw failure retention and honest denominators."""

import json
import shutil
from unittest.mock import MagicMock

import pytest

import conversation_quality_eval as evaluation
from errors import LLMError


def example():
    return {
        "id": "test",
        "text": "What do I enjoy?",
        "level": "beginner",
        "scenario": "introductions",
        "history": [
            {
                "learner_text": "I enjoy painting.",
                "tutor_reply": "Describe a picture you painted.",
                "feedback": ["NEVER SEND THIS FEEDBACK"],
            }
        ],
        "expectation": "EVALUATION-ONLY SECRET",
        "require_followup": True,
    }


def test_same_context_without_rubric_or_grammar_feedback(monkeypatch):
    chat = MagicMock(
        return_value='{"reply":"You enjoy painting. Describe your favorite subject to paint."}'
    )
    monkeypatch.setattr(evaluation.llm_client, "_chat", chat)
    evaluation.run_attempt(example(), "baseline-v1", "fake")
    evaluation.run_attempt(example(), "grounded-v2", "fake")
    a, b = [c.args[0] for c in chat.call_args_list]
    assert a[0] != b[0]
    assert (
        a[1:]
        == b[1:]
        == [
            {"role": "user", "content": "I enjoy painting."},
            {"role": "assistant", "content": "Describe a picture you painted."},
            {"role": "user", "content": "What do I enjoy?"},
        ]
    )
    assert "EVALUATION-ONLY SECRET" not in str(a + b)
    assert "NEVER SEND THIS FEEDBACK" not in str(a + b)


def test_invalid_raw_output_retained_once(monkeypatch):
    chat = MagicMock(return_value='{"reply":42}')
    monkeypatch.setattr(evaluation.llm_client, "_chat", chat)
    row = evaluation.run_attempt(example(), "grounded-v2", "fake")
    assert row["raw"] == '{"reply":42}'
    assert row["status"] == "unavailable" and row["reply"] is None
    chat.assert_called_once()


def test_unavailable_call_and_partial_run_keep_denominator(monkeypatch):
    chat = MagicMock(side_effect=LLMError("offline"))
    monkeypatch.setattr(evaluation.llm_client, "_chat", chat)
    row = evaluation.run_attempt(example(), "grounded-v2", "fake")
    summary = evaluation.summarize(
        [row, {"variant": "baseline-v1", "attempt_state": "started"}],
        ["grounded-v2", "baseline-v1"],
    )
    assert summary["grounded-v2"]["denominator"] == 16
    assert summary["grounded-v2"]["unavailable"] == 1
    assert summary["grounded-v2"]["human_useful"] is None
    assert summary["baseline-v1"]["denominator"] == 16
    assert summary["baseline-v1"]["attempts_started"] == 1
    assert summary["baseline-v1"]["timing"]["attempts"] == 0
    chat.assert_called_once()


def test_run_protects_existing_evidence(tmp_path, monkeypatch):
    path = tmp_path / "results.json"
    path.write_text("preserve")
    client = MagicMock()
    monkeypatch.setattr(evaluation.httpx, "Client", client)
    with pytest.raises(ValueError, match="Preserve"):
        evaluation.run(path)
    assert path.read_text() == "preserve"
    client.assert_not_called()


def test_dataset_identity_checked_before_inference(tmp_path):
    for name in ("protocol.json", "cases.json"):
        shutil.copy(evaluation.DIRECTORY / name, tmp_path / name)
    path = tmp_path / "cases.json"
    data = json.loads(path.read_text())
    data["cases"][0]["text"] = "Changed case"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Development cases changed"):
        evaluation.verify(tmp_path)


def test_every_attempt_checkpointed_and_order_alternates(tmp_path, monkeypatch):
    path = tmp_path / "results.json"
    protocol, data = evaluation.verify()
    response = MagicMock()
    response.json.return_value = {
        "models": [{"name": protocol["model"], "digest": protocol["model_digest"]}]
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = response
    monkeypatch.setattr(evaluation.httpx, "Client", lambda **kwargs: client)
    seen = []

    def attempt(case, variant, model):
        stored = json.loads(path.read_text())["rows"][-1]
        assert stored == {
            "case_id": case["id"],
            "variant": variant,
            "attempt_state": "started",
        }
        seen.append((case["id"], variant))
        return {
            **stored,
            "attempt_state": "complete",
            "status": "valid",
            "seconds": 0.1,
            "reply": "Test reply.",
        }

    monkeypatch.setattr(evaluation, "run_attempt", attempt)
    result = evaluation.run(path)
    assert len(seen) == 32
    for i, case in enumerate(data["cases"]):
        variants = (
            ["baseline-v1", "grounded-v2"]
            if i % 2 == 0
            else ["grounded-v2", "baseline-v1"]
        )
        assert seen[2 * i : 2 * i + 2] == [(case["id"], v) for v in variants]
    assert all(r["attempt_state"] == "complete" for r in result["rows"])
    assert result["summary"]["baseline-v1"]["valid"] == 16


def test_structured_candidate_combines_fields_in_one_model_call(monkeypatch, tmp_path):
    import db
    from separate_feedback import conversation_reply

    path = tmp_path / "history.sqlite"
    db.init_db(path)
    chat = MagicMock(
        return_value='{"answer":"You enjoy painting.","follow_up":"Describe a painting you made."}'
    )
    monkeypatch.setattr(evaluation.llm_client, "_chat", chat)
    reply = conversation_reply(
        "What do I enjoy?",
        level="beginner",
        scenario="introductions",
        session_id="test",
        db_path=path,
        prompt_variant="structured-v4",
    )
    assert reply == "You enjoy painting. Describe a painting you made."
    chat.assert_called_once()
    assert set(chat.call_args.kwargs["schema"]["required"]) == {"answer", "follow_up"}
    assert db.get_history("test", db_path=path) == []


@pytest.mark.parametrize(
    "raw",
    [
        '{"answer":"Hi"}',
        '{"answer":"", "follow_up":"  "}',
        '{"answer":"Hi", "follow_up":5}',
        json.dumps({"answer": "a" * 200, "follow_up": "b" * 200}),
    ],
)
def test_structured_candidate_rejects_unusable_output(raw):
    from errors import LLMResponseError
    from separate_feedback import parse_conversation_reply

    with pytest.raises(LLMResponseError):
        parse_conversation_reply(raw, "structured-v4")
