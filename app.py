"""Text and recorded-turn practice UI. Run with Streamlit, not plain Python."""

import os
import uuid
import warnings
from pathlib import Path

import streamlit as st

import db
from errors import user_message
from llm_client import MAX_LEARNER_CHARS, HistorySaveWarning, LLMError, ask_tutor
from prompts import LEVELS, SCENARIOS, get_opening_prompt
from stt import TranscriptionError, transcribe_audio

DB_PATH = Path(os.environ.get("SPEAKWELL_DB_PATH", str(db.DEFAULT_DB_PATH)))


def restore_page():
    """Hydrate once per browser session, not on every form/widget rerun."""
    if "conversation" in st.session_state:
        return
    st.session_state.conversation = None
    st.session_state.turns = []
    st.session_state.turn_number = 1
    st.session_state.load_error = None
    session_id = st.query_params.get("session")
    if session_id:
        try:
            uuid.UUID(session_id)
            db.init_db(DB_PATH)
            session, turns = db.load_session(session_id, DB_PATH)
            if session["level"] not in LEVELS or session["scenario"] not in SCENARIOS:
                raise ValueError("Unknown saved practice settings.")
            st.session_state.conversation = session
            st.session_state.turns = turns
            st.session_state.turn_number = len(turns) + 1
        except (ValueError, db.StorageError) as exc:
            st.session_state.load_error = str(exc)


def new_conversation():
    # Leave saved rows intact. Clearing the screen is not a deletion operation.
    st.query_params.clear()
    for key in (
        "conversation",
        "turns",
        "turn_number",
        "load_error",
        "draft",
        "clear_draft",
        "recording_version",
        "transcription_ready",
    ):
        st.session_state.pop(key, None)
    st.rerun()


def main():
    st.set_page_config(page_title="SpeakWell · English practice", page_icon="💬")
    restore_page()
    if st.session_state.pop("clear_draft", False):
        st.session_state.draft = ""
    st.title("SpeakWell")
    st.caption("Practice English by typing or recording a short message.")
    st.info(
        "Experimental tutor: grammar and vocabulary feedback can be inaccurate. Speech transcription does not assess pronunciation."
    )

    session = st.session_state.conversation
    with st.sidebar:
        st.header("Practice settings")
        level = st.selectbox(
            "Level",
            list(LEVELS),
            index=list(LEVELS).index(session["level"]) if session else 0,
            disabled=bool(session),
        )
        scenario = st.selectbox(
            "Scenario",
            list(SCENARIOS),
            index=list(SCENARIOS).index(session["scenario"]) if session else 0,
            disabled=bool(session),
        )
        st.caption(
            "Settings stay fixed during a conversation. Start a new one to change them."
        )
        if session:
            st.caption(f"Conversation: {session['session_id']}")
            if st.button("New conversation", key="new"):
                new_conversation()
        st.caption(
            "Text is saved locally in SQLite. New conversation does not delete history. Keep session URLs private; this local demo has no accounts."
        )

    if st.session_state.load_error:
        st.error(f"Could not restore history: {st.session_state.load_error}")
        if st.button("Start over", key="reset"):
            new_conversation()
        st.stop()

    if not session:
        st.write("Choose your practice settings, then start a conversation.")
        if st.button("Start conversation", key="start"):
            session_id = str(uuid.uuid4())
            try:
                db.init_db(DB_PATH)
                db.create_session(session_id, level, scenario, DB_PATH)
            except db.StorageError as exc:
                st.error(user_message(exc))
            else:
                st.session_state.conversation = {
                    "session_id": session_id,
                    "level": level,
                    "scenario": scenario,
                }
                st.query_params["session"] = session_id
                st.rerun()
        st.stop()

    st.subheader("Conversation")
    if not st.session_state.turns:
        st.markdown("**Start with this practice prompt**")
        st.info(get_opening_prompt(session["level"], session["scenario"]))
        st.caption(
            "Try two short sentences to begin. Share only details you are comfortable sharing."
        )
    for number, turn in enumerate(st.session_state.turns, 1):
        st.caption(f"Turn {number}")
        with st.chat_message("user"):
            st.text(turn["learner_text"])
        with st.chat_message("assistant"):
            st.text(turn["tutor_reply"])
            st.markdown("**Language feedback**")
            if turn["feedback"]:
                for point in turn["feedback"]:
                    st.text(f"• {point}")
            else:
                st.caption(
                    "No corrections suggested. This is not a guarantee of correctness."
                )
            if not turn["saved"]:
                st.warning(
                    "Not saved. This reply will disappear on refresh and will not be remembered by the tutor."
                )

    st.subheader(f"Turn #{st.session_state.turn_number}")
    with st.expander("Record a voice message"):
        st.caption(
            "Record 0.3–60 seconds, then stop and transcribe. Review the text before Send. "
            "Transcribing replaces the current draft. Audio is not saved to disk by this app; "
            "the recording stays in the widget until transcription succeeds or you clear it."
        )
        version = st.session_state.get("recording_version", 0)
        recording = st.audio_input(
            "Record your message", sample_rate=16000, key=f"recording_{version}"
        )
        if st.button(
            "Transcribe recording", key="transcribe", disabled=recording is None
        ):
            try:
                with st.spinner("Transcribing locally…"):
                    transcript = transcribe_audio(recording.getvalue())
                if len(transcript) > MAX_LEARNER_CHARS:
                    raise TranscriptionError(
                        "Transcript is too long. Record a shorter message."
                    )
            except TranscriptionError as exc:
                st.warning(user_message(exc))
            else:
                st.session_state.draft = transcript
                st.session_state.recording_version = version + 1
                st.session_state.transcription_ready = True
                st.rerun()
    if st.session_state.pop("transcription_ready", False):
        st.success("Transcript ready below. Review or edit it, then press Send.")
    with st.form("learner_turn", clear_on_submit=False):
        text = st.text_area(
            "Your message",
            key="draft",
            max_chars=MAX_LEARNER_CHARS,
            placeholder="Tell the tutor about your day.",
        )
        submitted = st.form_submit_button("Send", key="send")
    if submitted:
        if not text.strip():
            st.error("Enter a message before sending.")
            return
        try:
            with (
                st.spinner("The tutor is responding…"),
                warnings.catch_warnings(record=True) as notices,
            ):
                warnings.simplefilter("always", HistorySaveWarning)
                result = ask_tutor(
                    text,
                    level=session["level"],
                    scenario=session["scenario"],
                    session_id=session["session_id"],
                    db_path=DB_PATH,
                )
        except (ValueError, LLMError, db.StorageError) as exc:
            st.error(user_message(exc))
            st.caption(
                "Your message is still in the box. Fix the issue, then press Send to retry."
            )
            return
        saved = not any(issubclass(n.category, HistorySaveWarning) for n in notices)
        st.session_state.turns.append(
            {
                "learner_text": text.strip(),
                "tutor_reply": result["reply"],
                "feedback": result["feedback"],
                "saved": saved,
            }
        )
        st.session_state.turn_number += 1
        st.session_state.clear_draft = True
        st.rerun()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 -- final UI safety boundary
        # Streamlit's rerun/stop signals inherit BaseException and pass through.
        # Do not expose arbitrary exception messages or learner text in the UI.
        st.error(user_message(RuntimeError()))
        st.caption(
            f"Diagnostic type: {type(exc).__name__}. Report this with the failed action."
        )
