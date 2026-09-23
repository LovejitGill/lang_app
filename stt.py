"""Recorded English WAV → text. Audio stays in memory; inference stays local."""

import argparse
import io
import os
import threading
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np

from errors import TranscriptionError

MODEL_ID = "Systran/faster-whisper-base.en"
MODEL_REVISION = "3d3d5dee26484f91867d81cb899cfcf72b96be6c"
MODEL_DIR = Path(__file__).resolve().parent / ".models" / "faster-whisper-base.en"
MODEL_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
MAX_SECONDS = 60
MAX_BYTES = 2_000_000
_INFERENCE_LOCK = threading.Lock()


def decode_recording(audio: bytes) -> np.ndarray:
    """Accept the 16 kHz, mono PCM16 WAV produced by our recording widget."""
    if not isinstance(audio, bytes) or not audio:
        raise TranscriptionError("Record a short sentence first.")
    if len(audio) > MAX_BYTES:
        raise TranscriptionError("Recording is too large. Keep it under 60 seconds.")
    try:
        with wave.open(io.BytesIO(audio), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (
                1,
                2,
                16000,
            ) or wav.getcomptype() != "NONE":
                raise TranscriptionError("Use a mono, 16 kHz, 16-bit WAV recording.")
            frames = wav.getnframes()
            if not 0.3 <= frames / 16000 <= MAX_SECONDS:
                raise TranscriptionError("Record between 0.3 and 60 seconds of speech.")
            raw = wav.readframes(frames)
            if len(raw) != frames * 2:
                raise TranscriptionError(
                    "Recording is incomplete. Please record again."
                )
    except (wave.Error, EOFError, OSError) as exc:
        raise TranscriptionError("Cannot read this WAV. Please record again.") from exc
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    # This catches near-silence, not all noise; VAD handles speech detection later.
    if float(np.sqrt(np.mean(samples**2))) < 0.001:
        raise TranscriptionError("I didn't catch speech. Move closer and record again.")
    return samples


def download_model() -> Path:
    """Explicit setup step: download pinned public weights, never learner audio."""
    # Keep downloader metadata/logs beside this project's ignored model cache.
    os.environ.setdefault(
        "HF_HOME", str(MODEL_DIR.parent.parent / ".cache" / "huggingface")
    )
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    from huggingface_hub import snapshot_download

    snapshot_download(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=MODEL_DIR,
        allow_patterns=list(MODEL_FILES),
    )
    return MODEL_DIR


@lru_cache(maxsize=1)
def get_model():
    """Load once per Python process; normal use must not download missing files."""
    if not all((MODEL_DIR / filename).is_file() for filename in MODEL_FILES):
        raise TranscriptionError(
            "Speech model missing. Run: uv run --locked python stt.py --download"
        )
    from faster_whisper import WhisperModel

    return WhisperModel(
        str(MODEL_DIR),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
        local_files_only=True,
    )


def transcribe_audio(audio: bytes) -> str:
    """Validate, detect speech, then consume the model's lazy segment iterator."""
    samples = decode_recording(audio)
    try:
        # Serialize model access, including lazy iteration, to bound CPU use.
        with _INFERENCE_LOCK:
            segments, _ = get_model().transcribe(
                samples,
                language="en",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            parts = []
            for segment in segments:
                if segment.no_speech_prob > 0.6 or segment.avg_logprob < -1.0:
                    raise TranscriptionError(
                        "Speech was unclear. Try a shorter recording in a quieter place."
                    )
                parts.append(segment.text.strip())
    except TranscriptionError:
        raise
    except Exception as exc:
        # Includes errors during lazy generation, not just model construction.
        raise TranscriptionError(
            "Local transcription failed. Check the speech model or use typed input."
        ) from exc
    text = " ".join(part for part in parts if part).strip()
    if not text:
        raise TranscriptionError("I didn't catch speech. Please record again.")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", nargs="?", type=Path)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    try:
        if args.download:
            print(f"Speech model ready: {download_model()}")
        elif args.recording:
            # Bound file reads before decoding a possibly oversized recording.
            with args.recording.open("rb") as source:
                audio = source.read(MAX_BYTES + 1)
            print(f"Transcript: {transcribe_audio(audio)}")
        else:
            parser.error("provide a WAV path or --download")
    except (TranscriptionError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
