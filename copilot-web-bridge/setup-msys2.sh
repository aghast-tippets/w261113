#!/usr/bin/env bash
# Set up the copilot-web MCP bridge from an MSYS2 UCRT64 (or Git Bash) shell on Windows.
#
#   ./setup-msys2.sh              # create .venv and install dependencies
#   ./setup-msys2.sh --register   # ...and register the server with Claude Code (user scope)
#
# Env overrides:
#   PYTHON=/c/path/to/python.exe   native Windows Python to use (3.10+)
#   COPILOT_BROWSER_CHANNEL=msedge|chrome|chromium   (default msedge)
#
# Why not MSYS2's own python (mingw-w64-ucrt-x86_64-python)? pip reports its platform as
# mingw_x86_64_ucrt, so there are no wheels for playwright, greenlet or pydantic-core and
# installs fail. The venv must be built with a native Windows CPython (python.org, winget, uv).
set -euo pipefail
cd "$(dirname "$0")"

CHANNEL="${COPILOT_BROWSER_CHANNEL:-msedge}"
REGISTER=0
[[ "${1:-}" == "--register" ]] && REGISTER=1

die() { echo "error: $*" >&2; exit 1; }

# Prints the sysconfig platform of a python command, or nothing if it doesn't run.
platform_of() { "$@" -c 'import sysconfig; print(sysconfig.get_platform())' 2>/dev/null | tr -d '\r' || true; }
version_ok() { "$@" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; }

candidates=()
[[ -n "${PYTHON:-}" ]] && candidates+=("$PYTHON")
command -v py >/dev/null 2>&1 && candidates+=("py -3")
[[ -x /c/Windows/py.exe ]] && candidates+=("/c/Windows/py.exe -3")
if [[ -n "${LOCALAPPDATA:-}" ]]; then
  la="$(cygpath -u "$LOCALAPPDATA")"
  [[ -x "$la/Programs/Python/Launcher/py.exe" ]] && candidates+=("$la/Programs/Python/Launcher/py.exe -3")
  for p in "$la"/Programs/Python/Python3*/python.exe; do [[ -x "$p" ]] && candidates+=("$p"); done
fi
command -v python >/dev/null 2>&1 && candidates+=("python")

PY=()
for c in "${candidates[@]}"; do
  read -r -a cmd <<<"$c"
  plat="$(platform_of "${cmd[@]}")"
  if [[ "$plat" == win-* ]] && version_ok "${cmd[@]}"; then PY=("${cmd[@]}"); break; fi
  [[ -n "$plat" ]] && echo "skipping '$c' (platform $plat)" >&2
done
[[ ${#PY[@]} -gt 0 ]] || die "no native Windows Python 3.10+ found.
  Install one (e.g. in PowerShell: winget install Python.Python.3.12), then re-run,
  or point at it: PYTHON=/c/Users/you/AppData/Local/Programs/Python/Python312/python.exe $0"
echo "using Python: ${PY[*]} ($("${PY[@]}" --version 2>&1 | tr -d '\r'))"

[[ -x .venv/Scripts/python.exe ]] || "${PY[@]}" -m venv .venv
VPY=".venv/Scripts/python.exe"
[[ -x "$VPY" ]] || die "venv creation failed: $VPY missing"

"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt
if [[ "$CHANNEL" == "chromium" ]]; then
  "$VPY" -m playwright install chromium
fi

# Quick import check (no browser launch).
"$VPY" -c "import mcp, playwright; print('imports ok')"

WIN_PY="$(cygpath -w "$PWD/$VPY")"
WIN_SERVER="$(cygpath -w "$PWD/server.py")"
CMD=(claude mcp add --env "COPILOT_BROWSER_CHANNEL=$CHANNEL" --scope user --transport stdio
     copilot-web -- "$WIN_PY" "$WIN_SERVER")

if [[ $REGISTER -eq 1 ]]; then
  command -v claude >/dev/null 2>&1 || die "claude not on PATH in this shell; run the command below from wherever you run Claude Code."
  claude mcp remove --scope user copilot-web >/dev/null 2>&1 || true
  "${CMD[@]}"
  echo "registered. Start Claude Code and run /mcp to confirm 'copilot-web' is connected."
else
  echo
  echo "Register with Claude Code (run where 'claude' is available):"
  printf '  %q' "${CMD[@]}"; echo
  echo
  echo "PowerShell equivalent:"
  echo "  claude mcp add --env COPILOT_BROWSER_CHANNEL=$CHANNEL --scope user --transport stdio copilot-web -- \"$WIN_PY\" \"$WIN_SERVER\""
fi
