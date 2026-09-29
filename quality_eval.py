"""Opt-in prompt comparison. Fixed labels stay outside model messages."""

import argparse
import hashlib
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import httpx

import llm_client
from prompts import PROMPT_VARIANTS, build_system_prompt

ROOT = Path(__file__).resolve().parent


def load_cases(split):
    path = ROOT / "evaluation" / f"{split}.json"
    raw = path.read_bytes()
    return json.loads(raw)["cases"], hashlib.sha256(raw).hexdigest()


def evaluate_case(case, variant):
    """Use the real retry/parser path, without saving test inputs as user history."""
    prompt = build_system_prompt(case["level"], case["scenario"], variant=variant)
    row = {
        **case,
        "variant": variant,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_characters": len(prompt),
        "review": None,
    }
    start = perf_counter()
    with (
        patch.object(llm_client, "build_system_prompt", return_value=prompt),
        patch.object(llm_client, "_chat", wraps=llm_client._chat) as calls,
    ):
        try:
            row["result"] = llm_client.ask_tutor(
                case["text"], level=case["level"], scenario=case["scenario"]
            )
        except llm_client.LLMError as exc:
            row["error"] = str(exc)
        row["attempts"] = calls.call_count
    row["seconds"] = round(perf_counter() - start, 3)
    return row


def summarize(rows):
    """Mechanical metrics only: nonempty feedback is NOT a useful-correction score."""
    summary = {}
    for variant in sorted({row["variant"] for row in rows}):
        selected = [row for row in rows if row["variant"] == variant]
        good = [row for row in selected if "result" in row]
        correct = [row for row in good if not row["expected_error"]]
        incorrect = [row for row in good if row["expected_error"]]
        summary[variant] = {
            "attempted": len(selected),
            "completed": len(good),
            "correct_inputs_with_feedback": sum(
                bool(row["result"]["feedback"]) for row in correct
            ),
            "correct_inputs_completed": len(correct),
            "incorrect_inputs_with_feedback": sum(
                bool(row["result"]["feedback"]) for row in incorrect
            ),
            "incorrect_inputs_completed": len(incorrect),
            "median_seconds_all_calls": statistics.median(
                row["seconds"] for row in selected
            ),
            "max_seconds": max(row["seconds"] for row in selected),
            "retried_cases": sum(row["attempts"] > 1 for row in selected),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split", choices=["development", "heldout", "regression"], required=True
    )
    parser.add_argument(
        "--variants", choices=list(PROMPT_VARIANTS), nargs="+", required=True
    )
    parser.add_argument("--runs", type=int, choices=[1, 2], default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; use a new filename to preserve evidence.")
    cases, digest = load_cases(args.split)
    with httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        model = next(
            item
            for item in response.json()["models"]
            if item["name"] == llm_client.MODEL
        )
    report = {
        "started_utc": datetime.now(UTC).isoformat(),
        "split": args.split,
        "dataset_sha256": digest,
        "model": model,
        "settings": {
            "think": False,
            "temperature": 0.2,
            "num_predict": 256,
            "num_ctx": 4096,
            "history": "none; independent cases",
            "timing": "LLM/parser/retry only; no STT/UI",
            "seed": "unset; variation possible",
            "order": "variant order alternates by case",
        },
        "rows": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for run in range(1, args.runs + 1):
        for index, case in enumerate(cases):
            variants = (
                args.variants if index % 2 == 0 else list(reversed(args.variants))
            )
            for variant in variants:
                row = evaluate_case(case, variant)
                row["run"] = run
                report["rows"].append(row)
                report["summary"] = summarize(report["rows"])
                # Save every completed attempt so an interrupted run retains evidence.
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                print(
                    f"run={run} {case['id']} {variant}: {row['seconds']}s {'ERROR' if 'error' in row else 'completed'}",
                    flush=True,
                )
    print(json.dumps(report["summary"], indent=2))
    return int(any("error" in row for row in report["rows"]))


if __name__ == "__main__":
    raise SystemExit(main())
