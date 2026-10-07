"""Preserve gap-fix regressions and fresh component checks, without LLM calls."""

import argparse
import json
from pathlib import Path

import httpx

from benchmark import ROOT, digest, save
from grammar_gap_detector import VARIANT, collect_count_evidence, explain_with_gaps

DIRECTORY = ROOT / "evaluation/detection_gaps"


def regression_cases():
    source = json.loads(
        (ROOT / "evaluation/benchmark_v2/final_development_report.json").read_text()
    )
    raw = {
        r["case_id"]: r["raw"] for r in source["rows"] if r["engine"] == "languagetool"
    }
    cases = []
    for row in json.loads(
        (ROOT / "evaluation/broader_rules/development_results.json").read_text()
    )["rows"]:
        cases.append(
            {
                **row,
                "id": row["case_id"],
                "cohort": "development",
                "raw": raw[row["case_id"]],
            }
        )
    for row in json.loads(
        (ROOT / "evaluation/broader_rules/fresh_results.json").read_text()
    )["rows"]:
        cases.append({**row, "cohort": "prior_component"})
    return cases


def evaluate(mode, output):
    if output.exists():
        raise ValueError("Preserve prior evidence; use an unused output path.")
    if mode == "regression":
        cases = regression_cases()
    else:
        protocol = json.loads((DIRECTORY / "protocol.json").read_text())
        for name, expected in protocol["files_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError(f"Frozen file changed: {name}")
        cases = json.loads((DIRECTORY / "fresh_cases.json").read_text())["cases"]
    report = {
        "variant": VARIANT,
        "mode": mode,
        "scope": "Authored/saved proposals; component validation, not end-to-end LLM results.",
        "candidate_sha256": digest(ROOT / "grammar_gap_detector.py"),
        "rule_sha256": digest(ROOT / "rules/en-speakwell.xml"),
        "rows": [],
    }
    if mode == "fresh":
        report.update(
            protocol_sha256=digest(DIRECTORY / "protocol.json"),
            cases_sha256=digest(DIRECTORY / "fresh_cases.json"),
        )
    save(output, report, exclusive=True)
    # One local Java call for the batch; retain its full evidence and diagnostics.
    custom = collect_count_evidence([c["original"] for c in cases])
    report["custom_evidence"] = custom
    save(output, report)
    with httpx.Client(
        base_url="http://127.0.0.1:8081", trust_env=False, timeout=30
    ) as client:
        for index, case in enumerate(cases):
            try:
                builtin = case.get("raw")
                if builtin is None:
                    response = client.post(
                        "/v2/check",
                        data={"language": "en-US", "text": case["original"]},
                    )
                    response.raise_for_status()
                    builtin = response.json()
                    if builtin["software"]["version"] != "6.6":
                        raise ValueError("Wrong LanguageTool version.")
                decision = explain_with_gaps(
                    case["original"],
                    case["proposed"],
                    builtin,
                    custom["per_input"][index],
                )
                row = {
                    **case,
                    "raw": builtin,
                    "decision": decision,
                    "human_review": None,
                }
                if "expected_state" in case:
                    row["passed"] = decision["state"] == case["expected_state"]
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                row = {**case, "error": str(exc), "passed": False}
            report["rows"].append(row)
            save(output, report)
    rows = report["rows"]
    checks = [r for r in rows if "expected_state" in r]
    dev = [r for r in rows if r.get("cohort") == "development"]
    report["summary"] = {
        "cases": len(rows),
        "component_checks": len(checks),
        "component_passes": sum(r.get("passed", False) for r in checks),
        "unavailable": sum("error" in r for r in rows),
        "llm_calls": 0,
        "development_offers_on_errors": sum(
            r["expected_error"] and r.get("decision", {}).get("state") == "provisional"
            for r in dev
        ),
        "development_offers_on_correct": sum(
            not r["expected_error"]
            and r.get("decision", {}).get("state") == "provisional"
            for r in dev
        ),
    }
    save(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["regression", "fresh"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.mode, args.output)["summary"], indent=2))
