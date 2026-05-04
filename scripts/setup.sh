#!/usr/bin/env bash
# One-shot setup: creates .venv, installs deps including Apple's SHARP.
# Re-run safely; it will skip steps that are already done.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install with: brew install uv  (or https://docs.astral.sh/uv/)"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "==> Creating Python 3.13 virtualenv at .venv/"
  uv venv --python 3.13 .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dependencies (this pulls torch + ml-sharp; ~2 GB)"
uv pip install -r requirements.txt

echo
echo "Setup complete."
echo "Activate the venv:    source .venv/bin/activate"
echo "Then run the app:     python server.py"
echo "Open:                 http://localhost:8765"
echo
echo "First upload triggers a one-time 2.6 GB checkpoint download from Apple's CDN."
