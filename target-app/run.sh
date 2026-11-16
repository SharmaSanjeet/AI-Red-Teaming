#!/usr/bin/env bash
# Start the Nova training target on http://localhost:8000
# Usage:
#   ./run.sh                 # unhardened (vulnerable) — Labs 1-5, 7-8
#   SAMR_HARDENED=1 ./run.sh   # hardened — Lab 6 re-verify / before-after
#
# The app falls back to a deterministic STUB LLM if Ollama is unreachable,
# so it runs fully offline with no paid APIs.
set -euo pipefail
cd "$(dirname "$0")"
exec uvicorn app:app --host 127.0.0.1 --port 8000 --reload
