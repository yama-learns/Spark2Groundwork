#!/bin/bash
# ===========================================================
#  Framework upgrade: check / diff / apply
#
#  This file is a BUTTON, not the program. All the logic lives
#  in scripts/harness/upgrade.py so that macOS and Windows run
#  exactly the same code. Do not copy logic back into here:
#  two copies of one thing is how this framework's own
#  "fixed one layer, missed another" incidents happened.
#
#  ⚠️ If double-clicking does nothing, this file may have lost its
#     executable bit (that happens when the project arrives as a
#     downloaded .zip rather than a git clone). In Terminal, run:
#         chmod +x "<this file>"
#     and if macOS says the file is "from the internet":
#         xattr -dr com.apple.quarantine "<this project folder>"
# ===========================================================
cd "$(dirname "$0")" || exit 1

PY=""
command -v python3 >/dev/null 2>&1 && PY=python3
[ -z "$PY" ] && command -v python >/dev/null 2>&1 && PY=python

if [ -z "$PY" ]; then
  echo
  echo "[FAIL] Python was not found on this computer."
  echo
  echo "  This framework needs Python 3.9 or newer."
  echo "  macOS: open Terminal and run   xcode-select --install"
  echo "  or install from https://www.python.org/downloads/"
  echo
  echo "  Nothing was changed."
  echo
  printf "Press Return to close this window. "
  read -r _
  exit 1
fi

if [ "$#" -eq 0 ]; then
  "$PY" "scripts/harness/upgrade.py" check
  RC=$?
  if [ -d "_upgrade" ]; then
    echo
    "$PY" "scripts/harness/upgrade.py" diff
    DIFF_RC=$?
    [ "$DIFF_RC" -ne 0 ] && RC=$DIFF_RC
  fi
else
  "$PY" "scripts/harness/upgrade.py" "$@"
  RC=$?
fi
echo
echo "==========================================================="
printf "Press Return to close this window. "
read -r _
exit "$RC"
