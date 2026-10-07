"""Development-only sentence-diff experiment; archive baseline, never tune held-out."""

import argparse
import hashlib
import json
import platform
import uuid
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from benchmark import ROOT, digest, load_dataset, save, timing
from sentence_grammar import PROMPT, SCHEMA, check_sentence


def summarize(report):
    cases = {c["id"]: c for c in report["dataset"]["cases"]}
    valid = [r for r in report["rows"] if r["status"] == "valid"]
    return {
        **timing(report["rows"]),
        "unchanged_correct_inputs": sum(
            not cases[r["case_id"]]["expected_error"]
            and r["result"]["corrected_text"] == cases[r["case_id"]]["text"]
            for r in valid
        ),
        "exact_reference_matches_on_errors": sum(
            cases[r["case_id"]]["expected_error"]
            and r["result"]["corrected_text"] in cases[r["case_id"]]["references"]
            for r in valid
        ),
        "warning": "Exact-reference matching is diagnostic only, not a useful-feedback score. Alternative valid corrections may differ. Human explanation and meaning review required.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserve historical evidence.")
    dataset = ROOT / "evaluation/benchmark_v2/development.json"
    baseline = ROOT / "evaluation/benchmark_v2/final_development_report.json"
    protocol = ROOT / "evaluation/sentence_experiment/protocol.json"
    data = load_dataset(dataset)
    contract = json.loads(protocol.read_text())
    if data["split"] != "development" or digest(dataset) != contract["dataset_sha256"]:
        parser.error("Development dataset differs from frozen protocol.")
    if (
        digest(baseline) != contract["baseline_sha256"]
        or hashlib.sha256(PROMPT.encode()).hexdigest() != contract["prompt_sha256"]
    ):
        parser.error("Baseline or prompt differs from frozen protocol.")
    model = contract["model"]
    try:
        with httpx.Client(
            base_url=llm_client.HOST, trust_env=False, timeout=5
        ) as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            identity = next(m for m in response.json()["models"] if m["name"] == model)
        if identity["digest"] != contract["model_digest"]:
            parser.error("Model digest differs from frozen protocol.")
    except (httpx.HTTPError, StopIteration) as exc:
        parser.exit(1, f"Cannot verify local model: {exc}\n")
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "engine": "sentence_diff",
        "dataset": data,
        "dataset_sha256": digest(dataset),
        "model_identity": identity,
        "protocol": contract,
        "protocol_sha256": digest(protocol),
        "grammar_prompt": PROMPT,
        "grammar_schema": SCHEMA,
        "platform": platform.platform(),
        "code_sha256": {
            name: digest(ROOT / name)
            for name in ("sentence_grammar.py", "sentence_eval.py", "llm_client.py")
        },
        "rows": [],
    }
    save(args.output, report, exclusive=True)
    for index, case in enumerate(data["cases"]):
        row = {
            "blind_id": uuid.uuid4().hex,
            "case_id": case["id"],
            "engine": "sentence_diff",
            "run": 1,
            "first_engine_call": index == 0,
        }
        start = perf_counter()
        try:
            row.update(check_sentence(case["text"], model=model))
        except llm_client.LLMError as exc:
            row.update(status="error", error=str(exc), result=None, edits=[])
        row["seconds"] = round(perf_counter() - start, 4)
        report["rows"].append(row)
        report["summary"] = summarize(report)
        save(args.output, report)
        print(f"{case['id']} {row['status']} {row['seconds']}s", flush=True)
    print(json.dumps(report["summary"], indent=2))
    return int(any(r["status"] != "valid" for r in report["rows"]))


if __name__ == "__main__":
    raise SystemExit(main())
