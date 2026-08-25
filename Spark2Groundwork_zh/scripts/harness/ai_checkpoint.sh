#!/usr/bin/env bash
# AI 檢查點 —— **薄殼，⛔ 這裡沒有邏輯**
#
# 全部邏輯在 scripts/harness/checkpoint.py，Windows 與 macOS 跑的是同一份程式碼。
# ⛔ 不要把邏輯抄回這裡：**同一件事有兩份拷貝**，正是本框架自己
#    「修一層漏另一層」事故的成因（見 governance/Incident_Log.md）。
#
# ⚠️ 保留這個檔名是因為 SETUP.md 與既有習慣都指向它。
cd "$(dirname "$0")/../.." || exit 1
PY=""; command -v python3 >/dev/null 2>&1 && PY=python3
[ -z "$PY" ] && command -v python >/dev/null 2>&1 && PY=python
[ -z "$PY" ] && { echo "[FAIL] 找不到 Python 3.9+"; exit 1; }
exec "$PY" scripts/harness/checkpoint.py --mode ai "$@"
