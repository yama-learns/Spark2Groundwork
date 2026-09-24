#!/bin/bash
# A thin check button. No install, chmod, quarantine clearing or research writes.
cd "$(dirname "$0")" || exit 2
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--no-pause" ]; }; then
  echo "[INCOMPLETE] Unsupported button arguments."
  exit 2
fi
PY=""
probe() {
  [ -n "$PY" ] && return
  [ -x "$1" ] || return
  "$1" -I -B -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 2)' >/dev/null 2>&1 && PY="$1"
}
probe /Library/Frameworks/Python.framework/Versions/Current/bin/python3
probe /opt/homebrew/bin/python3
probe /usr/local/bin/python3
candidate=$(command -v python3 || true)
if [ "$candidate" = /usr/bin/python3 ]; then
  /usr/bin/xcode-select -p >/dev/null 2>&1 && probe "$candidate"
else
  [ -n "$candidate" ] && probe "$candidate"
fi
if [ -z "$PY" ]; then
  echo '[INCOMPLETE] Python 3.9+ was not found. See docs/START_HERE.html.'
  /usr/bin/open "docs/START_HERE.html"
  RC=2
else
  "$PY" -I -B "scripts/harness/check_environment.py" --lang en --action sync
  RC=$?
fi
printf '\nResult code: %s (0=PASS, 1=FAIL, 2=INCOMPLETE)\n' "$RC"
printf 'Press Return to close. '
if [ "${1:-}" != "--no-pause" ]; then read -r _; fi
exit "$RC"
