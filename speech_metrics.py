"""Offline measurement helpers; supply real recordings/transcripts/event timestamps."""

import argparse
import json
import math
import re
from pathlib import Path

from benchmark import timing


def word_error_rate(reference, hypothesis):
    """Case/punctuation-insensitive word edit distance; never normalize grammar."""

    def words(text):
        return re.findall(r"\w+(?:['’]\w+)*", text.lower())

    expected, actual = words(reference), words(hypothesis)
    if not expected:
        raise ValueError("Use a nonempty verbatim reference; test silence separately.")
    previous = list(range(len(actual) + 1))
    for i, word in enumerate(expected, 1):
        current = [i]
        for j, heard in enumerate(actual, 1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (word != heard),
                )
            )
        previous = current
    return {
        "word_errors": previous[-1],
        "reference_words": len(expected),
        "wer": previous[-1] / len(expected),
    }


def voice_latency(events):
    """All timestamps must share a monotonic clock; browser playback is authoritative."""
    keys = (
        "speech_end",
        "turn_detected",
        "transcript_ready",
        "first_token",
        "first_audio",
    )
    values = [events[k] for k in keys]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError("Timestamps must be finite numbers in seconds.")
    if values != sorted(values):
        raise ValueError("Events must be ordered on the same monotonic clock.")
    result = {
        "speech_end_to_first_audio": values[-1] - values[0],
        "turn_detection": values[1] - values[0],
        "transcription_after_detection": values[2] - values[1],
        "llm_to_first_token": values[3] - values[2],
        "first_token_to_playback": values[4] - values[3],
    }
    if "feedback_ready" in events:
        end = events["feedback_ready"]
        if type(end) not in (int, float) or not math.isfinite(end) or end < values[0]:
            raise ValueError("Invalid feedback timestamp.")
        result["speech_end_to_feedback"] = end - values[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="JSON with transcriptions and/or voice_turns arrays"
    )
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    transcriptions = [
        word_error_rate(r["reference"], r["hypothesis"])
        for r in data.get("transcriptions", [])
    ]
    turns = data.get("voice_turns", [])
    successful = [voice_latency(t["events"]) for t in turns if t["status"] == "valid"]
    result = {
        "transcriptions": transcriptions,
        "voice_turns_attempted": len(turns),
        "voice_turn_failures": sum(t["status"] != "valid" for t in turns),
        "voice_latency_successful_only": timing(
            [
                {"seconds": t["speech_end_to_first_audio"], "status": "valid"}
                for t in successful
            ]
        ),
    }
    if transcriptions:
        result["corpus_wer"] = sum(t["word_errors"] for t in transcriptions) / sum(
            t["reference_words"] for t in transcriptions
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
