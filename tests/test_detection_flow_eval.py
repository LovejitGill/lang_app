"""Run bookkeeping checks with fake inference; never retry or leak labels."""

import json
import shutil
import subprocess

import pytest

import detection_flow_eval as flow
from errors import LLMError


class Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {"software": {"version": "6.6"}, "matches": []}


class Checker:
    def __init__(self):
        self.calls = []

    def post(self, path, *, data):
        self.calls.append((path, data))
        return Response()


@pytest.fixture
def fake_pipeline(monkeypatch):
    calls = []

    def generate(text, *, model):
        calls.append((text, model))
        return {
            "status": "valid",
            "raw": "retained",
            "result": {"corrected_text": "Corrected."},
        }

    monkeypatch.setattr(flow, "check_sentence", generate)
    monkeypatch.setattr(
        flow,
        "collect_count_evidence",
        lambda texts: {"raw": {"matches": []}, "per_input": [{"matches": []}]},
    )
    monkeypatch.setattr(
        flow,
        "explain_with_gaps",
        lambda *args: {"state": "provisional", "explanation": "draft"},
    )
    return calls


@pytest.fixture
def frozen_candidate(monkeypatch, tmp_path):
    """Verify the evaluated source snapshot after later wording-only edits."""
    protocol = json.loads((flow.DIRECTORY / "protocol.json").read_text())
    for name in protocol["candidate_files_sha256"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        source = flow.ROOT / name
        if name == "grammar_explanation_reasons.py":
            source = flow.DIRECTORY / "frozen/grammar_explanation_reasons.py.txt"
        target.symlink_to(source)
    monkeypatch.setattr(flow, "ROOT", tmp_path)


def test_labels_and_frozen_candidate_verified(frozen_candidate):
    protocol, data = flow.verify()
    assert len(data["cases"]) == 32
    assert protocol["gates"]["minimum_human_useful_error_cases"] == 13


def test_changed_approved_labels_rejected(tmp_path, frozen_candidate):
    directory = tmp_path / "validation"
    directory.mkdir()
    for name in (
        "protocol.json",
        "labels_pending.json",
        "labels_approved.json",
        "label_approval.json",
    ):
        shutil.copy(flow.DIRECTORY / name, directory / name)
    path = directory / "labels_approved.json"
    data = json.loads(path.read_text())
    data["cases"][0]["references"] = ["changed"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Approved label file changed"):
        flow.verify(directory)


def test_actual_text_only_and_checkpoints(fake_pipeline):
    checker, stages = Checker(), []
    result = flow.run_case(
        "Input.",
        "fake",
        checker,
        lambda row: stages.append(tuple(row["seconds"].values())),
    )
    assert fake_pipeline == [("Input.", "fake")]
    assert checker.calls == [("/v2/check", {"language": "en-US", "text": "Input."})]
    assert len(stages) == 3
    assert result["generation"]["raw"] == "retained"
    assert result["total_seconds"] >= sum(result["seconds"].values())


def test_generation_failure_no_retry(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise LLMError("offline")

    monkeypatch.setattr(flow, "check_sentence", fail)
    checker = Checker()
    row = flow.run_case("Input.", "fake", checker)
    assert calls == [1] and checker.calls == []
    assert row["decision"]["state"] == "unavailable"
    assert row["failure"]["stage"] == "generation"
    row.update(attempt_state="complete", expected_error=True, reference_match=False)
    summary = flow.summarize([row])
    assert summary["unavailable"] == 1
    assert summary["stage_timings"]["builtin"]["attempts"] == 0


def test_rejected_output_retained_no_checkers(monkeypatch):
    monkeypatch.setattr(
        flow,
        "check_sentence",
        lambda *a, **k: {"status": "rejected", "raw": "invalid", "result": None},
    )
    checker = Checker()
    row = flow.run_case("Input.", "fake", checker)
    assert row["generation"]["raw"] == "invalid"
    assert row["decision"]["state"] == "unavailable"
    assert checker.calls == []


def test_checker_process_failure_keeps_diagnostics(monkeypatch, fake_pipeline):
    def fail(texts):
        raise subprocess.CalledProcessError(
            1, ["java"], output="partial", stderr="checker error"
        )

    monkeypatch.setattr(flow, "collect_count_evidence", fail)
    row = flow.run_case("Input.", "fake", Checker())
    assert row["failure"]["stage"] == "supplemental"
    assert row["failure"]["stdout"] == "partial"
    assert row["generation"]["raw"] == "retained"
    assert row["decision"]["state"] == "unavailable"


def test_existing_run_is_protected(monkeypatch, tmp_path):
    path = tmp_path / "results.json"
    path.write_text("untouched")
    monkeypatch.setattr(flow, "DIRECTORY", tmp_path)
    with pytest.raises(ValueError, match="already started"):
        flow.main()
    assert path.read_text() == "untouched"


def test_incomplete_attempt_does_not_disappear():
    summary = flow.summarize([{"attempt_state": "started"}])
    assert summary["attempts_started"] == 1 and summary["completed"] == 0
    assert summary["error_denominator"] == 16
    assert summary["correct_denominator"] == 16
    assert summary["human_useful_feedback"] is None
