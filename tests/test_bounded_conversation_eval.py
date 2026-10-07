"""The benchmark must preserve failures and the full denominator."""

import asyncio
import json

import httpx
import pytest

import bounded_conversation_eval as evaluation
from benchmark import digest


def test_report_checkpoints_responses_before_aggregation(monkeypatch, tmp_path):
    directory = tmp_path / "prepared"
    directory.mkdir()
    case = {
        "id": "test-1",
        "text": "Pottery.",
        "history": [],
        "level": "beginner",
        "scenario": "daily activities",
    }
    (directory / "cases.json").write_text(json.dumps({"cases": [case]}))
    (directory / "protocol_runner_v3.json").write_text(
        json.dumps(
            {
                "source_sha256": {},
                "dataset_sha256": digest(directory / "cases.json"),
            }
        )
    )
    monkeypatch.setattr(evaluation, "DIRECTORY", directory)
    monkeypatch.setattr(evaluation, "verify", lambda: None)
    real_client = httpx.AsyncClient

    def transport(request):
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": evaluation.flow.MODEL,
                            "digest": evaluation.flow.MODEL_DIGEST,
                        }
                    ]
                },
            )
        return httpx.Response(
            200, json={"done": True, "done_reason": "stop", "message": {"content": "0"}}
        )

    monkeypatch.setattr(
        evaluation.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(transport), **kw),
    )

    async def respond(*args, **kwargs):
        return {
            "reply": "A preserved response.",
            "path": "local_fallback",
            "support": "guided_practice",
            "seconds": 0.9,
            "raw_selector": None,
        }

    monkeypatch.setattr(evaluation.flow, "respond", respond)
    output = tmp_path / "result.json"
    original_timing = evaluation.timing

    def broken_summary(rows):
        raise RuntimeError("summary failed")

    monkeypatch.setattr(evaluation, "timing", broken_summary)
    with pytest.raises(RuntimeError, match="summary failed"):
        asyncio.run(evaluation.run(output))
    retained = json.loads(output.read_text())
    assert retained["rows"][0]["reply"] == "A preserved response."
    assert retained["rows"][0]["attempt_state"] == "complete"
    with pytest.raises(ValueError, match="unused output"):
        asyncio.run(evaluation.run(output))
    monkeypatch.setattr(evaluation, "timing", original_timing)
    report = asyncio.run(evaluation.run(tmp_path / "second.json"))
    assert report["summary"]["denominator"] == 1
    assert report["summary"]["local_fallback"] == 1
    assert report["summary"]["human_useful"] is None


def test_tampered_source_stops_before_model_access(monkeypatch, tmp_path):
    source = tmp_path / "source.py"
    source.write_text("changed")
    (tmp_path / "protocol_runner_v3.json").write_text(
        json.dumps({"source_sha256": {"source.py": "prepared_hash"}})
    )
    monkeypatch.setattr(evaluation, "DIRECTORY", tmp_path)
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Prepared source changed"):
        asyncio.run(evaluation.run(tmp_path / "output.json"))
    assert not (tmp_path / "output.json").exists()
