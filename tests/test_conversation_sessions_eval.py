"""Verify conversation lineage, label isolation and failure accounting."""

import asyncio
from copy import deepcopy

from conversation_sessions_eval import collect, summarize


def session(identifier, count=2):
    return {
        "id": identifier,
        "level": "beginner",
        "scenario": "introductions",
        "turns": [
            {
                "id": f"{identifier}-{i}",
                "text": f"Message {i}",
                "expected": "PRIVATE_REFERENCE",
            }
            for i in range(count)
        ],
    }


def test_history_uses_actual_replies_only_and_resets_between_sessions():
    calls, snapshots = [], []

    async def respond(text, **kwargs):
        calls.append((text, deepcopy(kwargs)))
        return {
            "reply": f"Actual reply to {text}",
            "display_text": "GRAMMAR_NOT_HISTORY",
        }

    rows = asyncio.run(
        collect(
            [session("a", 6), session("b")],
            respond,
            lambda rows: snapshots.append(deepcopy(rows)),
        )
    )
    assert calls[0][1]["history"] == calls[6][1]["history"] == []
    assert calls[1][1]["history"] == [
        {"learner_text": "Message 0", "tutor_reply": "Actual reply to Message 0"}
    ]
    assert len(calls[5][1]["history"]) == 4
    assert calls[5][1]["history"][0]["learner_text"] == "Message 1"
    assert "PRIVATE_REFERENCE" not in str(calls)
    assert "GRAMMAR_NOT_HISTORY" not in str(calls)
    assert snapshots[0][0]["attempt_state"] == "started"
    assert all(r["attempt_state"] == "complete" for r in rows)


def test_failure_is_saved_without_retry_or_invented_history():
    calls = []

    async def respond(text, **kwargs):
        calls.append(text)
        if len(calls) == 1:
            raise TimeoutError("sensitive diagnostic")
        return {"reply": "A reply."}

    rows = asyncio.run(
        collect([session("a"), session("b")], respond, lambda rows: None)
    )
    assert [r["attempt_state"] for r in rows] == [
        "failed",
        "skipped",
        "complete",
        "complete",
    ]
    assert rows[0]["error_type"] == "TimeoutError"
    assert "sensitive diagnostic" not in str(rows)
    assert len(calls) == 3


def test_summary_retains_failed_latency_and_uses_all_turns_as_denominator():
    summary = summarize(
        [
            {
                "attempt_state": "complete",
                "seconds": 1,
                "path": "deterministic",
                "correction": {"state": "no_supported_correction"},
            },
            {"attempt_state": "failed", "seconds": 3},
            {"attempt_state": "skipped"},
        ],
        3,
    )
    assert summary["denominator"] == 3
    assert summary["completed"] == summary["failed"] == summary["skipped"] == 1
    assert summary["within_two_seconds"] == 1
    assert summary["timing"]["maximum_seconds"] == 3
    assert summary["human_useful"] is None
