#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：框架套件是不是同一個版本

## 為什麼需要這一支

🔴 **升級是一次換一包的，⛔ 而「換到一半」不會產生任何錯誤訊息。**

⚠️ **實測個案（專案 D，2026-08-31）：** `governance/`、`profiles/`、`docs/` 已經是 v1.4.2，
而 `policy/` 還停在 v1.3.0。**專案看起來是好的：感測器全綠、自測全過。**
⛔ **⚠️ 沒有任何一支感測器在看「這幾包是不是同一版」，
所以那個狀態是靜默的——⛔ 而它是靠一次外部稽核才被發現的。**

## ⛔ 它不宣稱的事

⛔ **版本字串只回答「這個資料夾自稱哪一版」，⛔ 它⛔ 不證明內容完整。**
⚠️ **同一個專案 D 還有另一半：`prompts/_VERSION` 寫 v1.4.2，
而 `prompts/_COMMON_BLOCKS.md` 的內容仍是 v1.3.0。**
🔴 **⇒ 本感測器抓得到「自稱不一致」，⛔ 抓不到「自稱一致而內容不同」。**
**那件事的規定動作是 `upgrade.py diff`，⛔ 不是這一支。寫在這裡，不留白。**

## 三項檢查

    VERSION_MISMATCH      套件之間版本不同（＝升級只換了一半）      FAIL
    VERSION_UNREADABLE    套件在，⛔ 而 `_VERSION` 讀不到           INCOMPLETE
    PACKAGE_ABSENT        這個專案沒有這一包                        WARN

⚠️ **`PACKAGE_ABSENT` 是 `WARN` ⛔ 不是 `FAIL`：**
**一個專案可以合法地沒有某一包**（例如從舊版升上來、`docs/` 尚未補），
🔴 **⛔ 而「你少了一包」與「你的兩包版本不同」是兩件事，處置也不同。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402


def read_version(p):
    """只取第一個非註解、非空白的行。

    ⚠️ **與 `upgrade.py::read_version()` 同一套規則。**
    ⛔ **兩份實作若不同，本感測器與升級工具會對同一個檔案報不同的版本**——
    🔴 **而那正是本感測器要抓的那種東西發生在它自己身上（憲章 §3.2）。**
    """
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                return s
    except Exception:                                       # noqa: BLE001
        return None
    return None


def survey(root, cfg):
    """回傳 (每包的版本, 缺包, 讀不到的包)。⛔ 三者都要有分母（`R-35`）。"""
    pkgs = cfg.get("version_packages",
                   ["governance", "profiles", "prompts", "scripts", "docs"])
    fname = cfg.get("version_file", "_VERSION")
    found, absent, unreadable = {}, [], []
    for name in pkgs:
        d = root / name
        if not d.is_dir():
            absent.append(name)
            continue
        v = read_version(d / fname)
        if v is None:
            unreadable.append(name)
        else:
            found[name] = v
    return found, absent, unreadable


def main():
    root, cfg, as_json, name = cli("version_consistency")
    findings, stats = [], {}
    found, absent, unreadable = survey(root, cfg)

    stats["套件"] = len(found) + len(absent) + len(unreadable)
    stats["讀到版本"] = len(found)

    for pkg in absent:
        findings.append(("WARN", "PACKAGE_ABSENT",
                         f"這個專案沒有 `{pkg}/`——"
                         "**⚠️ 舊版升上來時可能沒有這一包；"
                         "跑 `upgrade.py apply " + pkg + "` 可以補回**"))
    for pkg in unreadable:
        findings.append(("INCOMPLETE", "VERSION_UNREADABLE",
                         f"`{pkg}/` 在，⛔ 而它的版本標記讀不到"
                         "——**⛔ 這一包本輪未比對，而那不等於它是對的**"))

    versions = set(found.values())
    if len(versions) > 1:
        rows = "、".join(f"{k}={v}" for k, v in sorted(found.items()))
        # 🔴 **⛔ 這裡刻意⛔ 不宣稱「哪一版最新」（裁決 `A4b: B`，2026-09-02）。**
        #    ⚠️ **舊版寫 `sorted(versions)[-1]`，那是字串排序**——
        #    **實測 `{v1.9.0, v1.10.0}` 會選出 `v1.9.0`，⛔ 而那是比較舊的那一版。**
        #    🔴 **更根本的理由：本感測器看不到 `_upgrade/`，⛔ 所以它沒有能力知道目標版本。**
        #    **「該補到哪一版」的權威源是升級來源，那是 `upgrade.py diff` 的職權（`R-34`）。**
        findings.append(("FAIL", "VERSION_MISMATCH",
                         f"框架套件不是同一版：{rows}"
                         "——🔴 **升級只換了一半。**"
                         "**跑 `upgrade.py diff` 看新版來源是哪一版，再一次補一包**"
                         "（⛔ 本感測器看不到升級來源，所以⛔ 不替你判斷該補到哪一版）"))
        stats["🔴 不同版本"] = len(versions)
    elif versions:
        stats["版本"] = versions.pop()

    if not found:
        findings.append(("INCOMPLETE", "VERSION_UNREADABLE",
                         "一個框架套件的版本都讀不到——**⛔ 本項查不了，⛔ 不是通過**"))
    return emit("版本一致性感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
