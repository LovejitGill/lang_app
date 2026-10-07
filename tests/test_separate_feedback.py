"""Replay the reviewed evidence through the app adapter; test safe service failures."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

import db
import llm_client
import separate_feedback as flow
from errors import LLMError, LLMResponseError

DIRECTORY = Path(__file__).resolve().parents[1] / "evaluation/detection_flow_validation"


@pytest.fixture
def transport(monkeypatch):
    response = MagicMock()
    response.json.return_value = {
        "models": [{"name": flow.GRAMMAR_MODEL, "digest": flow.GRAMMAR_DIGEST}]
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = response
    client.post.return_value = response
    factory = MagicMock(return_value=client)
    monkeypatch.setattr(flow.httpx, "Client", factory)
    return client, factory


def test_all_32_reviewed_decisions_survive_app_adapter(monkeypatch, transport):
    client, factory = transport
    source = json.loads((DIRECTORY / "results.json").read_text())
    for row in source["rows"]:
        base = MagicMock()
        base.json.return_value = row["builtin"]
        client.post.return_value = base
        generator = MagicMock(return_value=row["generation"])
        custom = MagicMock(return_value=row["supplemental"])
        monkeypatch.setattr(flow, "check_sentence", generator)
        monkeypatch.setattr(flow, "collect_count_evidence", custom)
        actual = flow.grammar_feedback(row["original"])
        expected = row["decision"]
        assert actual["state"] == (
            "offered" if expected["state"] == "provisional" else expected["state"]
        )
        if actual["state"] == "offered":
            assert actual["edit"] == expected["edit"]
            assert actual["explanation"] == expected["explanation"].replace(
                "means more than one", "is more than one"
            )
        else:
            assert "explanation" not in actual and "edit" not in actual
        assert actual["feedback_seconds"] >= sum(actual["stage_seconds"].values())
        generator.assert_called_once_with(row["original"], model="qwen3:4b")
        client.post.assert_called_with(
            "/v2/check", data={"language": "en-US", "text": row["original"]}
        )
    assert all(call.kwargs["trust_env"] is False for call in factory.call_args_list)


def test_conversation_uses_history_and_reply_only_schema(monkeypatch, tmp_path):
    path = tmp_path / "history.sqlite"
    db.init_db(path)
    db.insert_turn(
        "a", "My name is Maya.", "Hello Maya.", ["Do not resend feedback"], path
    )
    chat = MagicMock(
        return_value='{"reply":"Your name is Maya. Tell me about an activity you enjoy."}'
    )
    monkeypatch.setattr(llm_client, "_chat", chat)
    reply = flow.conversation_reply(
        " What is my name? ",
        level="beginner",
        scenario="introductions",
        session_id="a",
        db_path=path,
    )
    messages = chat.call_args.args[0]
    assert messages[1:] == [
        {"role": "user", "content": "My name is Maya."},
        {"role": "assistant", "content": "Hello Maya."},
        {"role": "user", "content": "What is my name?"},
    ]
    assert "do not correct" in messages[0]["content"]
    assert chat.call_args.kwargs["schema"] == flow.REPLY_SCHEMA
    assert reply.startswith("Your name is Maya.")
    assert len(db.get_history("a", db_path=path)) == 1  # Caller owns saving.


@pytest.mark.parametrize(
    "raw",
    [
        "not JSON",
        '{"reply":""}',
        '{"reply":42}',
        '{"reply":"Hi", "feedback":["invented"]}',
    ],
)
def test_invalid_conversation_output_rejected_once(monkeypatch, tmp_path, raw):
    path = tmp_path / "history.sqlite"
    db.init_db(path)
    chat = MagicMock(return_value=raw)
    monkeypatch.setattr(llm_client, "_chat", chat)
    with pytest.raises(LLMResponseError):
        flow.conversation_reply(
            "Hello",
            level="beginner",
            scenario="introductions",
            session_id="a",
            db_path=path,
        )
    chat.assert_called_once()
    assert db.get_history("a", db_path=path) == []


def test_multiline_is_unsupported_without_inference(monkeypatch):
    chat = MagicMock()
    monkeypatch.setattr(flow, "check_sentence", chat)
    result = flow.grammar_feedback("First line.\nSecond line.")
    assert result["state"] == "unsupported"
    chat.assert_not_called()


def test_changed_model_not_silently_used(transport, monkeypatch):
    client, _ = transport
    client.get.return_value.json.return_value = {
        "models": [{"name": flow.GRAMMAR_MODEL, "digest": "wrong"}]
    }
    generator = MagicMock()
    monkeypatch.setattr(flow, "check_sentence", generator)
    assert flow.grammar_feedback("I packed two bag.")["state"] == "unavailable"
    generator.assert_not_called()


@pytest.mark.parametrize(
    "failure", [LLMError("private draft"), httpx.ConnectError("private draft")]
)
def test_generation_failure_redacted(transport, monkeypatch, failure):
    monkeypatch.setattr(flow, "check_sentence", MagicMock(side_effect=failure))
    result = flow.grammar_feedback("I packed two bag.")
    assert result["state"] == "unavailable"
    assert result["failed_stage"] == "generation"
    assert "private draft" not in json.dumps(result)


def test_invalid_proposal_never_reaches_checkers(transport, monkeypatch):
    client, _ = transport
    monkeypatch.setattr(
        flow,
        "check_sentence",
        lambda *a, **kw: {"status": "rejected", "raw": "private"},
    )
    result = flow.grammar_feedback("Hello.")
    assert result["state"] == "unavailable"
    assert "private" not in json.dumps(result)
    client.post.assert_not_called()


@pytest.mark.parametrize("stage", ["builtin", "supplemental"])
def test_checker_failure_never_becomes_no_correction(transport, monkeypatch, stage):
    client, _ = transport
    monkeypatch.setattr(
        flow,
        "check_sentence",
        lambda *a, **kw: {
            "status": "valid",
            "result": {"corrected_text": "I packed two bags."},
        },
    )
    if stage == "builtin":
        client.post.side_effect = httpx.ConnectError("private")
    else:
        client.post.return_value = MagicMock()
        client.post.return_value.json.return_value = {
            "software": {"version": "6.6"},
            "matches": [],
        }
        monkeypatch.setattr(
            flow,
            "collect_count_evidence",
            MagicMock(side_effect=subprocess.TimeoutExpired("java", 90)),
        )
    result = flow.grammar_feedback("I packed two bag.")
    assert result["state"] == "unavailable"
    assert "corrected_text" not in result
    assert result["failed_stage"] == stage + "_checker"
