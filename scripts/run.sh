#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
make
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
exec python backend/app.py
