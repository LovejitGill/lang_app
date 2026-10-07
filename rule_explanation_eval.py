"""Replay saved proposals without inference; diagnostic coverage, not human scores."""

import argparse
import json
from pathlib import Path

from benchmark import digest, save
from rule_explanations import TEMPLATES, VARIANT, explain_change

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "evaluation/sentence_experiment/development_results.json"
DATA = ROOT / "evaluation/benchmark_v2/development.json"


def replay():
    source = json.loads(SOURCE.read_text())
    if source["dataset_sha256"] != digest(DATA):
        raise ValueError(
            "Dataset changed since source inference; review provenance first."
        )
    cases = {c["id"]: c for c in json.loads(DATA.read_text())["cases"]}
    if len(source["rows"]) != len(cases) or {
        r["case_id"] for r in source["rows"]
    } != set(cases):
        raise ValueError("Expected exactly one source response for every case.")
    rows = []
    for row in source["rows"]:
        case = cases[row["case_id"]]
        proposed = row["result"]["corrected_text"] if row["status"] == "valid" else None
        # Only original/proposed text enter the candidate. Labels are scoring-only.
        decision = (
            explain_change(case["text"], proposed)
            if proposed
            else {
                "state": "unavailable",
                "rule": None,
                "explanation": None,
            }
        )
        offered = decision["state"] == "provisional"
        rows.append(
            {
                "case_id": case["id"],
                "original": case["text"],
                "proposed": proposed,
                **decision,
                "expected_error": case["expected_error"],
                "offered_reference_match": offered and proposed in case["references"],
                "human_review": {
                    "rule_applies": None,
                    "explanation_clear": None,
                    "useful_feedback": None,
                    "reviewer": "",
                },
            }
        )
    errors = [r for r in rows if r["expected_error"]]
    return {
        "variant": VARIANT,
        "source_sha256": digest(SOURCE),
        "dataset_sha256": digest(DATA),
        "code_sha256": digest(ROOT / "rule_explanations.py"),
        "templates": TEMPLATES,
        "template_review": "pending",
        "limitations": "Development-informed rules, single saved run, finite vocabulary. Matching is not semantic proof. No human useful-feedback score or voice latency measured.",
        "summary": {
            "cases": len(rows),
            "model_calls": 0,
            "provisional_offers": sum(r["state"] == "provisional" for r in rows),
            "withheld_proposals": sum(r["state"] == "withheld" for r in rows),
            "no_proposal": sum(r["state"] == "no_proposal" for r in rows),
            "unavailable": sum(r["state"] == "unavailable" for r in rows),
            "false_offers_on_correct_inputs": sum(
                r["state"] == "provisional" and not r["expected_error"] for r in rows
            ),
            "error_reference_matches_offered": sum(
                r["offered_reference_match"] for r in errors
            ),
            "error_denominator": len(errors),
            "human_useful_feedback": None,
        },
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay()
    save(args.output, report, exclusive=True)
    print(json.dumps(report["summary"], indent=2))
