"""Repeatable dialogue checks, isolated SQLite memory, human quality ratings."""

import argparse
import json
import tempfile
import uuid
from pathlib import Path
from time import perf_counter

import httpx

import db
import llm_client
from benchmark import digest, save


def run(dataset, output):
    cases = json.loads(Path(dataset).read_text())
    with httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        model = next(
            m for m in response.json()["models"] if m["name"] == llm_client.MODEL
        )
    report = {
        "dataset_sha256": digest(dataset),
        "model": model,
        "timing_scope": "Text through LLM/parser/history only; no UI/STT/TTS",
        "rows": [],
    }
    save(output, report, exclusive=True)
    with tempfile.TemporaryDirectory(prefix="speakwell-conversation-") as directory:
        for case in cases:
            session = uuid.uuid4().hex
            path = Path(directory) / "history.sqlite"
            for turn in case["turns"]:
                row = {
                    "case_id": case["id"],
                    "level": case["level"],
                    **turn,
                    "review": {
                        "reviewer": "",
                        "direct_answer": None,
                        "history_use": None,
                        "followup_relevance": None,
                        "level_fit": None,
                        "rationale": "",
                    },
                }
                start = perf_counter()
                try:
                    row["result"] = llm_client.ask_tutor(
                        turn["text"],
                        level=case["level"],
                        session_id=session,
                        db_path=path,
                    )
                    row["status"] = "valid"
                except (llm_client.LLMError, db.StorageError) as exc:
                    row.update(status="error", error=str(exc))
                row["seconds"] = round(perf_counter() - start, 4)
                report["rows"].append(row)
                save(output, report)
                print(f"{case['id']} {row['status']} {row['seconds']}s", flush=True)
    return int(any(r["status"] != "valid" for r in report["rows"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_v2/conversations.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.dataset, args.output))
