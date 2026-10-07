"""Compare explanation wording on identical saved proposals and rule decisions."""

import argparse
import json
from pathlib import Path

from benchmark import ROOT, digest, save
from grammar_explanation_reasons import VARIANT, explain_with_reason

SOURCES = {
    "development": ROOT / "evaluation/broader_rules/development_results.json",
    "fresh_component": ROOT / "evaluation/broader_rules/fresh_results.json",
    "checker": ROOT / "evaluation/benchmark_v2/final_development_report.json",
}


def replay():
    raw = json.loads(SOURCES["checker"].read_text())
    checks = {
        r["case_id"]: r["raw"] for r in raw["rows"] if r["engine"] == "languagetool"
    }
    rows = []
    for cohort in ("development", "fresh_component"):
        data = json.loads(SOURCES[cohort].read_text())
        for case in data["rows"]:
            evidence = (
                checks[case["case_id"]] if cohort == "development" else case["raw"]
            )
            decision = explain_with_reason(case["original"], case["proposed"], evidence)
            old = case["decision"]
            if any(
                decision.get(key) != old.get(key)
                for key in ("state", "rule_id", "edit", "match_index")
            ):
                raise ValueError(
                    "Detection changed; this experiment must isolate wording."
                )
            rows.append(
                {
                    "cohort": cohort,
                    "case_id": case.get("case_id", case.get("id")),
                    "original": case["original"],
                    "proposed": case["proposed"],
                    "before": old,
                    "after": decision,
                    "human_review": {
                        "accurate": None,
                        "explains_why": None,
                        "easy_to_understand": None,
                        "reviewer": "",
                    },
                }
            )
    offered = [r for r in rows if r["after"]["state"] == "provisional"]
    return {
        "variant": VARIANT,
        "sources_sha256": {k: digest(v) for k, v in SOURCES.items()},
        "code_sha256": {
            name: digest(ROOT / name)
            for name in (
                "grammar_rule_detector.py",
                "grammar_explanation_reasons.py",
                "grammar_reason_eval.py",
            )
        },
        "scope": "Wording replay only. Previously fresh component cases are now inspected examples, not new validation. No accuracy approvals inherited for rewritten explanations.",
        "summary": {
            "cases": len(rows),
            "detection_changes": 0,
            "offered_explanations": len(offered),
            "contextual_drafts": sum(
                r["after"].get("reason_status") == "contextual_draft" for r in offered
            ),
            "needs_context_review": sum(
                r["after"].get("reason_status") == "needs_context_review"
                for r in offered
            ),
            "model_calls": 0,
            "checker_calls": 0,
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
