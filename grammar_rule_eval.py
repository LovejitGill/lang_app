"""Evaluate broader rule detection on cached development or fresh component cases."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import httpx

from benchmark import ROOT, digest, save
from grammar_rule_detector import VARIANT, explain_proposal

DIRECTORY = ROOT / "evaluation/broader_rules"


def development():
    sentences = ROOT / "evaluation/sentence_experiment/development_results.json"
    checker = ROOT / "evaluation/benchmark_v2/final_development_report.json"
    source, checks = json.loads(sentences.read_text()), json.loads(checker.read_text())
    if source["dataset_sha256"] != checks["dataset_sha256"]:
        raise ValueError("Development sources use different datasets.")
    texts = {c["id"]: c for c in checks["dataset"]["cases"]}
    raw = {
        r["case_id"]: r["raw"] for r in checks["rows"] if r["engine"] == "languagetool"
    }
    rows = []
    for row in source["rows"]:
        case = texts[row["case_id"]]
        if row["status"] != "valid":
            raise ValueError("This replay requires valid saved sentence proposals.")
        proposed = row["result"]["corrected_text"]
        result = explain_proposal(case["text"], proposed, raw[case["id"]])
        rows.append(
            {
                "case_id": case["id"],
                "original": case["text"],
                "proposed": proposed,
                "expected_error": case["expected_error"],
                "reference_match": proposed in case["references"],
                "decision": result,
                "human_useful": None,
            }
        )
    return {
        "sources_sha256": {
            str(p.relative_to(ROOT)): digest(p) for p in (sentences, checker)
        },
        "summary": {
            "cases": len(rows),
            "error_denominator": 30,
            "offered_on_errors": sum(
                r["expected_error"] and r["decision"]["state"] == "provisional"
                for r in rows
            ),
            "offered_on_correct": sum(
                not r["expected_error"] and r["decision"]["state"] == "provisional"
                for r in rows
            ),
        },
        "rows": rows,
    }


def fresh(path, output):
    cases = json.loads(path.read_text())["cases"]
    protocol = json.loads((DIRECTORY / "protocol.json").read_text())
    if digest(ROOT / "grammar_rule_detector.py") != protocol["detector_sha256"]:
        raise ValueError("Candidate changed after freeze.")
    report = {
        "variant": VARIANT,
        "protocol_sha256": digest(DIRECTORY / "protocol.json"),
        "cases_sha256": digest(path),
        "scope": "Fresh component checks with authored proposals; no LLM, not end-to-end held-out validation.",
        "rows": [],
    }
    save(output, report, exclusive=True)
    with httpx.Client(
        base_url="http://127.0.0.1:8081", trust_env=False, timeout=30
    ) as client:
        for case in cases:
            start = perf_counter()
            try:
                response = client.post(
                    "/v2/check", data={"language": "en-US", "text": case["original"]}
                )
                response.raise_for_status()
                raw = response.json()
                if raw["software"]["version"] != "6.6":
                    raise ValueError("Expected frozen LanguageTool 6.6.")
                decision = explain_proposal(case["original"], case["proposed"], raw)
                row = {
                    **case,
                    "raw": raw,
                    "decision": decision,
                    "passed": decision["state"] == case["expected_state"],
                }
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                row = {**case, "error": str(exc), "passed": False}
            row["seconds"] = perf_counter() - start
            report["rows"].append(row)
            save(output, report)
    report["summary"] = {
        "cases": len(cases),
        "passed": sum(r["passed"] for r in report["rows"]),
        "unavailable": sum("error" in r for r in report["rows"]),
        "llm_calls": 0,
    }
    save(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["development", "fresh"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve prior reports; choose a new filename.")
    if args.mode == "development":
        report = {
            "variant": VARIANT,
            "detector_sha256": digest(ROOT / "grammar_rule_detector.py"),
            **development(),
        }
        save(args.output, report, exclusive=True)
    else:
        report = fresh(DIRECTORY / "fresh_cases.json", args.output)
    print(json.dumps(report["summary"], indent=2))
