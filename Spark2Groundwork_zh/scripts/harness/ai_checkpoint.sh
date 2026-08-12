#!/usr/bin/env bash
# AI 檢查點 —— 標 auto: 且**不移動** reviewed 標籤
# ⚠️ 「AI 自己存的檔不算你看過」，這個區分是刻意的。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT" || exit 1
LABEL="${1:-unlabelled}"
[[ -f governance/AGENTS.md ]] || { echo "[FAIL] 這不是專案根目錄"; exit 1; }
[[ -z "$(git rev-parse --show-prefix 2>/dev/null)" ]] || { echo "[FAIL] 位於另一個 repo 之內"; exit 1; }
find .git -name "*.lock" -delete 2>/dev/null
git -c core.quotepath=false add -A
git diff --cached --quiet 2>/dev/null && { echo "無變更"; exit 0; }
git -c user.name="AI agent" -c user.email="agent@local" commit -q \
  -m "auto: $(date '+%Y-%m-%d %H:%M') [$LABEL] -- AI auto checkpoint, NOT human-reviewed"
echo "  ✅ 已建立 AI 檢查點"
echo "  ⛔ reviewed 標籤**未移動**——AI 自己存的檔不算你看過"
