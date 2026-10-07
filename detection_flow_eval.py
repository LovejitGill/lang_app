"""One-attempt combined validation using frozen generation and rule components."""

import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from benchmark import ROOT, digest, reviewed, save, timing
from grammar_gap_detector import collect_count_evidence, explain_with_gaps
from sentence_grammar import check_sentence

DIRECTORY = ROOT / "evaluation/detection_flow_validation"


def verify(directory=DIRECTORY):
    protocol = json.loads((directory / "protocol.json").read_text())
    for name, expected in protocol["candidate_files_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Frozen candidate changed: {name}")
    approval = json.loads((directory / "label_approval.json").read_text())
    draft_path, approved_path = (
        directory / "labels_pending.json",
        directory / "labels_approved.json",
    )
    if (
        digest(draft_path) != protocol["pending_labels_sha256"]
        or digest(draft_path) != approval["pending_sha256"]
    ):
        raise ValueError("Draft differs from approved frozen labels.")
    if digest(approved_path) != approval["approved_sha256"]:
        raise ValueError("Approved label file changed.")
    data, draft = (
        json.loads(approved_path.read_text()),
        json.loads(draft_path.read_text()),
    )

    def content(case):
        return {k: v for k, v in case.items() if k != "label_review"}

    if [content(c) for c in data["cases"]] != [content(c) for c in draft["cases"]]:
        raise ValueError("Case content changed during approval.")
    if not reviewed(data) or [c["id"] for c in data["cases"]] != protocol["sequence"]:
        raise ValueError("Missing label approval or changed case order.")
    if (
        len(data["cases"]) != 32
        or len({c["id"] for c in data["cases"]}) != 32
        or sum(c["expected_error"] for c in data["cases"]) != 16
    ):
        raise ValueError("Expected 32 unique inputs with 16 errors.")
    return protocol, data


def run_case(text, model, client, checkpoint=lambda row: None):
    """Only learner text enters inference; checkpoint each completed stage."""
    start = perf_counter()
    row = {
        "generation": None,
        "builtin": None,
        "supplemental": None,
        "decision": {"state": "unavailable", "explanation": None},
        "seconds": {
            "generation": None,
            "builtin": None,
            "supplemental": None,
            "decision": None,
        },
    }
    stage = "generation"
    stage_start = perf_counter()
    try:
        row[stage] = check_sentence(text, model=model)
        row["seconds"][stage] = perf_counter() - stage_start
        checkpoint(row)
        if row["generation"]["status"] == "valid":
            stage, stage_start = "builtin", perf_counter()
            response = client.post(
                "/v2/check", data={"language": "en-US", "text": text}
            )
            response.raise_for_status()
            row[stage] = response.json()
            if row[stage]["software"]["version"] != "6.6" or row[stage].get(
                "warnings", {}
            ).get("incompleteResults"):
                raise ValueError("Wrong checker version or incomplete results.")
            row["seconds"][stage] = perf_counter() - stage_start
            checkpoint(row)
            stage, stage_start = "supplemental", perf_counter()
            # One process for this input: measure real per-input overhead, not a batch average.
            row[stage] = collect_count_evidence([text])
            row["seconds"][stage] = perf_counter() - stage_start
            checkpoint(row)
            stage, stage_start = "decision", perf_counter()
            row["decision"] = explain_with_gaps(
                text,
                row["generation"]["result"]["corrected_text"],
                row["builtin"],
                row["supplemental"]["per_input"][0],
            )
            row["seconds"][stage] = perf_counter() - stage_start
    except (
        llm_client.LLMError,
        httpx.HTTPError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
    ) as exc:
        row["seconds"][stage] = perf_counter() - stage_start
        row["failure"] = {
            "stage": stage,
            "type": type(exc).__name__,
            "message": str(exc),
        }
        # Keep diagnostics when the local checker process fails or times out.
        for name in ("stdout", "stderr"):
            value = getattr(exc, name, None)
            if value is not None:
                row["failure"][name] = (
                    value.decode(errors="replace")
                    if isinstance(value, bytes)
                    else value
                )
    row["total_seconds"] = perf_counter() - start
    return row


def summarize(rows):
    complete = [r for r in rows if r["attempt_state"] == "complete"]
    offered = [r for r in complete if r["decision"]["state"] == "provisional"]
    error_offers = [r for r in offered if r["expected_error"]]
    stages = {}
    for stage in ("generation", "builtin", "supplemental", "decision"):
        values = [
            {
                "seconds": r["seconds"][stage],
                "status": "error"
                if r.get("failure", {}).get("stage") == stage
                or (stage == "generation" and r["generation"]["status"] != "valid")
                else "valid",
            }
            for r in complete
            if r["seconds"][stage] is not None
        ]
        stages[stage] = timing(values)
    total = lambda subset: timing(
        [
            {
                "seconds": r["total_seconds"],
                "status": "valid"
                if r["decision"]["state"] != "unavailable"
                else "error",
            }
            for r in subset
        ]
    )
    return {
        "attempts_started": len(rows),
        "completed": len(complete),
        "offered_on_errors": len(error_offers),
        "error_denominator": 16,
        "offered_reference_matches": sum(r["reference_match"] for r in error_offers),
        "offered_on_correct": sum(not r["expected_error"] for r in offered),
        "correct_denominator": 16,
        "withheld_errors": sum(
            r["expected_error"] and r["decision"]["state"] == "withheld"
            for r in complete
        ),
        "unchanged_errors": sum(
            r["expected_error"] and r["decision"]["state"] == "no_proposal"
            for r in complete
        ),
        "unavailable": sum(r["decision"]["state"] == "unavailable" for r in complete),
        "human_useful_feedback": None,
        "human_useful_upper_bound": len(error_offers),
        "coverage_gate_impossible": len(complete) == 32 and len(error_offers) < 13,
        "stage_timings": stages,
        "total_timing": total(complete),
        "total_excluding_first": total(complete[1:]),
        "first_attempt_seconds": complete[0]["total_seconds"] if complete else None,
    }


def main():
    path = DIRECTORY / "results.json"
    if path.exists():
        raise ValueError(
            "Validation already started; preserve evidence and do not rerun."
        )
    protocol, data = verify()
    with httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        identity = next(
            m for m in response.json()["models"] if m["name"] == protocol["model"]
        )
        version_response = client.get("/api/version")
        version_response.raise_for_status()
        version = version_response.json()
    if identity["digest"] != protocol["model_digest"]:
        raise ValueError("Model differs from the frozen protocol.")
    with httpx.Client(
        base_url="http://127.0.0.1:8081", trust_env=False, timeout=30
    ) as checker:
        checker.get("/v2/languages").raise_for_status()
        report = {
            "created_utc": datetime.now(UTC).isoformat(),
            "protocol_sha256": digest(DIRECTORY / "protocol.json"),
            "runner_sha256": digest(Path(__file__)),
            "approved_labels_sha256": digest(DIRECTORY / "labels_approved.json"),
            "protocol": protocol,
            "dataset": data,
            "model_identity": identity,
            "ollama_version": version,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "timing_scope": "Sequential generation + builtin HTTP + one custom Java process per input + decision and checkpoint overhead. Not audio/voice latency.",
            "rows": [],
        }
        save(path, report, exclusive=True)
        for case in data["cases"]:
            row = {
                "case_id": case["id"],
                "display_id": case["display_id"],
                "original": case["text"],
                "expected_error": case["expected_error"],
                "attempt_state": "started",
            }
            report["rows"].append(row)
            save(path, report)

            def checkpoint(progress, target=row):
                target.update(progress)
                save(path, report)

            row.update(run_case(case["text"], protocol["model"], checker, checkpoint))
            row["attempt_state"] = "complete"
            proposal = (row["generation"] or {}).get("result")
            row["reference_match"] = bool(
                proposal and proposal["corrected_text"] in case["references"]
            )
            row["human_review"] = {
                "correct_necessary_edit": None,
                "meaning_preserved": None,
                "explanation_accurate": None,
                "useful_feedback": None,
                "reviewer": "",
            }
            report["summary"] = summarize(report["rows"])
            save(path, report)
            print(
                f"{case['display_id']} {row['decision']['state']} {row['total_seconds']:.3f}s",
                flush=True,
            )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
