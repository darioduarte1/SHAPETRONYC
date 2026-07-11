#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Checking frontend..."
cd "$ROOT_DIR/frontend"
npm run lint
npm run build

echo "Checking backend..."
cd "$ROOT_DIR/backend"
if [ -x "venv/bin/python" ]; then
  PYTHON_BIN="venv/bin/python"
else
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" manage.py test exercises training progression accounts recommendations programs

echo "All checks passed."
