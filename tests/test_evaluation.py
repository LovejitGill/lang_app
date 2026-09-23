"""Evaluation must report failure honestly and isolate normal learner history."""

from unittest.mock import MagicMock

import evaluate
import llm_client
from errors import TutorUnavailable


def test_evaluation_uses_isolated_storage(monkeypatch, tmp_path):
    normal = tmp_path / "normal.sqlite"
    monkeypatch.setenv("SPEAKWELL_DB_PATH", str(normal))
    monkeypatch.setattr(
        llm_client, "_chat", lambda *a, **kw: '{"reply":"Tell me more.","feedback":[]}'
    )
    result = evaluate.run_evaluation()
    assert result["saved_turns"] == 5
    assert not normal.exists()
    assert all(case["feedback_rating"] is None for case in result["cases"])
    assert result["rerun_no_duplicate"]


def test_service_failures_are_not_counted_as_completed(monkeypatch):
    monkeypatch.setattr(
        llm_client, "_chat", MagicMock(side_effect=TutorUnavailable("offline"))
    )
    result = evaluate.run_evaluation()
    assert result["saved_turns"] == 0
    assert result["median_seconds"] is None
    assert len(result["cases"]) == 5
    assert all(case["errors"] for case in result["cases"])
