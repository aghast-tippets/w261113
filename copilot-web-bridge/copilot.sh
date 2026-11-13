#!/usr/bin/env bash
# Start a terminal chat with Microsoft 365 Copilot (no Claude needed).
#   ./copilot.sh [conversation-url]
cd "$(dirname "$0")" || exit 1
[[ -x .venv/Scripts/python.exe ]] || { echo "Run ./setup-msys2.sh first." >&2; exit 1; }
exec .venv/Scripts/python.exe -u chat.py "$@"
