"""Run a prepared local model comparison without changing the application's model."""

import argparse
import asyncio
import json
from pathlib import Path

import bounded_conversation as base
import contextual_conversation_eval as evaluation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cold", action="store_true")
    args = parser.parse_args()
    protocol = json.loads((args.protocol_dir / "protocol.json").read_text())
    # These bindings live only in this separate evaluation process. The runner
    # verifies installed digest, source hashes, and dataset before inference.
    base.MODEL = protocol["model"]
    base.MODEL_DIGEST = protocol["model_digest"]
    evaluation.DIRECTORY = args.protocol_dir
    asyncio.run(evaluation.run(args.output, cold=args.cold))


if __name__ == "__main__":
    main()
