"""Opt-in live evaluation: five Streamlit turns with real local LLM and temporary DB."""

import argparse
import io
import json
import os
import statistics
import tempfile
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import db
from llm_client import MODEL

CASES = [
    (
        "past_tense",
        "Yesterday I go to the store.",
        "Correct go to went; explain past tense.",
    ),
    ("correct_sentence", "I enjoy hiking with my friends.", "No correction needed."),
    (
        "agreement",
        "My brother work in a bank.",
        "Correct work to works; explain he/my brother agreement.",
    ),
    (
        "correct_routine",
        "I usually hike on Saturdays.",
        "No correction needed; plural Saturdays is valid.",
    ),
    (
        "recall",
        "Where does my brother work?",
        "Recall the bank; no grammar correction needed.",
    ),
]


def run_evaluation(audio: bytes | None = None) -> dict:
    """Time Send→render; never mutate the learner's normal conversation database."""
    records = []
    with tempfile.TemporaryDirectory(prefix="speakwell-eval-") as directory:
        path = Path(directory) / "evaluation.sqlite"
        audio_widget = (
            patch(
                "streamlit.audio_input", side_effect=lambda *a, **kw: io.BytesIO(audio)
            )
            if audio is not None
            else nullcontext()
        )
        with patch.dict(os.environ, {"SPEAKWELL_DB_PATH": str(path)}), audio_widget:
            app = AppTest.from_file(
                Path(__file__).with_name("app.py"), default_timeout=90
            ).run()
            app.button(key="start").click().run()
            for case_id, text, expected in CASES:
                app.text_area(key="draft").input(text)
                start = perf_counter()
                transcription_failed = False
                if audio is not None:
                    app.button(key="transcribe").click().run()
                    transcription_failed = bool(
                        app.warning or app.error or app.exception
                    )
                    text = app.text_area(key="draft").value
                    case_id = f"audio_repeat_{len(records) + 1}"
                    expected = "Review transcription and feedback; repeated clip is a timing probe, not diverse accuracy evidence."
                if not transcription_failed:
                    app.button(key="send").click().run()
                elapsed = round(perf_counter() - start, 3)
                errors = [item.value for item in app.error]
                if transcription_failed:
                    errors.extend(item.value for item in app.warning)
                if app.exception:
                    errors.append("Unhandled Streamlit exception")
                record = {
                    "case": case_id,
                    "input": text,
                    "expected": expected,
                    "seconds": elapsed,
                    "errors": errors,
                    "feedback_rating": None,
                    "review_notes": "TODO: review output manually",
                }
                if not errors:
                    record["result"] = app.session_state.turns[-1]
                records.append(record)
                print(
                    f"{case_id}: {elapsed:.3f}s; {'FAIL' if errors else 'completed'}",
                    flush=True,
                )
            session_id = app.session_state.conversation["session_id"]
            saved = len(db.load_session(session_id, path)[1])
            app.run()
            assert len(db.load_session(session_id, path)[1]) == saved, (
                "Rerun duplicated history"
            )
    durations = [r["seconds"] for r in records if not r["errors"]]
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "model": MODEL,
        "timing_scope": (
            "Completed WAV through STT, immediate Send, LLM, SQLite and rendered reply; excludes capture/human review/TTS"
            if audio is not None
            else "Text Send through rendered reply; includes LLM and SQLite, excludes recording/STT/human review/TTS"
        ),
        "context": "Five sequential beginner/daily-activities turns; model loading state uncontrolled",
        "saved_turns": saved,
        "rerun_no_duplicate": True,
        "median_seconds": statistics.median(durations) if durations else None,
        "max_seconds": max(durations) if durations else None,
        "cases": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".tools/evaluation.json"))
    parser.add_argument(
        "--audio",
        type=Path,
        help="Optional 16kHz mono PCM16 WAV to repeat for five full processing turns",
    )
    args = parser.parse_args()
    audio = None
    if args.audio:
        with args.audio.open("rb") as recording:
            audio = recording.read(2_000_001)
    result = run_evaluation(audio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Results: {args.output}; ratings still require review.")
    return 1 if any(case["errors"] for case in result["cases"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
