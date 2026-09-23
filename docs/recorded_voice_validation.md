# Recorded-turn validation — 2026-09-22

## Environment and automated checks

- Local macOS 26.6.2 / x86_64, Python 3.12 environment.
- CPU supports INT8 according to `ctranslate2.get_supported_compute_types('cpu')`.
- faster-whisper 1.2.1, CTranslate2 4.8.2, ONNX Runtime 1.23.2, PyAV 18.1.0.
- `uv sync --locked --no-build` succeeded, checking 63 installed packages.
- 87 tests passed in 7.52 seconds; Ruff reported `All checks passed!`.
- Tests include empty/malformed/oversized/truncated WAV, silence, short/long
  clips, unsupported sample rate, uncertain/empty speech segments, missing
  weights, lazy inference failure, draft preservation, transcript review before
  Send, and no repeated transcription during ordinary UI reruns.

## Real CPU inference

The macOS synthetic-voice command produced an empty recording in this execution
environment, so no synthetic-speech result is claimed. Instead the public
[Whisper test fixture](https://github.com/openai/whisper/blob/main/tests/jfk.flac)
was downloaded to ignored `.tools/`, decoded to a mono 16 kHz PCM16 WAV, and
passed through the real `transcribe_audio()` function. No learner recording was
used or committed. Duration: 11 seconds.

Inference was run with `HF_HUB_OFFLINE=1` after the explicit model download.
First call including model loading: **3.50 s**. A second call using the same
loaded model: **0.84 s**. These are individual observations, not a benchmark or
end-to-end voice latency; LLM generation, recording, and user review are excluded.

The transcript preserved the broad message but rendered the imperative
“ask” as “asked” twice. This is a concrete recognition error that could mislead
grammar feedback, supporting the decision to make the transcript editable.

A one-second silent WAV returned the friendly error:
`I didn't catch speech. Move closer and record again.`

## Manual checkpoint still required

A separate AppTest integration run substituted only the recording widget with
the reference WAV. Real speech inference populated the draft, with zero database
turns before Send. Real Ollama generation then produced one saved exchange and
Turn #2; a subsequent rerun left the database at one turn. The temporary test
database was removed after the check and did not change the user's sessions.

The tutor again suggested a correction to identical wording and an unsupported
explanation about “can.” Thus the audio-to-tutor connection works, but the
earlier feedback-quality problem was also observed in this integration run.

AppTest substitutes the browser recording widget; it cannot establish that the
user's microphone permissions, browser capture, accent, or room noise work well.
Follow the five-sentence exercise in [recorded_voice.md](recorded_voice.md) and
record results. Grammar feedback remains separately unreliable. Do not label
this milestone as validated pronunciation assessment or automatic turn-taking.
