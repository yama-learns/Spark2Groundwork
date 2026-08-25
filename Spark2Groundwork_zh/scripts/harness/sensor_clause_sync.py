#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：條款清單同步——**被抄過去的那一份，還和定義處一樣嗎**

## 檢查

    SYNC_LIST_DRIFT     副本的清單與定義處不同（多了／少了項目）        FAIL
    SYNC_HOME_MISSING   定義處不存在，或定義處沒有這份清單              INCOMPLETE
    SYNC_NO_COPY        定義處有清單，但全專案找不到任何副本            WARN
    SCAN_GLOB_MATCHES_NOTHING / COVERAGE_COLLAPSE                       WARN / INCOMPLETE

## 為什麼需要它（**一個實測個案，兩條規則互斥的產物**）

`R-24` 要求每份 prompt **完全自足**——⛔ 不得寫「同上」「參見前述」。
於是一份審計 prompt **必須**把 `governance/Audit_Protocol.md` §3 的禁用詞清單抄一份進去。

而憲章 §3.2 要求**每條規則只有一個定義處**。

> 🔴 **兩者在此互斥，而互斥的結果就是漂移。**

**實測個案：** `prompts/TEMPLATE_adversarial.txt` 寫「非常**穩健**」，
而 `governance/Audit_Protocol.md` §3 寫「非常**強健**」。
**一個字的差別，使那份 prompt 的禁用清單少防一個詞，而兩份文件都讀起來完全正常。**
⚠️ **那是靠人逐字比對才發現的，而且是在做別的事情時順手看到的。**

## ⛔ 這支感測器**不**解決那個互斥，它只是讓漂移無法靜默

⚠️ **不要期待它取代裁決：** 哪一份是定義處、要不要抄，仍然是人的決定。
它只回答一個機械問題：**「抄過去的那一份，今天還和定義處一樣嗎？」**

## ⚠️ 判準是「集合相等」，⛔ 不是「逐字逐序相同」

裁決 18 的字面是「逐字一致」。**實作為集合相等，差異記在這裡：**
兩版的禁用清單**內容相同而順序不同**（英文版定義處是 `airtight` 在前，模板是 `airtight` 在後）。

> **順序在這份清單裡不承載任何意義，而對一個無意義的差異報 FAIL，
> 正是 `R-19` 說的那種會教人關掉感測器的誤報。**

⛔ **但每一個項目仍須逐字相同**——「非常穩健」與「非常強健」是兩個不同的項目，
集合相等當場不成立。**放寬的是順序，不是字。**

## 判準是結構，不是檔名

⛔ **本感測器不含任何硬編的副本檔名清單。**
它掃 `sync_scan_globs`，把**每一行帶有標記的清單**都當成副本，
定義處由 `synced_lists[].home` 指定（⚠️ 那是一個**指標**，不是掃描範圍，故不違反 `R-21`）。
**加一份新模板不需要改這支感測器；漏改的那一份會自己現形。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（**⛔ 未完成 ≠ 通過**）
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import resolve_globs                   # noqa: E402

# 引號內的項目：中文「」、英文直/彎引號皆可
TERM = re.compile(r"「([^」]+)」|“([^”]+)”|\"([^\"]+)\"")


def terms_on(line):
    """取出該行引號內的所有項目（⛔ 逐字，不做任何正規化）。"""
    out = []
    for m in TERM.finditer(line):
        out.append(next(g for g in m.groups() if g is not None))
    return out


def find_list(text, marker):
    """回傳 (行號, 項目集合)；找不到標記回傳 (None, None)。"""
    for i, line in enumerate(text.splitlines(), 1):
        if marker.search(line):
            t = terms_on(line)
            if t:
                return i, frozenset(t)
    return None, None


def main():
    root, cfg, as_json, name = cli("clause_sync")
    specs = cfg.get("synced_lists", [])
    globs = cfg.get("sync_scan_globs", [])
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "sync_scan_globs", root)

    if not specs:
        findings.append(("WARN", "SYNC_NO_SPEC",
                         "`synced_lists` 是空的——**本感測器目前保護不了任何東西**"
                         "（⚠️ 不適用 ≠ 通過）"))
        return emit("條款清單同步感測器", findings, {}, as_json, name)

    checked = copies = 0
    for spec in specs:
        marker = re.compile(spec["marker"])
        home = root / spec["home"]
        if not home.is_file():
            findings.append(("INCOMPLETE", "SYNC_HOME_MISSING",
                             f"清單「{spec['id']}」的定義處 {spec['home']} 不存在"
                             "——**本項未檢查，這不等於通過**"))
            continue
        _, want = find_list(home.read_text(encoding="utf-8", errors="replace"), marker)
        if want is None:
            findings.append(("INCOMPLETE", "SYNC_HOME_MISSING",
                             f"清單「{spec['id']}」的定義處 {spec['home']} "
                             "裡找不到這份清單——⚠️ **標記或定義處其中之一過期了，"
                             "而過期的守望與沒有守望長得一樣**"))
            continue

        found_copy = False
        for p in files:
            if p.resolve() == home.resolve():
                continue                       # ⛔ 定義處不與自己比
            lineno, got = find_list(p.read_text(encoding="utf-8", errors="replace"), marker)
            if got is None:
                continue
            found_copy = True
            copies += 1
            if got != want:
                extra = sorted(got - want)
                miss = sorted(want - got)
                findings.append(("FAIL", "SYNC_LIST_DRIFT",
                                 f"{p.relative_to(root)}:{lineno} 的「{spec['id']}」與定義處"
                                 f" {spec['home']} 不同："
                                 + (f"**少了** {miss}；" if miss else "")
                                 + (f"**多了** {extra}" if extra else "")
                                 + "——⛔ 逐字為準，順序不論"))
        checked += 1
        if not found_copy:
            findings.append(("WARN", "SYNC_NO_COPY",
                             f"清單「{spec['id']}」的定義處有內容，"
                             "**但掃描範圍內找不到任何副本**"
                             "——⚠️ 這一項目前沒有在守望任何東西"))

    return emit("條款清單同步感測器", findings,
                {"清單": checked, "找到的副本": copies, "掃描檔案": len(files)},
                as_json, name)


if __name__ == "__main__":
    raise SystemExit(main())
