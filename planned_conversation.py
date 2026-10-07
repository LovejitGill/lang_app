"""Opt-in app adapter for the bounded, measured conversation candidate."""

import asyncio

import httpx

import bounded_conversation as base
import db
import dialogue_planner
from errors import LLMError
from llm_client import HISTORY_TURNS

ENGINE = "planned_v4"


def ensure_model():
    """Fail clearly when the prepared local model is unavailable or changed."""
    try:
        with httpx.Client(trust_env=False, timeout=0.4) as client:
            response = client.get(base.HOST + "/api/tags")
            response.raise_for_status()
            models = response.json()["models"]
        if not any(
            m["name"] == base.MODEL and m["digest"] == base.MODEL_DIGEST for m in models
        ):
            raise ValueError("Prepared conversation model missing")
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise LLMError(
            "The prepared conversation model is unavailable. Check the local Ollama service and model setup."
        ) from exc


def conversation_reply(text, *, level, scenario, session_id, db_path):
    """Read completed dialogue only; saving remains the app's responsibility."""
    dialogue_planner.prepare(text, level=level, scenario=scenario)
    history = [
        {"learner_text": row["learner_text"], "tutor_reply": row["tutor_reply"]}
        for row in db.get_history(session_id, HISTORY_TURNS, db_path)
    ]
    ensure_model()
    result = asyncio.run(
        dialogue_planner.respond(text, level=level, scenario=scenario, history=history)
    )
    # Persist a small explanation of the response path, not raw model requests/history.
    return result["reply"], {
        "engine": ENGINE,
        "path": result["path"],
        "support": result["support"],
        "correction": result["correction"],
        "candidate_seconds": result["seconds"],
    }
