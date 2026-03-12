#!/usr/bin/env bash
set -euo pipefail

# Reproducible local setup for this project.
# - Uses Python 3.12 in a virtual environment (works even when system python3.12 has no pip module).
# - Attempts dependency installation from normal pip index.
# - If outbound access is restricted, allows optional custom index via PIP_INDEX_URL.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN not found. Install Python 3.12 or set PYTHON_BIN." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip

if ! python -m pip install -r requirements.txt; then
  cat >&2 <<'MSG'
ERROR: dependency installation failed.

If your environment uses a restricted network/proxy, set a reachable package index and retry:
  PIP_INDEX_URL=http://<your-internal-pypi>/simple \
  python -m pip install --trusted-host <your-internal-pypi-host> -r requirements.txt

Or export PIP_INDEX_URL before running this script.
MSG
  exit 1
fi

python -m compileall app

echo "Setup and checks completed successfully."
