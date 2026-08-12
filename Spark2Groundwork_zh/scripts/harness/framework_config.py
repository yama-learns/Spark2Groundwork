#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""框架設定 —— **所有感測器的唯一設定來源**。

## 為什麼設定要集中在一個檔案

兩個先行專案的感測器都把路徑硬編在各自的檔案裡。後果：
**改一個資料夾名稱要改五支程式，而漏改的那一支不會報錯——它只是靜靜地什麼都不掃。**

⚠️ 實測個案（`Incident_Log.md` 家族④）：某專案的掃描清單中有兩個
**從建立起就命中 0 個檔案**的 glob——一個因為目錄被搬走、一個因為名稱少了一個 s。
**看起來在保護什麼，其實沒有。**

→ 因此本檔除了集中設定，還要求每支感測器**回報命中 0 個檔案的 glob**。

## 怎麼改

**只改本檔。** 改完跑一次 `run_selftest.py` 確認沒改壞。
⛔ 不要在個別感測器裡另外硬編路徑。
"""

import json
import pathlib

# ── 專案根目錄 ────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[2]

# ── 使用者可覆寫：專案根目錄放一個 governance_config.json 即可 ──
_USER = ROOT / "governance_config.json"

DEFAULTS = {
    # T0 必讀法：全專案各只有一份，子資料夾不得存放副本
    "t0_docs": ["governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"],

    # 治理文件（規則的家）——供跨檔重複與章節引用檢查使用
    # ⚠️ 這是 **glob**，不是硬編清單（R-21：白名單會靜默過濾）
    "governance_globs": ["governance/*.md", "policy/*.md", "ledgers/*.md", "file_index.md"],

    # 台帳
    "conjecture_ledger": "ledgers/Conjecture_Ledger.md",
    "claim_ledger": "ledgers/Claim_Ledger.md",

    # 語料庫：程式化提取的全文，錨點比對的對象
    # ⛔ 提取物不得手工編輯（R-14）
    "corpus_dir": "corpus_md",
    "corpus_manifest": "corpus_md/_manifest.json",

    # 產出物：會被下游引用者，受自我背書檢查
    "artifact_globs": ["handoffs/*.md", "outputs/*.md", "reports/*.md"],

    # 掃描時一律排除（⚠️ 以**相對於 root 的路徑**判定，見 R-18）
    "excluded_dirs": ["archive", ".git", "__pycache__", "selftest", "scratch",
                      "node_modules", ".venv"],

    # 多角色專案才需要：各角色的寫入範圍
    # 單 agent 專案請留空 {}，感測器會自動略過該項檢查
    "write_scopes": {},

    # 選用功能開關
    "enable_reference_authenticity": False,   # 需連網查 Crossref
    "enable_bat_checks": False,               # 僅 Windows 使用批次檔時開啟
}


def load():
    """讀設定。使用者檔存在時覆寫預設值（淺層合併）。"""
    cfg = dict(DEFAULTS)
    if _USER.exists():
        try:
            cfg.update(json.loads(_USER.read_text(encoding="utf-8")))
        except Exception as e:                       # noqa: BLE001
            # ⛔ 不得靜默忽略：設定壞掉而感測器照跑，等於在錯誤的範圍上宣告通過
            raise SystemExit(f"[FAIL] governance_config.json 無法解析：{e}")
    return cfg


def excluded(path, root, cfg):
    """路徑是否落在排除清單內。

    ⚠️ **必須用相對路徑**（R-18）。兩個先行專案各踩過一次：
    以絕對路徑的 parts 比對，會把測試樣本目錄下的每一個檔案都排除，
    **造成自測全綠或全紅**，而兩種都看不出是排除邏輯的問題。
    """
    try:
        parts = set(pathlib.Path(path).resolve().relative_to(root).parts)
    except ValueError:
        return True
    return bool(parts & set(cfg["excluded_dirs"]))


def resolve_globs(globs, root, cfg):
    """展開 glob 並回報命中 0 個檔案者。

    回傳 (檔案清單, 死 glob 清單)。
    ⚠️ **死 glob 必須被回報**——它與死豁免同型：看起來在保護什麼，其實沒有。
    """
    files, dead = [], []
    for g in globs:
        hit = [p for p in root.glob(g) if p.is_file() and not excluded(p, root, cfg)]
        if not hit:
            dead.append(g)
        files.extend(hit)
    return sorted(set(files)), dead
