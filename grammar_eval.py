"""Compare isolated grammar analysis with unchanged combined tutoring on fixed cases."""

import argparse
import hashlib
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from grammar import GRAMMAR_PROMPT, GRAMMAR_SCHEMA, check_grammar
from quality_eval import evaluate_case, load_cases


def evaluate_grammar(case, model=None):
    row = {**case, "variant": "grammar_only", "review": None}
    start = perf_counter()
    try:
        row.update(check_grammar(case["text"], model=model))
    except llm_client.LLMError as exc:
        row.update(status="error", error=str(exc), result=None)
    row["seconds"] = round(perf_counter() - start, 3)
    return row


def summarize(rows):
    summary = {}
    for variant in {row["variant"] for row in rows}:
        group = [row for row in rows if row["variant"] == variant]
        valid = [row for row in group if row.get("result") is not None]

        def nonempty(row):
            return bool(
                row["result"].get("corrections", row["result"].get("feedback", []))
            )

        summary[variant] = {
            "attempted": len(group),
            "valid": len(valid),
            "rejected": sum(row.get("status") == "rejected" for row in group),
            "service_errors": sum("error" in row for row in group),
            "valid_nonempty_on_correct": sum(
                not row["expected_error"] and nonempty(row) for row in valid
            ),
            "valid_nonempty_on_incorrect": sum(
                row["expected_error"] and nonempty(row) for row in valid
            ),
            "median_seconds_all_attempts": statistics.median(
                row["seconds"] for row in group
            ),
            "max_seconds": max(row["seconds"] for row in group),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split", choices=["development", "regression", "heldout"], required=True
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", choices=[1, 2], default=1, type=int)
    parser.add_argument("--grammar-model", default=llm_client.MODEL)
    parser.add_argument(
        "--grammar-only",
        action="store_true",
        help="Skip rerunning the combined baseline",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new filename to preserve results.")
    cases, digest = load_cases(args.split)
    try:
        with httpx.Client(
            base_url=llm_client.HOST, timeout=5, trust_env=False
        ) as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            model = next(
                item
                for item in response.json()["models"]
                if item["name"] == llm_client.MODEL
            )
            grammar_model = next(
                item
                for item in response.json()["models"]
                if item["name"] == args.grammar_model
            )
    except (httpx.HTTPError, StopIteration):
        parser.exit(
            1,
            f"Cannot verify the local models. Start Ollama and ensure {llm_client.MODEL} and {args.grammar_model} are installed.\n",
        )
    report = {
        "started_utc": datetime.now(UTC).isoformat(),
        "split": args.split,
        "dataset_sha256": digest,
        "model": model,
        "grammar_model": grammar_model,
        "grammar_prompt": GRAMMAR_PROMPT,
        "grammar_schema": GRAMMAR_SCHEMA,
        "grammar_prompt_sha256": hashlib.sha256(GRAMMAR_PROMPT.encode()).hexdigest(),
        "settings": {
            "think": False,
            "temperature": 0.2,
            "num_predict": 256,
            "num_ctx": 4096,
            "seed": "unset",
            "history": "none",
            "timing": "Separate calls; no UI, STT or human review. These are not sequential app-pipeline timings.",
            "retries": "Grammar: none; baseline: at most one format retry. Raw rejected grammar responses retained.",
        },
        "rows": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for run in range(1, args.runs + 1):
        for index, case in enumerate(cases):
            variants = (
                ["grammar_only"] if args.grammar_only else ["baseline", "grammar_only"]
            )
            if index % 2:
                variants.reverse()
            for variant in variants:
                row = (
                    evaluate_case(case, "baseline")
                    if variant == "baseline"
                    else evaluate_grammar(case, args.grammar_model)
                )
                row["run"] = run
                report["rows"].append(row)
                report["summary"] = summarize(report["rows"])
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                status = row.get("status", "error" if "error" in row else "valid")
                print(f"{case['id']} {variant} {status}: {row['seconds']}s", flush=True)
    print(json.dumps(report["summary"], indent=2))
    return int(
        any("error" in row or row.get("status") == "rejected" for row in report["rows"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
