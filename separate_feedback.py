"""Conversation-only generation and the reviewed, separately timed grammar pass."""

import json
import subprocess
from time import perf_counter

import httpx

import conversation_prompts
import db
import llm_client
from conversation_prompts import build_conversation_prompt
from errors import LLMError, LLMResponseError
from grammar_gap_detector import collect_count_evidence, explain_with_gaps
from sentence_grammar import check_sentence

GRAMMAR_MODEL = "qwen3:4b"
GRAMMAR_DIGEST = "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7"
CHECKER_HOST = "http://127.0.0.1:8081"
REPLY_SCHEMA = {
    "type": "object",
    "properties": {"reply": {"type": "string", "minLength": 1, "maxLength": 300}},
    "required": ["reply"],
    "additionalProperties": False,
}


STRUCTURED_REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "maxLength": 200},
        "follow_up": {"type": "string", "maxLength": 200},
    },
    "required": ["answer", "follow_up"],
    "additionalProperties": False,
}


def conversation_schema(prompt_variant=None):
    variant = prompt_variant or conversation_prompts.DEFAULT_VARIANT
    return STRUCTURED_REPLY_SCHEMA if variant == "structured-v4" else REPLY_SCHEMA


def conversation_messages(text, *, level, scenario, history, prompt_variant=None):
    """Build identical messages for the app and controlled prompt comparisons."""
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError("Enter 1–1000 characters of learner text.")
    return [
        {
            "role": "system",
            "content": build_conversation_prompt(level, scenario, prompt_variant),
        },
        *llm_client._history_messages(history),
        {"role": "user", "content": text.strip()},
    ]


def parse_conversation_reply(raw, prompt_variant=None):
    """Validate one reply; this proves format, not conversation quality."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise LLMResponseError("The conversational reply was not valid JSON.") from exc
    schema = conversation_schema(prompt_variant)
    keys = schema["required"]
    if not isinstance(value, dict) or set(value) != set(keys):
        raise LLMResponseError("The conversational reply had an invalid format.")
    if any(
        not isinstance(value[k], str)
        or len(value[k]) > schema["properties"][k]["maxLength"]
        for k in keys
    ):
        raise LLMResponseError("The conversational reply had an invalid format.")
    # Required fields make the two jobs explicit without a second model call.
    reply = " ".join(value[k].strip() for k in keys if value[k].strip())
    if not reply or len(reply) > 300:
        raise LLMResponseError("The conversational reply had an invalid format.")
    return reply


def conversation_reply(
    text, *, level, scenario, session_id, db_path, prompt_variant=None
):
    """Load context and generate only a reply; the caller owns persistence."""
    # Validate text/settings before touching history, then insert only complete turns.
    messages = conversation_messages(
        text,
        level=level,
        scenario=scenario,
        history=[],
        prompt_variant=prompt_variant,
    )
    history = db.get_history(session_id, llm_client.HISTORY_TURNS, db_path)
    messages[1:1] = llm_client._history_messages(history)
    return parse_conversation_reply(
        llm_client._chat(messages, schema=conversation_schema(prompt_variant)),
        prompt_variant,
    )


def grammar_feedback(text):
    """Use the reviewed detector; never show raw model explanations or guesses."""
    start = perf_counter()
    stages = {}
    stage = "input"
    result = {"state": "unavailable", "message": "Grammar feedback is unavailable."}
    try:
        if not isinstance(text, str) or not text.strip() or len(text) > 1000:
            raise ValueError("Invalid input")
        if "\n" in text or "\r" in text:
            result = {
                "state": "unsupported",
                "message": "Separate grammar feedback currently supports single-line messages.",
            }
            return result
        stage = "model_check"
        began = perf_counter()
        with httpx.Client(trust_env=False, timeout=5) as client:
            response = client.get(llm_client.HOST + "/api/tags")
            response.raise_for_status()
            if not any(
                m["name"] == GRAMMAR_MODEL and m["digest"] == GRAMMAR_DIGEST
                for m in response.json()["models"]
            ):
                result["message"] = (
                    "The reviewed grammar model is not installed. Check the setup guide."
                )
                return result
        stages[stage] = perf_counter() - began
        stage = "generation"
        began = perf_counter()
        proposal = check_sentence(text, model=GRAMMAR_MODEL)
        stages[stage] = perf_counter() - began
        if proposal["status"] != "valid":
            result["message"] = (
                "The grammar model returned an invalid response. Your reply is still available."
            )
            return result
        stage = "builtin_checker"
        began = perf_counter()
        with httpx.Client(base_url=CHECKER_HOST, trust_env=False, timeout=30) as client:
            response = client.post(
                "/v2/check", data={"language": "en-US", "text": text}
            )
            response.raise_for_status()
            builtin = response.json()
        stages[stage] = perf_counter() - began
        if builtin["software"]["version"] != "6.6" or builtin.get("warnings", {}).get(
            "incompleteResults"
        ):
            raise ValueError("Incomplete or unsupported checker response")
        stage = "supplemental_checker"
        began = perf_counter()
        count = collect_count_evidence([text])
        stages[stage] = perf_counter() - began
        stage = "decision"
        began = perf_counter()
        decision = explain_with_gaps(
            text, proposal["result"]["corrected_text"], builtin, count["per_input"][0]
        )
        stages[stage] = perf_counter() - began
        result = {"state": decision["state"]}
        if decision["state"] == "provisional":
            result.update(
                state="offered",
                corrected_text=proposal["result"]["corrected_text"],
                edit=decision["edit"],
                explanation=decision["explanation"],
                rule_id=decision["rule_id"],
                evidence_source=decision["evidence_source"],
            )
        elif decision["state"] == "no_proposal":
            result["message"] = (
                "No correction suggested. This does not guarantee the message is error-free."
            )
        else:
            result["message"] = (
                "No supported correction to show. This message may need a teacher's review."
            )
        return result
    except (
        LLMError,
        httpx.HTTPError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        result = {
            "state": "unavailable",
            "failed_stage": stage,
            "diagnostic_type": type(exc).__name__,
            "message": "Grammar feedback could not finish. Your conversational reply is still available. Check the local grammar services.",
        }
        return result
    finally:
        result["stage_seconds"] = stages
        result["feedback_seconds"] = perf_counter() - start
