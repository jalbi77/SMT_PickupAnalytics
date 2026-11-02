#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -f .venv/Scripts/python.exe ]]; then
    python_path=.venv/Scripts/python.exe
elif [[ -x .venv/bin/python ]]; then
    python_path=.venv/bin/python
else
    printf '%s\n' 'Python-Umgebung fehlt. Bitte die Installation in README.md ausführen.' >&2
    exit 1
fi
exec "$python_path" -m streamlit run main.py "$@"
