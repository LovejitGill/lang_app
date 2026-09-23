#!/usr/bin/env bash
# Run the project-local Ollama CLI with the same settings in every terminal.
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS="$project_root/.models/ollama"
export OLLAMA_NO_CLOUD=1
export OLLAMA_NOHISTORY=1
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_NUM_PARALLEL=1
if [[ ! -x "$project_root/.tools/ollama/ollama" ]]; then
    echo 'Run bash scripts/setup.sh first.' >&2
    exit 1
fi
exec "$project_root/.tools/ollama/ollama" "$@"
