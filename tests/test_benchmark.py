import copy
import json
from types import SimpleNamespace

import httpx
import pytest

import benchmark as b


def case(error=True):
    return {
        "id": "one",
        "text": "She walk." if error else "She walks.",
        "expected_error": error,
        "gold_error_count": int(error),
        "references": ["She walks."],
        "expected_issue": "Agreement",
        "label_review": {"status": "pending", "reviewer": "", "rationale": ""},
    }


def sample(error=True, status="valid", edits=True):
    report = {
        "dataset": {"cases": [case(error)]},
        "rows": [
            {
                "blind_id": "id",
                "case_id": "one",
                "engine": "qwen",
                "run": 1,
                "status": status,
                "seconds": 2,
                "edits": [
                    {
                        "original": "walk",
                        "replacement": "walks",
                        "explanation": "Agreement",
                    }
                ]
                if edits
                else [],
            }
        ],
    }
    review = {
        "rows": [
            {
                "blind_id": "id",
                "reviewer": "Human",
                "rationale": "Checked the rule",
                "true_positive": 1 if error and edits else 0,
                "false_positive": 1 if not error and edits else 0,
                "false_negative": 1 if error and not edits else 0,
                "explanation_accurate": True,
                "meaning_preserved": True,
            }
        ]
    }
    return report, review


def test_utf16_non_bmp():
    assert b.utf16_span("😀 He walk.", 6, 4) == (5, 9)


@pytest.mark.parametrize("offset,length", [(-1, 2), (1, 30), (1, -1)])
def test_bad_offsets(offset, length):
    with pytest.raises(ValueError):
        b.utf16_span("abc", offset, length)


def test_lt_keeps_all_matches_and_raw():
    raw = {
        "software": {"version": "6.6"},
        "matches": [
            {
                "offset": 4,
                "length": 4,
                "replacements": [{"value": "walks"}],
                "message": "Agreement",
                "rule": {"id": "TEST"},
            }
        ],
    }
    with httpx.Client(
        base_url=b.LT_URL,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=raw)),
    ) as client:
        result = b.languagetool("She walk.", client)
    assert result["raw"] == raw
    assert b.apply_edits("She walk.", result["edits"]) == "She walks."


def test_no_suggestion_is_rejected_not_clean():
    raw = {
        "matches": [
            {"offset": 0, "length": 3, "replacements": [], "message": "Unknown"}
        ]
    }
    with httpx.Client(
        base_url=b.LT_URL,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=raw)),
    ) as client:
        assert b.languagetool("abc", client)["status"] == "rejected"


def test_ambiguous_span_refused():
    with pytest.raises(ValueError, match="Ambiguous"):
        b.apply_edits("go go", [{"original": "go", "replacement": "went"}])


def test_overlap_refused():
    with pytest.raises(ValueError, match="Overlapping"):
        b.apply_edits(
            "abcd",
            [
                {"original": "abc", "replacement": "x", "start": 0, "end": 3},
                {"original": "cd", "replacement": "y", "start": 2, "end": 4},
            ],
        )


def test_no_corrections_cannot_win():
    report, review = sample(edits=False)
    result = b.score(report, review)["qwen"]["semantic_metrics"]
    assert result["recall"] == result["useful_feedback_rate"] == 0
    assert result["precision"] is None


def test_false_corrections_count():
    report, review = sample(error=False)
    assert (
        b.score(report, review)["qwen"]["semantic_metrics"]["false_correction_rate"]
        == 1
    )


@pytest.mark.parametrize("status", ["error", "rejected"])
def test_failures_are_misses(status):
    report, review = sample(status=status, edits=False)
    result = b.score(report, review)["qwen"]
    assert result["failures"] == 1
    assert result["semantic_metrics"]["fn"] == 1
    assert result["semantic_metrics"]["useful_feedback_rate"] == 0


def test_pending_does_not_show_accuracy():
    report, review = sample()
    review["rows"][0]["reviewer"] = ""
    assert b.score(report, review)["qwen"]["semantic_metrics"] is None


def test_wrong_explanation_not_useful():
    report, review = sample()
    review["rows"][0]["explanation_accurate"] = False
    result = b.score(report, review)["qwen"]["semantic_metrics"]
    assert result["recall"] == 1
    assert result["useful_feedback_rate"] == 0


def test_duplicate_reviews_refused():
    report, review = sample()
    review["rows"].append(copy.deepcopy(review["rows"][0]))
    with pytest.raises(ValueError):
        b.score(report, review)


def test_inconsistent_counts_refused():
    report, review = sample()
    review["rows"][0]["true_positive"] = 2
    with pytest.raises(ValueError):
        b.score(report, review)


def test_heldout_gate_before_network(tmp_path):
    dataset = tmp_path / "set.json"
    dataset.write_text(json.dumps({"split": "heldout", "cases": [case()]}))
    with pytest.raises(ValueError, match="human approval"):
        b.run(SimpleNamespace(dataset=dataset))


def test_export_gate(tmp_path):
    report, _ = sample()
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Review reference"):
        b.export_errant(SimpleNamespace(report=path))


def test_p95_nearest_rank():
    rows = [{"status": "valid", "seconds": i} for i in range(1, 21)]
    assert b.timing(rows)["p95_seconds_nearest_rank"] == 19


def test_no_overwrite(tmp_path):
    path = tmp_path / "result.json"
    b.save(path, {}, exclusive=True)
    with pytest.raises(FileExistsError):
        b.save(path, {}, exclusive=True)


def test_corpus_balance_and_separation():
    root = b.ROOT / "evaluation/benchmark_v2"
    dev, held = [
        b.load_dataset(root / f"{split}.json") for split in ("development", "heldout")
    ]
    assert len(dev["cases"]) + len(held["cases"]) == 100
    assert not {c["text"] for c in dev["cases"]} & {c["text"] for c in held["cases"]}
    for data in (dev, held):
        assert (
            sum(c["expected_error"] for c in data["cases"]) == len(data["cases"]) // 2
        )


def test_runs_are_reported_separately():
    report, review = sample()
    missed = copy.deepcopy(report["rows"][0])
    missed.update(blind_id="second", run=2, edits=[])
    report["rows"].append(missed)
    rating = copy.deepcopy(review["rows"][0])
    rating.update(blind_id="second", true_positive=0, false_negative=1)
    review["rows"].append(rating)
    result = b.score(report, review)["qwen"]["per_run"]
    assert result["1"]["semantic_metrics"]["useful_feedback_rate"] == 1
    assert result["2"]["semantic_metrics"]["useful_feedback_rate"] == 0


def test_review_completion_requires_every_label():
    data = {"cases": [case(), case()]}
    assert not b.reviewed(data)
    for item in data["cases"]:
        item["label_review"] = {
            "status": "approved",
            "reviewer": "Human",
            "rationale": "Accepted",
        }
    assert b.reviewed(data)
    data["cases"][1]["label_review"]["status"] = "pending"
    assert not b.reviewed(data)
