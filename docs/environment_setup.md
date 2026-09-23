# Milestone 0 — Reproducible Local Environment

This step installs and verifies tools only. It does not implement an LLM client,
prompts, UI, speech processing, or database application code. The repository's
`implementation_plan.md`, Section 10, defines this milestone.

## Tested configuration

| Component | Version/configuration |
|---|---|
| Host | macOS 26.6.2 (25G83), x86_64 Intel Mac |
| Python | CPython 3.12.13, pinned in `.python-version` |
| Project/dependency manager | uv 0.12.0 |
| Streamlit | 1.64.0 |
| Ollama Python client | 0.6.2 |
| pytest | 9.1.1, development dependency |
| Ruff | 0.16.8, development dependency |
| Ollama server/CLI | 0.34.3, official universal macOS binary |
| Model | `qwen3:1.7b`, Q4_K_M quantization |
| Inference | Local CPU; cloud features disabled |
| Server | `127.0.0.1:11434`, one concurrent request, 4,096-token context |

Python 3.12.13 was already available on this Mac and passed the milestone's
imports. The project constrains Python to the 3.12 series; the exact tested
patch is pinned. Future speech packages need their own compatibility checks;
this setup does not establish Pipecat, Kokoro, or Wav2Vec2 compatibility.

`pyproject.toml` declares direct dependencies, and `uv.lock` records exact
resolved versions and package hashes. The `ollama` Python package is an HTTP
client; it does not install or start the Ollama model server.

## Setup from a checkout

Use Terminal and change into the repository root, the directory containing
`pyproject.toml`. Do not run `uv init speakwell` here: this repository is already
initialized, and that would create an unnecessary nested project.

1. Install `uv` if needed using its [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
   The verified version is listed above. `uv` can download the pinned Python if
   it is absent. Git and macOS's `curl`, `tar`, and `shasum` are prerequisites.
2. Stop any project-local Ollama process before rerunning bootstrap, because it
   extracts the pinned executable into `.tools/ollama`.
3. Run:

   ```bash
   bash scripts/setup.sh
   ```

   This runs `uv sync --locked`, verifies the SHA-256 of the official Ollama
   archive before extraction, and checks Python imports. It does not run an
   unattended server or install a login/background service. Initial setup and
   model download need internet access; subsequent local inference does not
   require a paid account or API key. Allow several GB of free disk space.

4. In Terminal A, start the server and leave it running:

   ```bash
   bash scripts/ollama.sh serve
   ```

5. In Terminal B, from the same repository root, download the model once:

   ```bash
   bash scripts/ollama.sh pull qwen3:1.7b
   ```

6. Verify a local terminal response, with thinking disabled:

   ```bash
   bash scripts/ollama.sh run qwen3:1.7b --think=false --verbose \
     'Say hello in one short sentence.'
   ```

7. Verify Python tools:

   ```bash
   uv run --locked python -c 'import streamlit, ollama, sqlite3; print("Imports OK")'
   uv pip check
   uv run --locked streamlit version
   uv run --locked pytest --version
   uv run --locked ruff --version
   ```

No application tests exist yet; `pytest --version` verifies the tool, not an
application test suite. `uv run` selects `.venv` automatically; manual activation
is optional. `sqlite3` comes with Python and needs no separate pip package.

## Daily use and shutdown

Start Terminal A with `bash scripts/ollama.sh serve`, and use `uv run --locked`
for Python work in Terminal B. Use the wrapper for all Ollama commands so both
terminals share the same model directory and server address. It intentionally
does not change your global shell PATH or install into `/Applications`.

Stop the server with Ctrl+C in Terminal A. To release a loaded model while
leaving the server running, use `bash scripts/ollama.sh stop qwen3:1.7b`.
`bash scripts/ollama.sh ps` shows currently loaded models.

## Storage and reproducibility

| Location | Purpose | Commit? |
|---|---|---|
| `.python-version`, `pyproject.toml`, `uv.lock` | Python version and dependency definition | Yes |
| `scripts/` | Reproducible setup and local Ollama command wrapper | Yes |
| `docs/environment_setup.md`, `docs/environment_validation.md`, `model_manifest.json` | Instructions, verification evidence, model identity | Yes |
| `.venv/` | Main project environment | No |
| `.cache/uv/` | Project-local dependency cache | No |
| `.cache/repro-venv/` | Separate environment used to verify lockfile recreation | No |
| `.tools/` | Pinned Ollama executable/archive and local diagnostic logs | No |
| `.models/ollama/` | Downloaded model weights and registry manifests | No |
| `~/.ollama/` | Ollama-managed identity files outside the repo | No |

Ollama itself creates `~/.ollama` identity files on first launch. The wrapper
does not override your home directory. Model weights are redirected to the
project through `OLLAMA_MODELS`. Local cloud inference/web search are disabled
with `OLLAMA_NO_CLOUD=1`; model downloads still use the network.

The Ollama archive version and checksum are pinned in `scripts/setup.sh`.
The model's observed full digest is recorded in `model_manifest.json` because
registry tags can change. After a fresh pull, compare `/api/tags` with that
manifest; a different digest is a model change requiring revalidation. The
manifest records identity but does not guarantee an old registry artifact will
remain downloadable forever. Preserve the local model cache for the demo.

Do not run `uv lock --upgrade` during normal setup. Make dependency upgrades
deliberately, review `uv.lock`, and rerun the import checks. Commit the lockfile
alongside `pyproject.toml`. Do not commit model weights or private recordings.

## Troubleshooting

- **Cannot connect to Ollama:** start Terminal A first. The Python client and
  model commands need a running server.
- **Port already in use:** identify the existing listener before starting
  another server. Do not kill unrelated processes. Confirm the intended model
  cache/settings rather than connecting to an unknown server instance.
- **Model missing:** rerun the pull using the wrapper and check
  `bash scripts/ollama.sh list`.
- **Checksum mismatch:** remove the failed archive as instructed by bootstrap,
  then retry. Do not skip verification.
- **No compatible wheel:** confirm the pinned interpreter and Intel
  architecture; do not switch to Apple Silicon/CUDA instructions.
- **Slow first reply:** model load and CPU inference can take seconds. This
  milestone proves operation, not the eventual two-second voice target.
- **No `app.py`:** expected. Application implementation begins in Milestone 1.

## Learning checkpoint

Explain why `.venv` is excluded from Git while `uv.lock` is committed; why the
Python Ollama client is separate from the running server; and how the same
repository can recreate its Python environment. Then proceed to the next
milestone: write your first small `ask_llm` function yourself.

## Sources

- [Ollama macOS requirements](https://docs.ollama.com/macos): Intel runs on CPU;
  the documented minimum is macOS 14.
- [Pinned Ollama release](https://github.com/ollama/ollama/releases/tag/v0.34.3)
- [uv project creation](https://docs.astral.sh/uv/concepts/projects/init/)
- [Qwen3-1.7B model card and Apache-2.0 license](https://huggingface.co/Qwen/Qwen3-1.7B)
