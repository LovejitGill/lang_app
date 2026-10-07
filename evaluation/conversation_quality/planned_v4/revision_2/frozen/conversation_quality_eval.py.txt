"""Controlled prompt comparison; retain every attempt without semantic auto-grading."""

import argparse
import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

import conversation_prompts
import llm_client
from benchmark import ROOT, digest, save, timing
from errors import LLMError
from separate_feedback import (
    conversation_messages,
    conversation_schema,
    parse_conversation_reply,
)

DIRECTORY = ROOT / "evaluation/conversation_quality"


def verify(directory=DIRECTORY, *, protected_overrides=None):
    protocol = json.loads((directory / "protocol.json").read_text())
    if digest(directory / "cases.json") != protocol["dataset_sha256"]:
        raise ValueError("Development cases changed after preparation.")
    for variant, prompt in protocol["prompts"].items():
        if conversation_prompts.PROMPT_VARIANTS[variant] != prompt:
            raise ValueError("Prepared prompt changed.")
    overrides = protected_overrides or {}
    if set(overrides) - {"app.py", "feedback_store.py"}:
        raise ValueError("Only explicit UI/storage integration identities may change.")
    for name, expected in protocol["protected_sha256"].items():
        expected = overrides.get(name, expected)
        if digest(ROOT / name) != expected:
            raise ValueError(f"Protected source changed: {name}")
    tree = ast.parse((ROOT / "separate_feedback.py").read_text())
    grammar = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "grammar_feedback"
    )
    if (
        hashlib.sha256(ast.dump(grammar).encode()).hexdigest()
        != protocol["grammar_function_ast_sha256"]
    ):
        raise ValueError("Grammar flow changed.")
    data = json.loads((directory / "cases.json").read_text())
    cases = data["cases"]
    if len(cases) != 16 or len({c["id"] for c in cases}) != 16:
        raise ValueError("Expected sixteen unique development cases.")
    return protocol, data


def run_attempt(case, variant, model):
    # Explicit allowlist: expectations and review fields never enter generation.
    messages = conversation_messages(
        case["text"],
        level=case["level"],
        scenario=case["scenario"],
        history=case["history"],
        prompt_variant=variant,
    )
    row = {
        "case_id": case["id"],
        "variant": variant,
        "messages": messages,
        "raw": None,
        "reply": None,
    }
    began = perf_counter()
    try:
        row["raw"] = llm_client._chat(
            messages, schema=conversation_schema(variant), model=model
        )
        row["reply"] = parse_conversation_reply(row["raw"], variant)
        row["status"] = "valid"
    except (LLMError, ValueError) as exc:
        row.update(status="unavailable", error=str(exc), error_type=type(exc).__name__)
    row["seconds"] = perf_counter() - began
    row["attempt_state"] = "complete"
    return row


def summarize(rows, variants):
    return {
        variant: {
            "denominator": 16,
            "attempts_started": sum(r["variant"] == variant for r in rows),
            "valid": sum(
                r["variant"] == variant and r.get("status") == "valid" for r in rows
            ),
            "unavailable": sum(
                r["variant"] == variant and r.get("status") == "unavailable"
                for r in rows
            ),
            "timing": timing(
                [r for r in rows if r["variant"] == variant and "seconds" in r]
            ),
            "human_useful": None,
        }
        for variant in variants
    }


def run(output, directory=DIRECTORY):
    if output.exists():
        raise ValueError("Preserve this comparison; choose an unused output path.")
    protocol, data = verify(directory)
    with httpx.Client(base_url=llm_client.HOST, trust_env=False, timeout=5) as client:
        response = client.get("/api/tags")
        response.raise_for_status()
        model = next(
            (m for m in response.json()["models"] if m["name"] == protocol["model"]),
            None,
        )
    if model is None or model["digest"] != protocol["model_digest"]:
        raise ValueError("Expected the prepared local conversation model.")
    variants = list(protocol["prompts"])
    report = {
        "created_utc": datetime.now(UTC).isoformat(),
        "scope": data["scope"],
        "protocol_sha256": digest(directory / "protocol.json"),
        "dataset_sha256": digest(directory / "cases.json"),
        "model_identity": model,
        "settings": protocol["settings"],
        "schema_by_variant": {v: conversation_schema(v) for v in variants},
        "source_sha256": {
            name: digest(ROOT / name)
            for name in (
                "conversation_quality_eval.py",
                "conversation_prompts.py",
                "separate_feedback.py",
                "llm_client.py",
            )
        },
        "timing_scope": "One generation and parse, including any model loading; excludes UI, storage, speech and grammar. First-call cache/loading is uncontrolled.",
        "rows": [],
    }
    save(output, report, exclusive=True)
    for index, case in enumerate(data["cases"]):
        order = variants if index % 2 == 0 else variants[::-1]
        for variant in order:
            report["rows"].append(
                {"case_id": case["id"], "variant": variant, "attempt_state": "started"}
            )
            save(output, report)
            result = run_attempt(case, variant, protocol["model"])
            report["rows"][-1] = result
            report["summary"] = summarize(report["rows"], variants)
            save(output, report)
            print(
                f"{case['id']} {variant} {result['status']} {result['seconds']:.2f}s: {result['reply']}",
                flush=True,
            )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, default=DIRECTORY)
    args = parser.parse_args()
    run(args.output, args.protocol_dir)
