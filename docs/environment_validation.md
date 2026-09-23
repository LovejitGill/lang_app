# Environment validation — 2026-09-22

Milestone 0 was verified on macOS 26.6.2 (25G83), x86_64, using Python
3.12.13 and uv 0.12.0. No application code was created.

| Check | Result |
|---|---|
| Official Ollama archive SHA-256 | Matched `2c45865f94bce0d4d1d2567603dd2fdacaf375585220a175aa4800105193d36e` |
| Ollama binary architecture | Universal binary containing x86_64 and arm64 |
| `bash scripts/setup.sh` | Passed: locked sync, checksum, extraction, imports |
| `uv run --locked python` imports | Streamlit, Ollama client, and SQLite imported successfully |
| `uv pip check` | All 47 installed packages compatible |
| Separate virtual environment | Recreated `.cache/repro-venv` from `uv.lock` using `uv sync --locked --offline`; imports passed |
| Tool entry points | Streamlit 1.64.0, pytest 9.1.1, Ruff 0.16.8 |
| Shell syntax | `bash -n scripts/setup.sh scripts/ollama.sh` passed |
| Ollama local health | `/api/version` returned `0.34.3` |
| Model download | `qwen3:1.7b` downloaded successfully; full digest in `model_manifest.json` |
| Terminal generation | Passed with thinking disabled |
| Runtime device | `ollama ps` reported 100% CPU, 4,096-token context |
| Git whitespace check | `git diff --check` passed |

The clean-environment check used cached packages on this computer. It verifies
lockfile recreation, not installation on another operating system or an entirely
fresh Mac. No application test suite or speech-model compatibility was claimed.

## Observed terminal request

Command:

```bash
bash scripts/ollama.sh run qwen3:1.7b --think=false --verbose \
  'Say hello in one short sentence.'
```

Observed response:

> Hello! How can I assist you today?

Ollama reported total duration **8.970 seconds**, model loading **8.102 seconds**,
prompt evaluation **0.206 seconds**, and generation **0.656 seconds** for ten
output tokens (about **15.25 tokens/second**). This is one first-load terminal
request, not a conversational benchmark and not the speech pipeline's latency.

## Scope boundaries

The environment contains Streamlit and the Ollama client as runtime dependencies,
with pytest and Ruff in the development group. SQLite is part of Python.
Pipecat, faster-whisper, Kokoro, Wav2Vec2, frontend code, prompts, and application
modules are not installed or implemented in this milestone. Their compatibility
and performance remain separate development work.

The downloaded executables, model weights, caches, logs, and virtual environments
are ignored by Git. The existing `implementation_plan.md` was left unchanged.
No commit, push, cloud endpoint, or startup/login service was created.

The verification server was shut down after the checks. Start it explicitly with
`bash scripts/ollama.sh serve` before the next development session.
