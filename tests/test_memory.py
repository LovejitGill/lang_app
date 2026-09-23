"""Real temporary SQLite databases plus a fake LLM for deterministic checks."""

import json
import sqlite3
from unittest.mock import MagicMock

import pytest

import db
import llm_client


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "history.sqlite"
    db.init_db(path)
    return path


def test_history_survives_reinitialization_and_is_isolated(database):
    for i in range(6):
        db.insert_turn("a", f"Learner {i}", f"Tutor {i}", ["A note"], database)
    db.insert_turn("b", "Other learner", "Other reply", [], database)
    db.init_db(database)
    rows = db.get_history("a", 3, database)
    assert [r["learner_text"] for r in rows] == ["Learner 3", "Learner 4", "Learner 5"]
    assert rows[0]["feedback"] == ["A note"]
    assert len(db.get_history("b", 4, database)) == 1
    assert db.get_history("missing", 4, database) == []


def test_sql_like_input_is_saved_as_data(database):
    session = "x'; DROP TABLE turns; --"
    db.insert_turn(session, "I'm here.", "Welcome!", ["Café"], database)
    assert db.get_history(session, 4, database)[0]["feedback"] == ["Café"]
    assert db.get_history("x", 4, database) == []


@pytest.mark.parametrize("limit", [0, -1, 21, True, "4"])
def test_invalid_history_limit(database, limit):
    with pytest.raises(ValueError):
        db.get_history("a", limit, database)


def test_bad_database_path_is_reported(tmp_path):
    with pytest.raises(db.StorageError, match="initialize"):
        db.init_db(tmp_path)  # A directory cannot be opened as a database file.


def test_two_calls_send_prior_turn_and_save_only_once(database, monkeypatch):
    captured = []

    def fake_chat(messages, **kwargs):
        captured.append([dict(m) for m in messages])
        return json.dumps({"reply": "You enjoy hiking.", "feedback": []})

    monkeypatch.setattr(llm_client, "_chat", fake_chat)
    llm_client.ask_tutor("I enjoy hiking.", session_id="demo", db_path=database)
    llm_client.ask_tutor("What do I enjoy?", session_id="demo", db_path=database)
    assert captured[1][1:] == [
        {"role": "user", "content": "I enjoy hiking."},
        {"role": "assistant", "content": "You enjoy hiking."},
        {"role": "user", "content": "What do I enjoy?"},
    ]
    assert len(db.get_history("demo", 4, database)) == 2
    llm_client.ask_tutor("Hello", session_id="other", db_path=database)
    assert len(captured[2]) == 2  # Only the system and current user message.


def test_history_budget_keeps_newest_complete_pairs(monkeypatch):
    monkeypatch.setattr(llm_client, "HISTORY_CHAR_BUDGET", 8)
    turns = [{"learner_text": str(i) * 2, "tutor_reply": "ok"} for i in range(4)]
    messages = llm_client._history_messages(turns)
    assert [m["content"] for m in messages] == ["22", "ok", "33", "ok"]


@pytest.mark.parametrize(
    "failure", [llm_client.LLMError("offline"), llm_client.LLMResponseError("bad JSON")]
)
def test_failed_generation_does_not_save_turn(database, monkeypatch, failure):
    monkeypatch.setattr(llm_client, "_chat", MagicMock(side_effect=failure))
    with pytest.raises(llm_client.LLMError):
        llm_client.ask_tutor("Hello", session_id="demo", db_path=database)
    assert db.get_history("demo", 4, database) == []


def test_format_retry_saves_one_turn(database, monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "_chat",
        MagicMock(side_effect=["bad", '{"reply":"Hi!","feedback":[]}']),
    )
    llm_client.ask_tutor("Hello", session_id="demo", db_path=database)
    assert len(db.get_history("demo", 4, database)) == 1


def test_write_failure_preserves_reply_and_warns(database, monkeypatch):
    monkeypatch.setattr(
        llm_client, "_chat", lambda *a, **k: '{"reply":"Hi!","feedback":[]}'
    )
    monkeypatch.setattr(
        db, "insert_turn", MagicMock(side_effect=db.StorageError("locked"))
    )
    with pytest.warns(llm_client.HistorySaveWarning, match="NOT saved"):
        result = llm_client.ask_tutor("Hi", session_id="demo", db_path=database)
    assert result["reply"] == "Hi!"
    assert db.get_history("demo", 4, database) == []


def test_real_sqlite_write_lock_is_reported(database):
    connection = sqlite3.connect(database)
    try:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(db.StorageError, match="save"):
            db.insert_turn("demo", "Hello", "Hi", [], database)
    finally:
        connection.rollback()
        connection.close()
    assert db.get_history("demo", 4, database) == []


def test_no_session_means_no_database(monkeypatch, tmp_path):
    path = tmp_path / "unused.sqlite"
    monkeypatch.setattr(
        llm_client, "_chat", lambda *a, **k: '{"reply":"Hi!","feedback":[]}'
    )
    llm_client.ask_tutor("Hi", db_path=path)
    assert not path.exists()


def test_oversized_input_is_rejected_before_storage(monkeypatch, tmp_path):
    path = tmp_path / "unused.sqlite"
    with pytest.raises(ValueError, match="1000"):
        llm_client.ask_tutor("x" * 1001, session_id="demo", db_path=path)
    assert not path.exists()
