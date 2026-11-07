#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -x "$project_dir/.venv/bin/fcu-desktop" ]]; then
    echo "Install first: python3 -m venv .venv && .venv/bin/python -m pip install -e ." >&2
    exit 1
fi
export PATH="$project_dir/.venv/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PYTHONUNBUFFERED=1
if [[ $# -eq 0 ]]; then set -- clock; fi
exec "$project_dir/.venv/bin/fcu-desktop" "$@"
