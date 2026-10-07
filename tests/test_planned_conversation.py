"""The integration carries only conversation history and retains correction provenance."""

from unittest.mock import MagicMock

import pytest

import db
import planned_conversation as adapter
from errors import LLMError


def test_adapter_uses_saved_dialogue_without_feedback_or_private_labels(
    tmp_path, monkeypatch
):
    path = tmp_path / "history.sqlite"
    db.init_db(path)
    db.insert_turn("s", "I enjoy sewing.", "What do you sew?", ["OLD_CORRECTION"], path)
    seen = []

    async def reply(text, **kwargs):
        seen.append((text, kwargs))
        return {
            "reply": "What will you make next?",
            "path": "model_selected",
            "support": "planned_followup",
            "correction": {"state": "no_supported_correction"},
            "seconds": 0.3,
        }

    monkeypatch.setattr(adapter, "ensure_model", lambda: None)
    monkeypatch.setattr(adapter.dialogue_planner, "respond", reply)
    text, details = adapter.conversation_reply(
        "I sew bags.",
        level="beginner",
        scenario="introductions",
        session_id="s",
        db_path=path,
    )
    assert text == "What will you make next?"
    assert seen[0][1]["history"] == [
        {"learner_text": "I enjoy sewing.", "tutor_reply": "What do you sew?"}
    ]
    assert "OLD_CORRECTION" not in str(seen)
    assert details["engine"] == "planned_v4"
    assert len(db.get_history("s", db_path=path)) == 1


def test_changed_or_missing_model_is_not_silently_adopted(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value.json.return_value = {
        "models": [{"name": adapter.base.MODEL, "digest": "different"}]
    }
    monkeypatch.setattr(adapter.httpx, "Client", lambda **kw: client)
    with pytest.raises(LLMError, match="prepared conversation model"):
        adapter.ensure_model()


def test_invalid_input_fails_before_model_or_history_access(monkeypatch):
    check = MagicMock()
    monkeypatch.setattr(adapter, "ensure_model", check)
    with pytest.raises(ValueError):
        adapter.conversation_reply(
            "",
            level="beginner",
            scenario="introductions",
            session_id="s",
            db_path="not-a-database",
        )
    check.assert_not_called()
