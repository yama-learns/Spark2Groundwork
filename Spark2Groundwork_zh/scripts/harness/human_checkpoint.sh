#!/usr/bin/env bash
# 人工檢查點（macOS／Linux）—— 與 記錄快照.bat 對稱
# ⚠️ 兩側修改時必須同步：提交訊息格式、reviewed 標籤行為、鎖檔處理。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT" || exit 1
[[ -f governance/AGENTS.md ]] || { echo "[FAIL] 這不是專案根目錄，未寫入任何東西"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "建立版本控制…"; git init -q; }
[[ -z "$(git rev-parse --show-prefix 2>/dev/null)" ]] || { echo "[FAIL] 此資料夾位於另一個 repo 之內"; exit 1; }
find .git -name "*.lock" -delete 2>/dev/null
GITQ=(git -c core.quotepath=false)
"${GITQ[@]}" --no-pager diff --stat --summary HEAD 2>/dev/null | tail -20
"${GITQ[@]}" add -A
if git diff --cached --quiet 2>/dev/null; then echo "無變更"; else
  git -c user.name="researcher" -c user.email="me@local" commit -q -m "snapshot $(date '+%Y-%m-%d %H:%M')"
  echo "New checkpoint created."; fi
git tag -f reviewed >/dev/null 2>&1
echo "Done. Reviewed baseline moved to the latest checkpoint."
