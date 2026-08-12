#!/usr/bin/env bash
# Human checkpoint (macOS/Linux) — mirror of snapshot.bat
# ⚠️ Keep both sides in sync: commit message format, reviewed-tag behaviour, lock handling.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT" || exit 1
[[ -f governance/AGENTS.md ]] || { echo "[FAIL] not the project root; nothing was written"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "initialising version control..."; git init -q; }
[[ -z "$(git rev-parse --show-prefix 2>/dev/null)" ]] || { echo "[FAIL] this folder sits inside another repository"; exit 1; }
find .git -name "*.lock" -delete 2>/dev/null
GITQ=(git -c core.quotepath=false)
"${GITQ[@]}" --no-pager diff --stat --summary HEAD 2>/dev/null | tail -20
"${GITQ[@]}" add -A
if git diff --cached --quiet 2>/dev/null; then echo "no changes"; else
  git -c user.name="researcher" -c user.email="me@local" commit -q -m "snapshot $(date '+%Y-%m-%d %H:%M')"
  echo "New checkpoint created."; fi
git tag -f reviewed >/dev/null 2>&1
echo "Done. Reviewed baseline moved to the latest checkpoint."
