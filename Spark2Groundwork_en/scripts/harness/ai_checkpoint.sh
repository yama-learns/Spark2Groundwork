#!/usr/bin/env bash
# AI checkpoint — tags auto: and does **not** move the reviewed tag
# ⚠️ "What the AI saved is not what you reviewed" — the distinction is deliberate.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT" || exit 1
LABEL="${1:-unlabelled}"
[[ -f governance/AGENTS.md ]] || { echo "[FAIL] not the project root"; exit 1; }
[[ -z "$(git rev-parse --show-prefix 2>/dev/null)" ]] || { echo "[FAIL] sits inside another repository"; exit 1; }
find .git -name "*.lock" -delete 2>/dev/null
git -c core.quotepath=false add -A
git diff --cached --quiet 2>/dev/null && { echo "no changes"; exit 0; }
git -c user.name="AI agent" -c user.email="agent@local" commit -q \
  -m "auto: $(date '+%Y-%m-%d %H:%M') [$LABEL] -- AI auto checkpoint, NOT human-reviewed"
echo "  AI checkpoint created"
echo "  reviewed tag NOT moved -- what the AI saved is not what you reviewed"
