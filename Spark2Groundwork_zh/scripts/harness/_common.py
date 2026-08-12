#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器共用骨架 —— 統一輸出格式與退出碼。

⛔ **三個退出碼不得混用**（憲章 §7.4）：
    0 PASS｜1 FAIL（確定的缺陷）｜2 INCOMPLETE（查不了，**不等於通過**）
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from framework_config import load, resolve_globs, excluded   # noqa: E402


def cli(name):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import framework_config as fc
    root = pathlib.Path(a.root).resolve() if a.root else fc.ROOT
    return root, load(), a.json, name


def emit(title, findings, stats, as_json, sensor):
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    # ⚠️ INCOMPLETE 等級的 finding 必須使整體判定為 INCOMPLETE。
    #    先行專案曾把 incomplete 做成獨立布林參數，於是畫面印出 [INCOMPLETE]
    #    卻同時總結為 PASS、退出碼 0——**本專案最根本的一條規則被自己違反。**
    #    比缺陷本身更值得記的是它的形狀：**一個判定同時有兩個來源，而只有其中一個被更新。**
    inc = [f for f in findings if f[0] == "INCOMPLETE"]
    code = 2 if inc else (1 if fails else 0)
    if as_json:
        print(json.dumps({"sensor": sensor,
                          "status": {0: "PASS", 1: "FAIL", 2: "INCOMPLETE"}[code],
                          "findings": [{"level": l, "code": c, "message": m}
                                       for l, c, m in findings], "stats": stats},
                         ensure_ascii=False, indent=2))
    else:
        print(f"── {title} " + "─" * max(0, 34 - len(title)))
        for k, v in stats.items():
            print(f"  {k}：{v}")
        for l, c, m in findings:
            print(f"  [{l}] {c}: {m}")
        print(f"  結果：{{0:'PASS',1:'FAIL',2:'INCOMPLETE（**未完成 ≠ 通過**）'}}[{code}]"
              .replace("{0:'PASS',1:'FAIL',2:'INCOMPLETE（**未完成 ≠ 通過**）'}"
                       f"[{code}]", {0: 'PASS', 1: 'FAIL',
                                     2: 'INCOMPLETE（**未完成 ≠ 通過**）'}[code])
              + f"（WARN {len(warns)} 項）")
    return code


def dead_glob_findings(dead, where):
    """死 glob 必須被回報。

    ⚠️ **它與死豁免同型：看起來在保護什麼，其實沒有。**
    先行專案有兩個自建立起就命中 0 檔的 glob——一個因目錄被搬走、一個因名稱少了個 s。
    """
    return [("WARN", "SCAN_GLOB_MATCHES_NOTHING",
             f"{where} 的 glob「{g}」命中 0 個檔案——**它保護不了任何東西**")
            for g in dead]
