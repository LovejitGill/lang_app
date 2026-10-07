"""One saved attempt per held-out input; refuse reruns and verify frozen evidence."""

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from benchmark import digest, reviewed, save, timing
from rule_explanations import explain_change
from sentence_grammar import check_sentence

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / "evaluation/rule_validation"


def verify_files(directory=DIRECTORY, root=ROOT):
    contract = json.loads((directory / "protocol.json").read_text())
    for name, expected in contract["frozen_files_sha256"].items():
        if (
            digest(root / name) != expected
            or digest(directory / "frozen" / name) != expected
        ):
            raise ValueError(f"Frozen candidate mismatch: {name}")
    approval = json.loads((directory / "label_approval.json").read_text())
    if digest(directory / "labels_approved.json") != approval["approved_sha256"]:
        raise ValueError("Approved labels changed.")
    if digest(directory / "labels_pending.json") != approval["pending_sha256"]:
        raise ValueError("Original draft labels changed.")
    if approval["pending_sha256"] != contract["dataset_source_sha256"]:
        raise ValueError("Draft labels do not match protocol.")
    data = json.loads((directory / "labels_approved.json").read_text())
    pending = json.loads((directory / "labels_pending.json").read_text())
    # Approval may change review metadata, never silently change case content.
    strip = lambda case: {k: v for k, v in case.items() if k != "label_review"}
    if [strip(c) for c in data["cases"]] != [strip(c) for c in pending["cases"]]:
        raise ValueError("Case content differs from frozen draft.")
    if not reviewed(data) or len(data["cases"]) != 40:
        raise ValueError("Need all 40 reviewed cases.")
    if (
        len({c["id"] for c in data["cases"]}) != 40
        or sum(c["expected_error"] for c in data["cases"]) != 20
    ):
        raise ValueError("Invalid case IDs or class balance.")
    return contract, data


def evaluate_case(text, model):
    start = perf_counter()
    try:
        generation = check_sentence(text, model=model)
    except llm_client.LLMError as exc:
        generation = {
            "status": "error",
            "error": str(exc),
            "result": None,
            "raw": None,
            "edits": [],
        }
    generated_at = perf_counter()
    decision = {"state": "unavailable", "rule": None, "explanation": None}
    if generation["status"] == "valid":
        decision = explain_change(text, generation["result"]["corrected_text"])
    finished = perf_counter()
    return {
        "generation": generation,
        "decision": decision,
        "generation_seconds": generated_at - start,
        "rule_seconds": finished - generated_at,
        "total_seconds": finished - start,
    }


def summarize(rows):
    complete = [r for r in rows if r["attempt_state"] == "complete"]
    error_offers = [
        r
        for r in complete
        if r["expected_error"] and r["decision"]["state"] == "provisional"
    ]

    def stage(key, subset):
        return timing(
            [{"seconds": r[key], "status": r["generation"]["status"]} for r in subset]
        )

    return {
        "attempts_started": len(rows),
        "completed": len(complete),
        "unavailable": sum(r["decision"]["state"] == "unavailable" for r in complete),
        "offered_on_errors": len(error_offers),
        "error_denominator": 20,
        "offered_on_correct": sum(
            not r["expected_error"] and r["decision"]["state"] == "provisional"
            for r in complete
        ),
        "correct_denominator": 20,
        "reference_matches_among_error_offers": sum(
            r["reference_match"] for r in error_offers
        ),
        "human_useful_feedback": None,
        "coverage_gate_impossible": len(complete) == 40 and len(error_offers) < 12,
        "timing": {
            key: stage(key, complete)
            for key in ("generation_seconds", "rule_seconds", "total_seconds")
        },
        "first_attempt": {
            key: complete[0][key]
            for key in ("generation_seconds", "rule_seconds", "total_seconds")
        }
        if complete
        else None,
        "total_excluding_first": stage("total_seconds", complete[1:]),
    }


def main():
    output = DIRECTORY / "heldout_results.json"
    if output.exists():
        raise ValueError(
            "This validation already started; preserve evidence and do not rerun."
        )
    contract, data = verify_files()
    with httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        identity = next(
            m for m in response.json()["models"] if m["name"] == contract["model"]
        )
        version = client.get("/api/version").json()
    if identity["digest"] != contract["model_digest"]:
        raise ValueError("Model digest differs from frozen protocol.")
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "protocol": contract,
        "protocol_sha256": digest(DIRECTORY / "protocol.json"),
        "runner_sha256": digest(Path(__file__)),
        "model_identity": identity,
        "ollama_version": version,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "dataset": data,
        "dataset_sha256": digest(DIRECTORY / "labels_approved.json"),
        "rows": [],
    }
    save(output, report, exclusive=True)
    for case in data["cases"]:
        row = {
            "case_id": case["id"],
            "original": case["text"],
            "expected_error": case["expected_error"],
            "attempt_state": "started",
        }
        report["rows"].append(row)
        save(
            output, report
        )  # Persist intent before inference; interruptions are visible.
        row.update(evaluate_case(case["text"], contract["model"]))
        row["attempt_state"] = "complete"
        proposal = row["generation"]["result"]
        row["reference_match"] = bool(
            proposal and proposal["corrected_text"] in case["references"]
        )
        row["human_review"] = {
            "correct_necessary_edit": None,
            "explanation_accurate": None,
            "meaning_preserved": None,
            "useful_feedback": None,
            "reviewer": "",
        }
        report["summary"] = summarize(report["rows"])
        save(output, report)
        print(
            f"{case['id']} {row['decision']['state']} {row['total_seconds']:.3f}s",
            flush=True,
        )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
