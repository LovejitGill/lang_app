"""Preserved comparison of authored question selection and its deadline fallback."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import bounded_conversation as flow
from benchmark import ROOT, digest, save, timing
from conversation_quality_eval import verify

DIRECTORY = ROOT / "evaluation/conversation_quality/bounded_v1"


async def run(output, *, cold=False):
    if output.exists():
        raise ValueError("Choose an unused output path; preserve earlier attempts.")
    protocol_path = DIRECTORY / "protocol_runner_v3.json"
    protocol = json.loads(protocol_path.read_text())
    for name, expected in protocol["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Prepared source changed: {name}")
    if digest(DIRECTORY / "cases.json") != protocol["dataset_sha256"]:
        raise ValueError("Prepared cases changed.")
    verify()  # The approved grammar flow and historical comparison remain intact.
    cases = json.loads((DIRECTORY / "cases.json").read_text())["cases"]
    async with httpx.AsyncClient(trust_env=False, timeout=30) as client:
        tags = await client.get(flow.HOST + "/api/tags")
        tags.raise_for_status()
        model = next(
            (m for m in tags.json()["models"] if m["name"] == flow.MODEL), None
        )
        if not model or model["digest"] != flow.MODEL_DIGEST:
            raise ValueError("Expected the prepared local model digest.")
        report = {
            "created_utc": datetime.now(UTC).isoformat(),
            "protocol_sha256": digest(protocol_path),
            "dataset_sha256": protocol["dataset_sha256"],
            "model": model,
            "condition": "cold_first_request" if cold else "prewarmed",
            "timing_scope": "In-memory preparation + HTTP wait/cancellation + rendering a complete text reply. Excludes DB, UI, STT, TTS, and readiness setup. Not a voice measurement.",
            "source_sha256": protocol["source_sha256"],
            "rows": [],
        }
        save(output, report, exclusive=True)
        began = perf_counter()
        # A cold test unloads only this model; other local model files remain intact.
        setup = await client.post(
            flow.HOST + "/api/chat",
            json={
                "model": flow.MODEL,
                "messages": [],
                "stream": False,
                "keep_alive": 0 if cold else "10m",
                "options": flow.OPTIONS,
            },
        )
        setup.raise_for_status()
        report["readiness_raw"] = setup.json()
        if not cold:
            # Prime the same selector/context, not merely the default-size model.
            choice, raw = await flow._select(
                flow.prepare("I made something."), [], client
            )
            report["readiness_probe"] = {
                "choice": choice,
                "raw": raw,
                "text": "I made something.",
            }
        report["readiness_seconds"] = perf_counter() - began
        save(output, report)
        for case in cases:
            report["rows"].append({"case_id": case["id"], "attempt_state": "started"})
            save(output, report)
            result = await flow.respond(
                case["text"],
                history=case["history"],
                level=case["level"],
                scenario=case["scenario"],
            )
            report["rows"][-1] = {
                "case_id": case["id"],
                "attempt_state": "complete",
                "status": "valid",  # A rendered text response, not a semantic pass.
                **result,
            }
            save(output, report)  # Preserve raw results even if summary code fails.
            rows = report["rows"]
            report["summary"] = {
                "denominator": len(cases),
                "completed": len(rows),
                "timing": timing(rows),
                "within_two_seconds": sum(r["seconds"] <= 2 for r in rows),
                "model_selected": sum(r["path"] == "model_selected" for r in rows),
                "local_fallback": sum(r["path"] == "local_fallback" for r in rows),
                "deterministic": sum(r["path"] == "deterministic" for r in rows),
                "unsupported_questions": sum(
                    r["support"] == "unsupported_question" for r in rows
                ),
                "human_useful": None,
                "human_review_status": "pending",
            }
            save(output, report)
            print(
                f"{case['id']} {result['path']} {result['seconds']:.3f}s: {result['reply']}",
                flush=True,
            )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--cold",
        action="store_true",
        help="Unload the selector model before the first measured request",
    )
    args = parser.parse_args()
    asyncio.run(run(args.output, cold=args.cold))
