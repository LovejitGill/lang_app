"""Replay frozen proposed corrections through one isolated explanation review pass."""

import argparse
import copy
import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from benchmark import ROOT, digest, save, timing
from explanation_review import PROMPT, SCHEMA, review_change


def evaluate_pair(original, source_row, *, model):
    """Withheld corrections stay visible as unoffered proposals, not a clean bill of grammar."""
    row = {
        "case_id": source_row["case_id"],
        "source_status": source_row["status"],
        "source_result": copy.deepcopy(source_row.get("result")),
        "source_seconds": source_row["seconds"],
    }
    start = perf_counter()
    if source_row["status"] != "valid":
        row.update(
            status="upstream_failure",
            raw=None,
            result=None,
            reason="Source proposal unusable.",
        )
    else:
        try:
            row.update(
                review_change(
                    original, source_row["result"]["corrected_text"], model=model
                )
            )
        except llm_client.LLMError as exc:
            row.update(status="error", raw=None, result=None, reason=str(exc))
    row["review_seconds"] = round(perf_counter() - start, 4)
    row["would_offer_correction"] = (
        row["status"] == "valid" and row["result"]["decision"] == "supported"
    )
    if row["would_offer_correction"]:
        row["effective_text"] = source_row["result"]["corrected_text"]
        row["effective_explanation"] = row["result"]["explanation"]
    else:
        row["effective_text"] = original
        row["effective_explanation"] = None
    row["feedback_state"] = (
        "proposed"
        if row["would_offer_correction"]
        else "no_proposal"
        if row["status"] == "skipped"
        else "withheld"
        if row["status"] == "valid"
        else "unavailable"
    )
    return row


def summary(report):
    rows = report["rows"]
    cases = {c["id"]: c for c in report["dataset"]["cases"]}
    calls = [
        {"status": r["status"], "seconds": r["review_seconds"]}
        for r in rows
        if r["status"] not in ("skipped", "upstream_failure")
    ]
    return {
        "attempts": len(rows),
        "second_pass_calls": len(calls),
        "skipped_no_proposal": sum(r["status"] == "skipped" for r in rows),
        "supported_proposals": sum(r["would_offer_correction"] for r in rows),
        "withheld_proposals": sum(r["feedback_state"] == "withheld" for r in rows),
        "unavailable": sum(r["feedback_state"] == "unavailable" for r in rows),
        "correct_inputs_with_offered_change": sum(
            not cases[r["case_id"]]["expected_error"] and r["would_offer_correction"]
            for r in rows
        ),
        "erroneous_inputs_with_matching_offered_correction": sum(
            cases[r["case_id"]]["expected_error"]
            and r["would_offer_correction"]
            and r["effective_text"] in cases[r["case_id"]]["references"]
            for r in rows
        ),
        "review_call_timing": timing(calls),
        "warning": "Support is the same model self-review, not validation of grammar. Withheld genuine errors are misses. Exact matches are not useful-feedback scores. Source and review timings were measured in separate runs.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new filename.")
    source = ROOT / "evaluation/sentence_experiment/development_results.json"
    protocol_path = ROOT / "evaluation/explanation_experiment/protocol.json"
    contract = json.loads(protocol_path.read_text())
    if (
        digest(source) != contract["source_sha256"]
        or hashlib.sha256(PROMPT.encode()).hexdigest() != contract["prompt_sha256"]
        or SCHEMA != contract["schema"]
    ):
        parser.error("Source/prompt/schema differs from frozen protocol.")
    old = json.loads(source.read_text())
    if old["dataset"]["split"] != "development":
        parser.error("This experiment is development only.")
    cases = old["dataset"]["cases"]
    if len(old["rows"]) != len(cases) or {r["case_id"] for r in old["rows"]} != {
        c["id"] for c in cases
    }:
        parser.error("Source needs one completed attempt per case.")
    model = contract["model"]
    try:
        with httpx.Client(
            base_url=llm_client.HOST, trust_env=False, timeout=5
        ) as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            identity = next(m for m in response.json()["models"] if m["name"] == model)
        if identity["digest"] != contract["model_digest"]:
            parser.error("Model digest changed.")
    except (httpx.HTTPError, StopIteration) as exc:
        parser.exit(1, f"Cannot verify model: {exc}\n")
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "dataset": old["dataset"],
        "source_sha256": digest(source),
        "model_identity": identity,
        "protocol": contract,
        "protocol_sha256": digest(protocol_path),
        "prompt": PROMPT,
        "schema": SCHEMA,
        "platform": platform.platform(),
        "code_sha256": {
            p: digest(ROOT / p)
            for p in ("explanation_review.py", "explanation_eval.py", "llm_client.py")
        },
        "rows": [],
    }
    save(args.output, report, exclusive=True)
    by_id = {r["case_id"]: r for r in old["rows"]}
    for case in cases:
        row = evaluate_pair(case["text"], by_id[case["id"]], model=model)
        report["rows"].append(row)
        report["summary"] = summary(report)
        save(args.output, report)
        print(
            f"{case['id']} {row['status']} {row['feedback_state']} {row['review_seconds']}s",
            flush=True,
        )
    print(json.dumps(report["summary"], indent=2))
    return int(any(r["feedback_state"] == "unavailable" for r in report["rows"]))


if __name__ == "__main__":
    raise SystemExit(main())
