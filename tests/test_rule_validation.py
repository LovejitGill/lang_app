"""Check validation bookkeeping without running the model."""

import json
import shutil

import pytest

import rule_validation as validation
from errors import LLMError


def test_frozen_files_and_approved_labels():
    contract, data = validation.verify_files()
    assert contract["gates"]["minimum_human_useful_corrections"] == 12
    assert len(data["cases"]) == 40


def test_changed_labels_are_rejected(tmp_path):
    folder = tmp_path / "validation"
    shutil.copytree(validation.DIRECTORY, folder)
    path = folder / "labels_approved.json"
    data = json.loads(path.read_text())
    data["cases"][0]["text"] = "changed"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Approved labels changed"):
        validation.verify_files(folder)


def test_only_text_and_model_enter_generation(monkeypatch):
    calls = []

    def fake(text, *, model):
        calls.append((text, model))
        return {"status": "valid", "result": {"corrected_text": "He works nearby."}}

    monkeypatch.setattr(validation, "check_sentence", fake)
    row = validation.evaluate_case("He work nearby.", "test-model")
    assert calls == [("He work nearby.", "test-model")]
    assert row["decision"]["state"] == "provisional"
    assert row["total_seconds"] == pytest.approx(
        row["generation_seconds"] + row["rule_seconds"]
    )


def test_service_failure_kept_without_retry(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise LLMError("offline")

    monkeypatch.setattr(validation, "check_sentence", fail)
    row = validation.evaluate_case("Hi.", "test-model")
    assert calls == [1]
    assert row["generation"]["error"] == "offline"
    assert row["decision"]["state"] == "unavailable"


def test_invalid_generation_never_reaches_rules(monkeypatch):
    monkeypatch.setattr(
        validation,
        "check_sentence",
        lambda *a, **k: {"status": "rejected", "raw": "bad", "result": None},
    )

    def unexpected(*args):
        pytest.fail("Rejected output reached rules")

    monkeypatch.setattr(validation, "explain_change", unexpected)
    assert validation.evaluate_case("Hi.", "test")["decision"]["state"] == "unavailable"


def test_summary_keeps_misses_and_unfinished_attempt():
    rows = [{"attempt_state": "started"}]
    report = validation.summarize(rows)
    assert report["attempts_started"] == 1
    assert report["completed"] == 0
    assert report["error_denominator"] == 20
    assert report["human_useful_feedback"] is None
    assert not report["coverage_gate_impossible"]


def test_existing_run_is_never_overwritten(monkeypatch, tmp_path):
    path = tmp_path / "heldout_results.json"
    path.write_text("retain me")
    monkeypatch.setattr(validation, "DIRECTORY", tmp_path)
    with pytest.raises(ValueError, match="already started"):
        validation.main()
    assert path.read_text() == "retain me"


def test_completed_low_coverage_fails_even_before_human_review():
    rows = []
    for i in range(40):
        rows.append(
            {
                "attempt_state": "complete",
                "expected_error": i < 20,
                "decision": {"state": "withheld" if i < 20 else "no_proposal"},
                "generation": {"status": "valid"},
                "reference_match": True,
                "generation_seconds": 1.0,
                "rule_seconds": 0.001,
                "total_seconds": 1.001,
            }
        )
    report = validation.summarize(rows)
    assert report["coverage_gate_impossible"]
    assert report["offered_on_errors"] == 0
    assert report["human_useful_feedback"] is None
    assert report["total_excluding_first"]["attempts"] == 39
    assert report["timing"]["total_seconds"]["attempts"] == 40
