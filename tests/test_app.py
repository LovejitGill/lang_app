"""Simulate Streamlit reruns with a fake model and real temporary SQLite storage."""

import io
import json
import uuid
import wave
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import streamlit
from streamlit.testing.v1 import AppTest

import db
import llm_client
import stt
from errors import LLMResponseError, TutorUnavailable

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ui(monkeypatch, tmp_path):
    path = tmp_path / "ui.sqlite"
    monkeypatch.setenv("SPEAKWELL_DB_PATH", str(path))
    chat = MagicMock(
        return_value=json.dumps({"reply": "Tell me more.", "feedback": []})
    )
    monkeypatch.setattr(llm_client, "_chat", chat)
    return AppTest.from_file(APP, default_timeout=10).run(), path, chat


def start(at):
    at.button(key="start").click().run()
    assert not at.exception


def send(at, text):
    at.text_area(key="draft").input(text)
    at.button(key="send").click().run()
    assert not at.exception


def test_three_turns_rerun_and_refresh(ui):
    at, path, chat = ui
    at.selectbox[0].select("intermediate").run()
    start(at)
    for i in range(3):
        send(at, f"Message {i}")
    assert at.session_state.turn_number == 4
    assert len(at.chat_message) == 6
    assert [t["learner_text"] for t in at.session_state.turns] == [
        f"Message {i}" for i in range(3)
    ]
    at.run()  # A display rerun must not generate/save another reply.
    assert chat.call_count == 3
    session_id = at.query_params["session"][0]
    session, rows = db.load_session(session_id, path)
    assert len(rows) == 3
    fresh = AppTest.from_file(APP)
    fresh.query_params["session"] = session_id
    fresh.run()
    assert not fresh.exception
    assert fresh.session_state.turn_number == 4
    assert len(fresh.chat_message) == 6
    assert session["level"] == fresh.selectbox[0].value == "intermediate"
    assert chat.call_count == 3


def test_blank_and_failed_turn_keep_counter_and_draft(ui):
    at, _path, chat = ui
    start(at)
    send(at, "   ")
    assert at.error[0].value == "Enter a message before sending."
    chat.assert_not_called()
    chat.side_effect = llm_client.LLMError("Cannot reach Ollama")
    send(at, "Hello")
    assert "Cannot reach" in at.error[0].value
    assert at.text_area[0].value == "Hello"
    assert at.session_state.turn_number == 1
    assert not at.chat_message


def test_unsaved_reply_stays_visible(ui, monkeypatch):
    at, _path, chat = ui
    start(at)
    monkeypatch.setattr(
        db, "insert_turn", MagicMock(side_effect=db.StorageError("locked"))
    )
    send(at, "Hello")
    assert len(at.chat_message) == 2
    assert "Not saved" in at.warning[0].value
    at.run()
    assert "Not saved" in at.warning[0].value
    assert chat.call_count == 1


def test_new_conversation_keeps_old_rows_and_clears_display(ui):
    at, path, _chat = ui
    start(at)
    send(at, "First conversation")
    old_id = at.session_state.conversation["session_id"]
    at.button(key="new").click().run()
    assert at.session_state.turn_number == 1
    assert not at.chat_message
    assert len(db.load_session(old_id, path)[1]) == 1
    start(at)
    assert at.session_state.conversation["session_id"] != old_id


def test_missing_session_has_recovery(ui):
    _at, _path, _chat = ui
    fresh = AppTest.from_file(APP)
    fresh.query_params["session"] = str(uuid.uuid4())
    fresh.run()
    assert not fresh.exception
    assert "not found" in fresh.error[0].value
    fresh.button(key="reset").click().run()
    assert fresh.button(key="start")


def test_database_error_is_visible_at_start(ui, monkeypatch):
    at, _path, chat = ui
    monkeypatch.setattr(
        db,
        "init_db",
        MagicMock(side_effect=db.StorageError("Cannot initialize history")),
    )
    at.button(key="start").click().run()
    assert not at.exception
    assert "Cannot initialize" in at.error[0].value
    chat.assert_not_called()


def test_opening_prompt_needs_no_model_call_or_saved_turn(ui):
    at, path, chat = ui
    at.selectbox[1].select("ordering food").run()
    start(at)
    assert any("ordering lunch" in item.value for item in at.info)
    chat.assert_not_called()
    session_id = at.session_state.conversation["session_id"]
    assert db.load_session(session_id, path)[1] == []
    assert at.session_state.turn_number == 1


def test_transcript_review_then_send_uses_existing_pipeline(ui, monkeypatch):
    at, path, chat = ui
    # AppTest cannot operate a microphone: substitute only the widget return.
    monkeypatch.setattr(streamlit, "audio_input", lambda *a, **kw: io.BytesIO(b"wav"))
    transcribe = MagicMock(return_value="I enjoy hiking.")
    monkeypatch.setattr(stt, "transcribe_audio", transcribe)
    start(at)
    at.button(key="transcribe").click().run()
    assert not at.exception
    assert at.text_area(key="draft").value == "I enjoy hiking."
    chat.assert_not_called()
    assert not db.load_session(at.session_state.conversation["session_id"], path)[1]
    at.run()
    transcribe.assert_called_once_with(b"wav")
    send(at, "I enjoy hiking with friends.")
    chat.assert_called_once()
    assert at.session_state.turns[0]["learner_text"] == "I enjoy hiking with friends."
    assert at.session_state.turn_number == 2


def test_transcription_failure_preserves_draft_and_history(ui, monkeypatch):
    at, path, chat = ui
    monkeypatch.setattr(streamlit, "audio_input", lambda *a, **kw: io.BytesIO(b"wav"))
    monkeypatch.setattr(
        stt,
        "transcribe_audio",
        MagicMock(side_effect=stt.TranscriptionError("I didn't catch speech.")),
    )
    start(at)
    at.text_area(key="draft").input("Keep this draft").run()
    at.button(key="transcribe").click().run()
    assert not at.exception
    assert "didn't catch" in at.warning[0].value
    assert at.text_area(key="draft").value == "Keep this draft"
    chat.assert_not_called()
    assert not db.load_session(at.session_state.conversation["session_id"], path)[1]


@pytest.mark.parametrize(
    "failure, code",
    [
        (TutorUnavailable("Start Ollama"), "TUTOR_UNAVAILABLE"),
        (LLMResponseError("Bad model JSON"), "TUTOR_INVALID_RESPONSE"),
        (RuntimeError("private content must not appear"), "UNEXPECTED_ERROR"),
    ],
)
def test_failed_send_is_safe_and_retry_saves_once(ui, failure, code):
    at, path, chat = ui
    start(at)
    chat.side_effect = failure
    send(at, "I enjoy hiking.")
    assert code in at.error[0].value
    assert "private content" not in at.error[0].value
    assert at.text_area(key="draft").value == "I enjoy hiking."
    assert at.session_state.turn_number == 1
    session_id = at.session_state.conversation["session_id"]
    assert not db.load_session(session_id, path)[1]
    chat.side_effect = None
    at.button(key="send").click().run()
    assert not at.exception
    assert len(db.load_session(session_id, path)[1]) == 1
    assert at.session_state.turn_number == 2


def test_real_silence_validation_never_calls_tutor(ui, monkeypatch):
    at, path, chat = ui
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\0\0" * 16000)
    monkeypatch.setattr(
        streamlit, "audio_input", lambda *a, **kw: io.BytesIO(buffer.getvalue())
    )
    start(at)
    at.button(key="transcribe").click().run()
    assert not at.exception
    assert "RECORDING_ERROR" in at.warning[0].value
    assert "didn't catch" in at.warning[0].value
    chat.assert_not_called()
    assert not db.load_session(at.session_state.conversation["session_id"], path)[1]


def test_oversized_transcript_keeps_existing_draft(ui, monkeypatch):
    at, _path, chat = ui
    monkeypatch.setattr(streamlit, "audio_input", lambda *a, **kw: io.BytesIO(b"wav"))
    monkeypatch.setattr(stt, "transcribe_audio", lambda _: "x" * 1001)
    start(at)
    at.text_area(key="draft").input("Keep this draft").run()
    at.button(key="transcribe").click().run()
    assert not at.exception
    assert "too long" in at.warning[0].value
    assert at.text_area(key="draft").value == "Keep this draft"
    chat.assert_not_called()
