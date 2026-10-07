"""Auditable, opt-in grammar benchmarks; never used by the tutor UI."""

import argparse
import hashlib
import json
import math
import platform
import statistics
import uuid
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from time import perf_counter

import httpx

import llm_client
from grammar import GRAMMAR_PROMPT, GRAMMAR_SCHEMA, check_grammar

ROOT = Path(__file__).resolve().parent
LT_URL = "http://127.0.0.1:8081"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def load_dataset(path):
    data = json.loads(Path(path).read_text())
    cases = data["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Dataset needs unique, nonempty cases.")
    for c in cases:
        if not isinstance(c["text"], str) or not c["text"].strip():
            raise ValueError("Empty learner input.")
        if type(c["expected_error"]) is not bool:
            raise ValueError("expected_error must be boolean.")
        if type(c["gold_error_count"]) is not int or c["gold_error_count"] < 0:
            raise ValueError("Invalid gold_error_count.")
        if bool(c["gold_error_count"]) != c["expected_error"]:
            raise ValueError("Error count conflicts with expected_error.")
        if not c["references"] or any(
            not isinstance(x, str) or not x.strip() for x in c["references"]
        ):
            raise ValueError("Each case needs reference sentences.")
    return data


def reviewed(data):
    return all(
        c["label_review"].get("status") == "approved"
        and c["label_review"].get("reviewer", "").strip()
        and c["label_review"].get("rationale", "").strip()
        for c in data["cases"]
    )


def utf16_span(text, offset, length):
    """Java offsets count UTF-16 units; Python indexes Unicode code points."""
    raw = text.encode("utf-16-le")
    if (
        type(offset) is not int
        or type(length) is not int
        or offset < 0
        or length < 0
        or 2 * (offset + length) > len(raw)
    ):
        raise ValueError("Invalid LanguageTool span.")
    start = len(raw[: 2 * offset].decode("utf-16-le"))
    end = start + len(raw[2 * offset : 2 * (offset + length)].decode("utf-16-le"))
    return start, end


def languagetool(text, client):
    response = client.post("/v2/check", data={"language": "en-US", "text": text})
    response.raise_for_status()
    raw = response.json()
    edits = []
    for match in raw["matches"]:
        start, end = utf16_span(text, match["offset"], match["length"])
        choices = match["replacements"]
        if not choices:
            return {
                "status": "rejected",
                "raw": raw,
                "edits": [],
                "reason": "A match has no replacement; retained in raw output.",
            }
        replacement = choices[0]["value"]
        if text[start:end] == replacement:
            return {
                "status": "rejected",
                "raw": raw,
                "edits": [],
                "reason": "No-op replacement.",
            }
        edits.append(
            {
                "original": text[start:end],
                "replacement": replacement,
                "explanation": match["message"],
                "start": start,
                "end": end,
                "rule_id": match["rule"]["id"],
                "explanation_source": "LanguageTool; human review pending",
            }
        )
    return {"status": "valid", "raw": raw, "edits": edits}


def apply_edits(text, edits):
    """Reject ambiguous or overlapping edits instead of guessing a corrected text."""
    spans = []
    for edit in edits:
        start, end = edit.get("start"), edit.get("end")
        if start is None:
            original = edit["original"]
            if not original or text.count(original) != 1:
                raise ValueError(
                    "Ambiguous original span; manually review before exporting."
                )
            start = text.index(original)
            end = start + len(original)
        if not 0 <= start <= end <= len(text) or text[start:end] != edit["original"]:
            raise ValueError("Invalid edit offsets.")
        spans.append((start, end, edit["replacement"]))
    spans.sort()
    for left, right in pairwise(spans):
        if left[1] > right[0] or left[0] == right[0]:
            raise ValueError("Overlapping edits.")
    for start, end, replacement in reversed(spans):
        text = text[:start] + replacement + text[end:]
    return text


def timing(rows):
    values = sorted(r["seconds"] for r in rows)
    return {
        "attempts": len(rows),
        "failures": sum(r["status"] != "valid" for r in rows),
        "median_seconds": statistics.median(values) if values else None,
        "p95_seconds_nearest_rank": values[math.ceil(0.95 * len(values)) - 1]
        if values
        else None,
        "maximum_seconds": max(values) if values else None,
    }


def run(args):
    data = load_dataset(args.dataset)
    if data["split"] == "heldout" and not reviewed(data):
        raise ValueError("Held-out labels need named human approval before evaluation.")
    if Path(args.output).exists():
        raise ValueError("Output already exists; preserve prior evidence.")
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": digest(args.dataset),
        "dataset": data,
        "labels_independently_reviewed": reviewed(data),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "model": args.model,
        "grammar_prompt": GRAMMAR_PROMPT,
        "grammar_schema": GRAMMAR_SCHEMA,
        "settings": {
            "think": False,
            "temperature": 0.2,
            "num_predict": 256,
            "num_ctx": 4096,
        },
        "protocol": "Independent calls, alternating order; first call separately identifiable, cache state uncontrolled. No STT/UI/TTS timing.",
        "rows": [],
    }
    with (
        httpx.Client(base_url=LT_URL, trust_env=False, timeout=30) as lt,
        httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as ollama,
    ):
        if "qwen" in args.engines:
            tags = ollama.get("/api/tags")
            tags.raise_for_status()
            report["model_identity"] = next(
                m for m in tags.json()["models"] if m["name"] == args.model
            )
        save(args.output, report, exclusive=True)
        seen = set()
        for repetition in range(1, args.runs + 1):
            for index, case in enumerate(data["cases"]):
                engines = (
                    args.engines if index % 2 == 0 else list(reversed(args.engines))
                )
                for engine in engines:
                    row = {
                        "blind_id": uuid.uuid4().hex,
                        "case_id": case["id"],
                        "engine": engine,
                        "run": repetition,
                        "first_engine_call": engine not in seen,
                    }
                    seen.add(engine)
                    start = perf_counter()
                    try:
                        if engine == "languagetool":
                            row.update(languagetool(case["text"], lt))
                        else:
                            result = check_grammar(case["text"], model=args.model)
                            row.update(result)
                            row["edits"] = (
                                result["result"]["corrections"]
                                if result["result"]
                                else []
                            )
                    except (
                        httpx.HTTPError,
                        llm_client.LLMError,
                        ValueError,
                        KeyError,
                        TypeError,
                    ) as exc:
                        row.update(status="error", reason=str(exc), edits=[])
                    row["seconds"] = round(perf_counter() - start, 4)
                    report["rows"].append(row)
                    save(args.output, report)
                    print(
                        f"{case['id']} {engine} {row['status']} {row['seconds']}s",
                        flush=True,
                    )
    print(
        json.dumps(
            {
                e: timing([r for r in report["rows"] if r["engine"] == e])
                for e in args.engines
            },
            indent=2,
        )
    )
    return int(any(r["status"] != "valid" for r in report["rows"]))


def make_review(args):
    report = json.loads(Path(args.report).read_text())
    cases = {c["id"]: c for c in report["dataset"]["cases"]}
    rows = []
    for r in report["rows"]:
        c = cases[r["case_id"]]
        rows.append(
            {
                "blind_id": r["blind_id"],
                "text": c["text"],
                "references": c["references"],
                "expected_issue": c["expected_issue"],
                "status": r["status"],
                "edits": [
                    {k: e[k] for k in ("original", "replacement", "explanation")}
                    for e in r["edits"]
                ],
                "reviewer": "",
                "rationale": "",
                "true_positive": None,
                "false_positive": None,
                "false_negative": None,
                "explanation_accurate": None,
                "meaning_preserved": None,
            }
        )
    # Random IDs allow reproducible shuffled presentation without revealing engine names.
    rows.sort(key=lambda r: r["blind_id"])
    save(
        args.output,
        {
            "report_sha256": digest(args.report),
            "instructions": "Human review required. TP/FP count proposed edits; FN counts missed gold errors. Do not count alternative valid wording as an error. Service/rejected rows remain failures.",
            "rows": rows,
        },
        exclusive=True,
    )
    print(f"Review worksheet: {len(rows)} rows; semantic scores pending.")


def score(report, review, *, include_runs=True):
    by_id = {r["blind_id"]: r for r in review["rows"]}
    if len(by_id) != len(review["rows"]) or set(by_id) != {
        r["blind_id"] for r in report["rows"]
    }:
        raise ValueError("Review rows must match the report exactly.")
    cases = {c["id"]: c for c in report["dataset"]["cases"]}
    output = {}
    for engine in sorted({r["engine"] for r in report["rows"]}):
        rows = [r for r in report["rows"] if r["engine"] == engine]
        tp = fp = fn = useful = false_sentences = pending = 0
        correct = sum(not cases[r["case_id"]]["expected_error"] for r in rows)
        incorrect = len(rows) - correct
        for row in rows:
            c, rating = cases[row["case_id"]], by_id[row["blind_id"]]
            if row["status"] != "valid":
                fn += c["gold_error_count"]
                continue
            counts = [
                rating[k] for k in ("true_positive", "false_positive", "false_negative")
            ]
            if (
                not rating["reviewer"].strip()
                or not rating["rationale"].strip()
                or any(v is None for v in counts)
                or any(
                    type(rating[k]) is not bool
                    for k in ("explanation_accurate", "meaning_preserved")
                )
            ):
                pending += 1
                continue
            if any(type(v) is not int or v < 0 for v in counts):
                raise ValueError("Review counts must be nonnegative integers.")
            a, b, missed = counts
            if a + b != len(row["edits"]) or a + missed != c["gold_error_count"]:
                raise ValueError(
                    "Edit counts disagree with proposals/gold errors; adjudicate labels first."
                )
            tp += a
            fp += b
            fn += missed
            false_sentences += int(not c["expected_error"] and b > 0)
            useful += int(
                c["expected_error"]
                and a > 0
                and not b
                and not missed
                and rating["explanation_accurate"]
                and rating["meaning_preserved"]
            )
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        metrics = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f0_5": 1.25 * tp / (1.25 * tp + 0.25 * fn + fp) if tp + fn + fp else None,
            "false_correction_rate": false_sentences / correct if correct else None,
            "useful_feedback_rate": useful / incorrect if incorrect else None,
            "correct_inputs": correct,
            "incorrect_inputs": incorrect,
        }
        output[engine] = {
            **timing(rows),
            "pending_reviews": pending,
            "semantic_metrics": None if pending else metrics,
            "label_status": "reviewed"
            if reviewed(report["dataset"])
            else "PROVISIONAL labels",
        }
    if include_runs:
        for engine, result in output.items():
            result["per_run"] = {}
            for repetition in sorted(
                {r["run"] for r in report["rows"] if r["engine"] == engine}
            ):
                selected = [
                    r
                    for r in report["rows"]
                    if r["engine"] == engine and r["run"] == repetition
                ]
                ids = {r["blind_id"] for r in selected}
                subset = {**report, "rows": selected}
                ratings = {
                    **review,
                    "rows": [r for r in review["rows"] if r["blind_id"] in ids],
                }
                result["per_run"][str(repetition)] = score(
                    subset, ratings, include_runs=False
                )[engine]
    return output


def export_errant(args):
    report = json.loads(Path(args.report).read_text())
    if not reviewed(report["dataset"]):
        raise ValueError("Review reference labels before exporting ERRANT data.")
    rows = [
        r for r in report["rows"] if r["engine"] == args.engine and r["run"] == args.run
    ]
    if len(rows) != len(report["dataset"]["cases"]) or any(
        r["status"] != "valid" for r in rows
    ):
        raise ValueError(
            "Export requires a complete valid run; failures cannot disappear from the benchmark."
        )
    cases = {c["id"]: c for c in report["dataset"]["cases"]}
    contents = {"source.txt": [], "hypothesis.txt": []}
    ref_count = max(len(c["references"]) for c in cases.values())
    for i in range(ref_count):
        contents[f"reference-{i}.txt"] = []
    for row in rows:
        case = cases[row["case_id"]]
        contents["source.txt"].append(case["text"])
        contents["hypothesis.txt"].append(apply_edits(case["text"], row["edits"]))
        for i in range(ref_count):
            refs = case["references"]
            contents[f"reference-{i}.txt"].append(refs[i] if i < len(refs) else refs[0])
    if any(
        "\n" in line or "\r" in line for lines in contents.values() for line in lines
    ):
        raise ValueError("ERRANT export needs single-line sentences.")
    Path(args.output).mkdir(parents=True, exist_ok=False)
    for filename, lines in contents.items():
        (Path(args.output) / filename).write_text("\n".join(lines) + "\n")
    save(
        Path(args.output) / "manifest.json",
        {
            "report_sha256": digest(args.report),
            "engine": args.engine,
            "run": args.run,
            "case_ids": [r["case_id"] for r in rows],
        },
    )
    print(
        "Aligned ERRANT inputs exported; scoring requires the separate ERRANT environment."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("run")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--engines",
        nargs="+",
        choices=["languagetool", "qwen"],
        default=["languagetool", "qwen"],
    )
    p.add_argument("--model", default="qwen3:4b")
    p.add_argument("--runs", type=int, choices=[1, 2], default=1)
    p = subs.add_parser("review")
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = subs.add_parser("score")
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p = subs.add_parser("export-errant")
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--engine", choices=["qwen", "languagetool"], required=True)
    p.add_argument("--run", type=int, default=1)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            return run(args)
        if args.command == "review":
            make_review(args)
        elif args.command == "score":
            report = json.loads(args.report.read_text())
            review = json.loads(args.review.read_text())
            if review["report_sha256"] != digest(args.report):
                raise ValueError("Review belongs to a different or changed report.")
            print(json.dumps(score(report, review), indent=2))
        elif args.command == "export-errant":
            export_errant(args)
    except (ValueError, KeyError, OSError, httpx.HTTPError, StopIteration) as exc:
        parser.exit(1, f"Benchmark stopped: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
