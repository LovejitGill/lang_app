#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
JAVA_BIN="$PROJECT_DIR/.tools/benchmark/jdk-21.0.12.1+1-jre/Contents/Home/bin/java"
LT_DIR="$PROJECT_DIR/.tools/benchmark/LanguageTool-6.6"
if [[ ! -x "$JAVA_BIN" || ! -f "$LT_DIR/languagetool-server.jar" ]]; then
  echo 'Run uv run python scripts/setup_benchmark.py first.' >&2
  exit 1
fi
cd "$LT_DIR"
# No --public or browser CORS flag: Python connects only through loopback.
exec "$JAVA_BIN" -Xmx1g -cp languagetool-server.jar org.languagetool.server.HTTPServer --port 8081
