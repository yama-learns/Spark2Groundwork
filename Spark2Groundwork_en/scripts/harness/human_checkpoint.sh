#!/usr/bin/env bash
# Human checkpoint — **a thin shell; ⛔ no logic lives here**
#
# All the logic is in scripts/harness/checkpoint.py, so Windows and macOS run
# exactly the same code.
# ⛔ Do not copy logic back into here: **two copies of one thing** is precisely
#    how this framework's own "fixed one layer, missed another" incidents happened
#    (see governance/Incident_Log.md).
#
# ⚠️ The filename is kept because SETUP.md and existing habits point at it.
cd "$(dirname "$0")/../.." || exit 1
PY=""; command -v python3 >/dev/null 2>&1 && PY=python3
[ -z "$PY" ] && command -v python >/dev/null 2>&1 && PY=python
[ -z "$PY" ] && { echo "[FAIL] Python 3.9+ not found"; exit 1; }
exec "$PY" scripts/harness/checkpoint.py  "$@"
