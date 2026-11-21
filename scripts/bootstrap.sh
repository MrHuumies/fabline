#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x ".tools/uv" ]; then
  mkdir -p .tools
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$ROOT/.tools" sh
fi

if [ ! -x ".venv/bin/python" ]; then
  .tools/uv venv --clear --python 3.12 .venv
fi

.tools/uv pip install --python .venv/bin/python -e ".[dev]"

echo "bootstrap complete: $ROOT/.venv"
