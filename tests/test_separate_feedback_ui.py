"""Exercise reply-first rendering while a real background thread is paused."""

import io
import json
from pathlib import Path
from threading import Event
from time import perf_counter
from unittest.mock import MagicMock

import pytest
import streamlit
from streamlit.testing.v1 import AppTest

import db
import feedback_store
import feedback_worker
import llm_client
import separate_feedback
import stt

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ui(monkeypatch, tmp_path):
    path = tmp_path / "ui.sqlite"
    monkeypatch.setenv("SPEAKWELL_DB_PATH", str(path))
    streamlit.cache_resource.clear()
    worker = feedback_worker.FeedbackWorker()
    monkeypatch.setattr(feedback_worker, "FeedbackWorker", lambda: worker)
    entered, release = Event(), Event()
    result = {
        "state": "offered",
        "edit": {"original": "seed", "replacement": "seeds"},
        "corrected_text": "They planted fifteen seeds.",
        "explanation": "‘Fifteen’ is more than one, so use the plural ‘seeds’.",
        "feedback_seconds": 0.2,
    }

    def check(text):
        entered.set()
        if not release.wait(10):
            raise TimeoutError("Test did not release worker")
        return dict(result)

    checker = MagicMock(side_effect=check)
    monkeypatch.setattr(separate_feedback, "grammar_feedback", checker)
    chat = MagicMock(
        return_value=json.dumps({"reply": "Tell me about the garden they planted."})
    )
    monkeypatch.setattr(llm_client, "_chat", chat)
    at = AppTest.from_file(APP, default_timeout=5).run()
    at.checkbox(key="separate_grammar").check().run()
    at.button(key="start").click().run()
    yield at, path, worker, entered, release, result, chat, checker
    release.set()
    worker.close()
    streamlit.cache_resource.clear()


def send(at, text="They planted fifteen seed."):
    at.text_area(key="draft").input(text)
    at.button(key="send").click().run()
    assert not at.exception


def test_reply_visible_while_grammar_waits_then_survives_refresh(ui):
    at, path, worker, entered, release, result, chat, checker = ui
    send(at)
    assert entered.wait(1)
    session = at.session_state.conversation["session_id"]
    assert any(t.value == "Tell me about the garden they planted." for t in at.text)
    assert any("Checking grammar" in c.value for c in at.caption)
    assert at.button(key="send").disabled
    assert len(db.load_session(session, path)[1]) == 1
    assert db.load_session(session, path)[1][0]["feedback"] == []
    at.run()
    chat.assert_called_once()
    checker.assert_called_once_with("They planted fifteen seed.")
    release.set()
    worker.close()
    at.run()
    assert not at.button(key="send").disabled
    assert any(t.value == result["explanation"] for t in at.text)
    assert any("Grammar processing:" in c.value for c in at.caption)
    assert any("Feedback ready after Send:" in c.value for c in at.caption)
    fresh = AppTest.from_file(APP)
    fresh.query_params["session"] = session
    fresh.run()
    assert not fresh.exception
    assert fresh.checkbox(key="separate_grammar").value
    assert any(t.value == result["explanation"] for t in fresh.text)
    chat.assert_called_once()
    checker.assert_called_once()


def test_checker_unavailable_does_not_remove_reply(ui):
    at, path, worker, entered, release, result, _chat, _checker = ui
    result.clear()
    result.update(state="unavailable", message="Grammar service unavailable.")
    send(at)
    assert entered.wait(1)
    release.set()
    worker.close()
    at.run()
    assert any("Grammar service unavailable" in w.value for w in at.warning)
    assert any("Tell me about the garden" in t.value for t in at.text)
    assert not at.button(key="send").disabled
    assert db.load_session(at.session_state.conversation["session_id"], path)[1][0][
        "saved"
    ]


def test_unsaved_reply_does_not_start_unattached_grammar(ui, monkeypatch):
    at, path, _worker, _entered, _release, _result, _chat, checker = ui
    monkeypatch.setattr(
        feedback_store, "save_reply", MagicMock(side_effect=db.StorageError("locked"))
    )
    send(at)
    checker.assert_not_called()
    assert any("Not saved" in w.value for w in at.warning)
    assert any("Tell me about the garden" in t.value for t in at.text)
    assert not db.load_session(at.session_state.conversation["session_id"], path)[1]


def test_new_conversation_cannot_receive_old_job_result(ui):
    at, path, worker, entered, release, _result, chat, _checker = ui
    send(at)
    assert entered.wait(1)
    old = at.session_state.conversation["session_id"]
    at.button(key="new").click().run()
    at.button(key="start").click().run()
    new = at.session_state.conversation["session_id"]
    release.set()
    worker.close()
    at.run()
    assert not at.exception
    assert not at.chat_message
    assert db.load_session(new, path)[1] == []
    assert db.load_session(old, path)[1][0]["feedback"]
    chat.assert_called_once()


def test_confirmed_transcript_not_raw_transcription_is_checked(ui, monkeypatch):
    at, _path, _worker, entered, _release, _result, chat, checker = ui
    monkeypatch.setattr(streamlit, "audio_input", lambda *a, **kw: io.BytesIO(b"wav"))
    monkeypatch.setattr(
        stt, "transcribe_audio", lambda _: "They planted fifteen seeds."
    )
    at.run()
    at.button(key="transcribe").click().run()
    chat.assert_not_called()
    checker.assert_not_called()
    send(at, "They planted fifteen seed.")
    assert entered.wait(1)
    checker.assert_called_once_with("They planted fifteen seed.")
    assert chat.call_args.args[0][-1]["content"] == "They planted fifteen seed."


def test_interrupted_job_after_restart_is_not_retried(ui):
    at, path, _worker, _entered, _release, _result, chat, checker = ui
    session = at.session_state.conversation["session_id"]
    job = feedback_store.save_reply(
        session, "Hello.", "Tell me about your day.", 0.2, perf_counter(), path
    )
    feedback_store.claim(job)
    fresh = AppTest.from_file(APP)
    fresh.query_params["session"] = session
    fresh.run()
    assert not fresh.exception
    assert any("interrupted" in w.value for w in fresh.warning)
    assert any(t.value == "Tell me about your day." for t in fresh.text)
    assert not fresh.button(key="send").disabled
    chat.assert_not_called()
    checker.assert_not_called()
