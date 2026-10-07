"""Real SQLite checks for exact-turn attachment, duplicate work, and persistence."""

from time import perf_counter
from unittest.mock import MagicMock

import pytest

import db
import feedback_store as store


@pytest.fixture
def saved(tmp_path):
    path = tmp_path / "feedback.sqlite"
    db.init_db(path)
    db.create_session("a", "beginner", "introductions", path)
    job = store.save_reply(
        "a",
        "I packed two bag.",
        "Where are you going?",
        0.2,
        perf_counter() - 0.2,
        path,
    )
    return path, job


def offered():
    return {
        "state": "offered",
        "edit": {"original": "bag", "replacement": "bags"},
        "explanation": "Two is more than one.",
        "corrected_text": "I packed two bags.",
        "feedback_seconds": 0.1,
    }


def test_reply_saved_before_feedback_and_survives_reload(saved):
    path, job = saved
    assert db.load_session("a", path)[1][0]["tutor_reply"] == "Where are you going?"
    assert store.load("a", path)[job["turn_id"]]["state"] == "pending"
    check = MagicMock(return_value=offered())
    store.run_job(job, check)
    loaded = store.load("a", path)[job["turn_id"]]
    assert loaded["state"] == "offered"
    assert loaded["result"]["total_seconds"] >= 0.2
    assert "bag → bags" in db.load_session("a", path)[1][0]["feedback"][0]
    store.run_job(job, check)
    check.assert_called_once_with("I packed two bag.")


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", "b"),
        ("learner_text", "Different text."),
        ("turn_id", 999),
        ("job_id", "wrong"),
    ],
)
def test_mismatched_identity_rejected(saved, field, value):
    path, job = saved
    wrong = {**job, field: value}
    assert not store.claim(wrong)
    assert not store.finish(wrong, offered())
    assert store.load("a", path)[job["turn_id"]]["state"] == "pending"


def test_late_result_does_not_attach_to_newest_turn(saved):
    path, first = saved
    second = store.save_reply(
        "a", "I enjoy hiking.", "Tell me about a hike.", 0.1, perf_counter(), path
    )
    other = store.save_reply(
        "b", "I packed two bag.", "A different session.", 0.1, perf_counter(), path
    )
    store.run_job(first, lambda _: offered())
    assert store.load("a", path)[first["turn_id"]]["state"] == "offered"
    assert store.load("a", path)[second["turn_id"]]["state"] == "pending"
    assert store.load("b", path)[other["turn_id"]]["state"] == "pending"
    assert len(db.load_session("a", path)[1]) == 2


def test_unexpected_failure_keeps_reply_and_hides_private_message(saved):
    path, job = saved
    store.run_job(job, MagicMock(side_effect=RuntimeError("private learner content")))
    result = store.load("a", path)[job["turn_id"]]["result"]
    assert result["state"] == "unavailable"
    assert "private learner" not in str(result)
    assert db.load_session("a", path)[1][0]["tutor_reply"] == "Where are you going?"


def test_interrupted_job_not_silently_replayed(saved):
    path, job = saved
    assert store.claim(job)
    store.finish(job, store.unavailable("Interrupted."))
    check = MagicMock()
    store.run_job(job, check)
    check.assert_not_called()
    assert not store.finish(job, offered())
    assert store.load("a", path)[job["turn_id"]]["state"] == "unavailable"
