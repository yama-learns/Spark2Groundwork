#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：T0 唯一性與寫入範圍

## 兩項檢查

    T0_DUPLICATE_IN_SUBDIR   子資料夾出現與 T0 同名的檔案            FAIL
    WRITE_OUT_OF_SCOPE       本輪變更落在宣告範圍之外                FAIL

⚠️ **T0 唯一性為什麼是 FAIL 而非 WARN：**
**改一份漏其餘，而每一份單獨讀起來都正常。** 這是「修一層漏另一層」家族最難察覺的形態。

⚠️ **單 agent 專案請把 `write_scopes` 留空**——感測器會明說「本項不適用」，
**而不是靜默通過**。

## 兩個踩過的坑（**都寫在這裡是因為它們會再發生**）

1. `git rev-parse --show-toplevel` 必須等於專案根目錄。
   否則當專案位於另一個 repo 之內時，**會對著錯誤的 repo 回報，而且語氣非常肯定**。
2. `git -c core.quotepath=false`。否則非 ASCII 路徑會印成八進位轉義，
   **「哪個檔案改了」這個唯一需要讀的欄位會變成一串數字。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from framework_config import excluded                      # noqa: E402


def git_changed(root):
    """本輪變更清單。回傳 (清單, 錯誤訊息)。"""
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=20)
        if top.returncode != 0:
            return None, "尚未建立版本控制"
        if pathlib.Path(top.stdout.strip()).resolve() != root.resolve():
            # ⛔ 這一步不能省。見檔頭坑 1。
            return None, "專案位於另一個 repo 之內——**拒絕回報，以免對著錯誤的 repo 下判定**"
        r = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false",
                            "status", "--porcelain"],
                           capture_output=True, text=True, timeout=20)
        return [ln[3:].strip().strip('"') for ln in r.stdout.splitlines() if ln.strip()], None
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git 無法執行：{e}"


def main():
    root, cfg, as_json, name = cli("scope_and_t0")
    findings = []

    # ① T0 唯一性
    t0_names = {pathlib.Path(t).name for t in cfg["t0_docs"]}
    t0_paths = {(root / t).resolve() for t in cfg["t0_docs"]}
    for p in root.rglob("*.md"):
        if excluded(p, root, cfg) or p.resolve() in t0_paths:
            continue
        if p.name in t0_names:
            findings.append(("FAIL", "T0_DUPLICATE_IN_SUBDIR",
                             f"{p.relative_to(root)} — T0 全專案各只有一份。"
                             "**改一份漏其餘，而每一份單獨讀起來都正常**"))

    # ② 寫入範圍
    scopes = cfg.get("write_scopes") or {}
    stats = {"T0 份數": len(cfg["t0_docs"])}
    if not scopes:
        stats["寫入範圍"] = "未設定 write_scopes，本項不適用（⚠️ 不適用 ≠ 通過）"
    else:
        changed, err = git_changed(root)
        if changed is None:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{err}——**本項未檢查，這不等於通過**"))
        else:
            allowed = [a.rstrip("/") for v in scopes.values() for a in v]
            # 🔴 **deny：無論任何角色都不得寫。**（憲章 §6 通則 2 第一次有機械對應物）
            #    ⚠️ T0 兩份自 `t0_docs` 併入——⛔ 不在 `deny` 裡重寫一次（憲章 §3.2）。
            denied = ([d.rstrip("/") for d in cfg.get("deny", [])]
                      + [t.rstrip("/") for t in cfg["t0_docs"]])
            # ⚠️ `_human` 不是角色，是例外。**它的代價寫在 framework_config 裡，
            #    而這裡的責任是：⛔ 被豁免的筆數必須被印出來。**
            #    靜默豁免與沒有豁免，在畫面上長得一樣（「靜默過濾」家族）。
            human = [h.rstrip("/") for h in scopes.get("_human", [])]

            def under(path, tops):
                return any(path == a or path.startswith(a + "/") for a in tops)

            exempted = 0
            for c in changed:
                if under(c, denied):
                    if under(c, human):
                        exempted += 1
                        continue
                    findings.append(("FAIL", "WRITE_TO_DENIED_PATH",
                                     f"{c} 落在 deny 範圍內——**⛔ 任何 AI 角色皆不得寫**"
                                     f"（憲章 §6 通則 2）"))
                    continue
                if not under(c, allowed):
                    findings.append(("FAIL", "WRITE_OUT_OF_SCOPE",
                                     f"{c} 不在任何角色的宣告範圍內"))
            stats["本輪變更"] = len(changed)
            stats["deny 範圍"] = len(denied)
            if exempted:
                stats["⚠️ 經 _human 豁免的 deny 命中"] = (
                    f"{exempted} 筆——**豁免不是沒有發生，只是判定為人做的**")

    return emit("範圍與 T0 感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
