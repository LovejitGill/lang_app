#!/usr/bin/env bash
# Bootstrap only the environment; this does not create application code.
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
if [[ "$(uname -s)" != Darwin ]]; then
    echo 'This bootstrap is for the documented macOS environment.' >&2
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
uv sync --locked

# Pin and verify the official universal macOS archive before extracting it.
ollama_version=0.34.3
archive=.tools/downloads/ollama-darwin.tgz
expected_sha=2c45865f94bce0d4d1d2567603dd2fdacaf375585220a175aa4800105193d36e
mkdir -p .tools/downloads .tools/ollama
if [[ ! -f "$archive" ]]; then
    curl -fL --retry 2 \
        "https://github.com/ollama/ollama/releases/download/v${ollama_version}/ollama-darwin.tgz" \
        -o "$archive.partial"
    mv "$archive.partial" "$archive"
fi
actual_sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
    echo "Checksum mismatch: remove $archive and rerun setup." >&2
    exit 1
fi
tar -xzf "$archive" -C .tools/ollama
uv run --locked python -c 'import streamlit, ollama, sqlite3; print("Environment imports OK")'
echo 'Next: bash scripts/ollama.sh serve (leave that terminal open).'
echo 'Then, in another terminal: bash scripts/ollama.sh pull qwen3:1.7b'
