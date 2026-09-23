"""Local text generation and structured tutoring with optional SQLite memory."""

import argparse
import json
import sys
import warnings
from pathlib import Path

import httpx
from ollama import Client, ResponseError

import db
from errors import LLMError, LLMResponseError, TutorUnavailable
from prompts import LEVELS, SCENARIOS, build_system_prompt

MODEL = "qwen3:1.7b"
HOST = "http://127.0.0.1:11434"
HISTORY_TURNS = 4
HISTORY_CHAR_BUDGET = 3000
MAX_LEARNER_CHARS = 1000

# The runner constrains generation; our parser still validates the returned data.
TUTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string", "minLength": 1, "maxLength": 300},
        "feedback": {
            "type": "array",
            "maxItems": 2,
            "items": {"type": "string", "minLength": 1, "maxLength": 240},
        },
    },
    "required": ["reply", "feedback"],
    "additionalProperties": False,
}


class HistorySaveWarning(UserWarning):
    """A generated reply is available, but it was not persisted."""


def _history_messages(turns: list[dict]) -> list[dict[str, str]]:
    """Keep the newest complete pairs within a character budget, in time order."""
    selected = []
    used = 0
    for turn in reversed(turns):
        size = len(turn["learner_text"]) + len(turn["tutor_reply"])
        if used + size > HISTORY_CHAR_BUDGET:
            break
        selected.append(turn)
        used += size
    messages = []
    for turn in reversed(selected):
        messages.extend(
            [
                {"role": "user", "content": turn["learner_text"]},
                {"role": "assistant", "content": turn["tutor_reply"]},
            ]
        )
    return messages


def ask_llm(prompt: str) -> str:
    """Return a reply; raise ValueError for bad input or LLMError for service failure."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Enter a non-empty text prompt.")
    return _chat([{"role": "user", "content": prompt.strip()}])


def _chat(messages: list[dict[str, str]], *, structured: bool = False) -> str:
    """Share transport/error handling while preserving the Milestone 1 function."""
    output_settings = {"format": TUTOR_SCHEMA} if structured else {}
    options = {"num_predict": 256 if structured else 128, "num_ctx": 4096}
    if structured:
        options["temperature"] = (
            0.2  # Reduce variation; this does not ensure correctness.
        )

    try:
        # Explicit localhost prevents an environment variable selecting a remote host.
        # This timeout allows CPU model loading; it is not a response-speed target.
        with Client(
            host=HOST, timeout=httpx.Timeout(30.0, connect=3.0), trust_env=False
        ) as client:
            response = client.chat(
                model=MODEL,
                messages=messages,
                think=False,  # Request an answer without the model's thinking output.
                stream=False,  # Learn the complete-response path before streaming.
                options=options,
                **output_settings,
            )
    except (ConnectionError, httpx.ConnectError) as exc:
        raise TutorUnavailable(
            "Cannot reach Ollama. Start it with: bash scripts/ollama.sh serve"
        ) from exc
    except httpx.TimeoutException as exc:
        raise LLMError(
            "Ollama timed out. Wait for model loading, then try again."
        ) from exc
    except ResponseError as exc:
        if exc.status_code == 404:
            raise LLMError(
                f"Model unavailable. Download it with: bash scripts/ollama.sh pull {MODEL}"
            ) from exc
        raise LLMError(f"Ollama returned an error (HTTP {exc.status_code}).") from exc
    except httpx.RequestError as exc:
        raise LLMError(
            "The connection to Ollama failed. Check the server and retry."
        ) from exc

    # Return generated text only, never turn an error message into a tutor reply.
    reply = (response.message.content or "").strip()
    if not reply:
        if structured:
            raise LLMResponseError("Ollama returned empty tutoring output.")
        raise LLMError("Ollama returned no reply. Try again with a short prompt.")
    return reply


def parse_tutor_response(raw: str) -> dict[str, str | list[str]]:
    """Parse JSON and validate types, keys, and bounds; do not regex-extract it."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise LLMResponseError("Tutor output was not valid JSON.") from exc
    if not isinstance(data, dict) or set(data) != {"reply", "feedback"}:
        raise LLMResponseError("Tutor output must contain only reply and feedback.")
    reply, feedback = data["reply"], data["feedback"]
    if not isinstance(reply, str) or not reply.strip() or len(reply) > 300:
        raise LLMResponseError(
            "Tutor reply must be non-empty text under 301 characters."
        )
    if not isinstance(feedback, list) or len(feedback) > 2:
        raise LLMResponseError("Tutor feedback must be a list of at most two points.")
    if any(not isinstance(p, str) or not p.strip() or len(p) > 240 for p in feedback):
        raise LLMResponseError("Each feedback point must be brief, non-empty text.")
    return {"reply": reply.strip(), "feedback": [p.strip() for p in feedback]}


def ask_tutor(
    learner_text: str,
    *,
    level: str = "beginner",
    scenario: str = "daily activities",
    session_id: str | None = None,
    db_path: Path = db.DEFAULT_DB_PATH,
) -> dict[str, str | list[str]]:
    """Return tutoring data; load/save recent turns only when a session ID is given."""
    if not isinstance(learner_text, str) or not learner_text.strip():
        raise ValueError("Enter a non-empty text prompt.")
    if len(learner_text) > MAX_LEARNER_CHARS:
        raise ValueError(
            f"Keep a learner turn to {MAX_LEARNER_CHARS} characters or fewer."
        )
    system_prompt = build_system_prompt(level, scenario)
    history = []
    if session_id is not None:
        db.validate_session_id(session_id)
        db.init_db(db_path)
        history = _history_messages(db.get_history(session_id, HISTORY_TURNS, db_path))
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": learner_text.strip()},
    ]
    for attempt in range(2):
        try:
            result = parse_tutor_response(_chat(messages, structured=True))
            break
        except LLMResponseError as exc:
            if attempt == 1:
                raise LLMResponseError(
                    "Tutor output was invalid twice. Please try again."
                ) from exc
            # Retry format failures once, without treating invalid output as history.
            messages[0]["content"] = system_prompt + (
                '\nReturn ONLY {"reply": "brief text", "feedback": []}, '
                "adding up to two short corrections to feedback only when needed."
            )
    # No database connection/transaction is held open while the model generates.
    if session_id is not None:
        try:
            db.insert_turn(
                session_id,
                learner_text.strip(),
                result["reply"],
                result["feedback"],
                db_path,
            )
        except db.StorageError:
            warnings.warn(
                "Reply generated but NOT saved. Check database access/locks; this turn will not be remembered.",
                HistorySaveWarning,
                stacklevel=2,
            )
    return result


def main() -> int:
    """Provide a terminal checkpoint without adding an application interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", default="Say hello in one short sentence.")
    parser.add_argument("--tutor", action="store_true", help="Return tutoring JSON")
    parser.add_argument("--level", choices=LEVELS, default="beginner")
    parser.add_argument("--scenario", choices=SCENARIOS, default="daily activities")
    parser.add_argument("--session", help="Save/reload tutoring history under this ID")
    parser.add_argument(
        "--db", type=Path, default=db.DEFAULT_DB_PATH, help="SQLite history path"
    )
    args = parser.parse_args()
    if args.session is not None and not args.tutor:
        parser.error("--session requires --tutor")
    try:
        if args.tutor:
            with warnings.catch_warnings(record=True) as notices:
                warnings.simplefilter("always", HistorySaveWarning)
                result = ask_tutor(
                    args.prompt,
                    level=args.level,
                    scenario=args.scenario,
                    session_id=args.session,
                    db_path=args.db,
                )
            for notice in notices:
                print(f"History warning: {notice.message}", file=sys.stderr)
        else:
            result = ask_llm(args.prompt)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except LLMError as exc:
        print(f"LLM error: {exc}", file=sys.stderr)
        return 1
    except db.StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(result, indent=2, ensure_ascii=False)
        if args.tutor
        else f"Tutor: {result}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
