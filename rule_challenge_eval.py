"""Run fixed boundary checks; no LLM calls, training, or held-out inputs."""

import argparse
import json
from pathlib import Path

from benchmark import digest, save
from rule_explanations import VARIANT, explain_change

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "evaluation/rule_challenges/cases.json"


def evaluate():
    cases = json.loads(CASES.read_text())["cases"]
    rows = []
    for case in cases:
        result = explain_change(case["original"], case["proposed"])
        rows.append(
            {
                **case,
                "actual": result,
                "passed": result["state"] == case["expected_state"],
            }
        )
    return {
        "variant": VARIANT,
        "cases_sha256": digest(CASES),
        "code_sha256": digest(ROOT / "rule_explanations.py"),
        "limitations": "Assistant-authored policy/grammar challenge expectations. State checks do not establish explanation quality, independent generalization, or end-to-end performance.",
        "summary": {
            "cases": len(rows),
            "passed": sum(r["passed"] for r in rows),
            "failed": sum(not r["passed"] for r in rows),
            "model_calls": 0,
        },
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    save(args.output, report, exclusive=True)
    print(json.dumps(report["summary"], indent=2))
    for row in report["rows"]:
        if not row["passed"]:
            print(row["id"], row["original"], "=>", row["actual"]["state"])
