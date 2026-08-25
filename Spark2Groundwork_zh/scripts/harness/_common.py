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

def _force_utf8():
    """⛔ **輸出編碼必須是 UTF-8，⛔ 不得依賴系統預設。**

    🔴 **實測個案（繁體中文 Windows）：** Python 在 Windows 上的預設輸出編碼是系統
    ANSI 碼頁（繁中為 `cp950`），而本框架的每一則訊息都含 `✅`／`⚠️`／`⛔`。
    **於是感測器印到第一個符號就 `UnicodeEncodeError` 當掉。**

    ⚠️ **更糟的是它當掉的方式：** Python 未捕捉例外一律以 **exit 1** 結束，
    **而 `run_all_sensors.py` 把 exit 1 讀成「找到缺陷」（FAIL），不是「查不了」（INCOMPLETE）。**
    🔴 **於是畫面顯示「整套 FAIL」，而真正發生的是兩支感測器根本沒有跑完**——
    **那正是 `R-22` 與憲章 §7.4 要擋的混淆，發生在框架自己身上。**

    ⛔ `errors="replace"` 是刻意的：**最壞情況是印出 `?`，⛔ 不是整支程式當掉。**
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if sys.platform == "win32":
        # 讓主控台也用 UTF-8 顯示，否則不會當掉但會變成亂碼。
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:                                    # noqa: BLE001
            pass


_force_utf8()



def cli(name):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import framework_config as fc
    root = pathlib.Path(a.root).resolve() if a.root else fc.ROOT
    # ⚠️ 設定讀自**被掃描的根目錄**，見 framework_config.load 的說明。
    return root, load(root), a.json, name


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


def _glob_dir(root, g):
    """glob 所指的**掃描目錄**；⛔ 若這個樣式根本不是掃描範圍，回傳 None。

    ⚠️ **無萬用字元的樣式（例如 `file_index.md`）指的是一個特定檔案，不是一個掃描範圍。**
    首版把它的「目錄」算成專案根目錄，而根目錄永遠有東西——
    **於是每一個缺少該檔的 fixture 都被判成覆蓋崩潰。自測當場抓到 7 筆回歸。**
    → 這種樣式一律回傳 None，交由 `WARN`（檔案不存在）處理。
    """
    if "*" not in g:
        return None
    head = g.split("*", 1)[0]
    return (root / head) if head.endswith("/") else (root / head).parent


def dead_glob_findings(dead, where, root=None):
    """命中 0 個檔案的 glob 必須被回報。

    ⚠️ **它與死豁免同型：看起來在保護什麼，其實沒有。**
    先行專案有兩個自建立起就命中 0 檔的 glob——一個因目錄被搬走、一個因名稱少了個 s。

    ## 🔴 兩種「命中 0 個」在輸出上長得一樣，但它們是兩件事（裁決 20）

    | 情況 | 是什麼 | 等級 |
    |---|---|---|
    | **目錄不存在** | 這個專案還沒用到這一塊 | `WARN`——新專案的正常狀態 |
    | **目錄存在，但掃到 0 個檔** | 🔴 **覆蓋崩潰** | `INCOMPLETE`（exit 2） |

    ⚠️ **觸發個案（他專案實測）：** 一輪對抗測試查出**五支感測器**在「比對對象變成 0」時
    一律印 PASS——**「查無比對對象」與「比對後一致」在輸出上完全相同，
    因為分母歸零時一致性判準自動全真。**

    ⛔ **但一律升為 exit 2 是錯的：** 那會讓一個全新專案第一次執行就得到 INCOMPLETE，
    而憲章 §4.1.1 對退出碼 2 的處置是「停止並回報」——**與 `SETUP.md` 說的
    「第一次跑有一批警告是正常的」直接打架。而常態性紅燈會教人忽略整套系統（`R-19`）。**

    → **判準改為結構性的：目錄在不在。⛔ 不需要任何歷史資訊。**
    """
    out = []
    for g in dead:
        # ⚠️ **判準收緊過兩次，兩次都是自測當場抓到的：**
        #    ① 首版「目錄存在即崩潰」→ 一個剛建好還沒用的目錄被判 INCOMPLETE。
        #    ② 第二版「目錄裡有東西即崩潰」→ `scripts/**/*.sh` 在只有 `.py` 的專案裡
        #       被判崩潰，**而那只是「這裡沒有這種檔」。**
        #    → 最終判準：**同副檔名的檔案確實存在於該目錄底下，而這個 glob 一個都沒看到。**
        #      那才是「東西在，但 glob 看不到」——例如深度寫錯、名稱樣式寫錯。
        d = _glob_dir(root, g) if root is not None else None
        suffix = pathlib.Path(g).suffix
        collapsed = bool(d and d.is_dir() and suffix
                         and any(f.is_file() for f in d.rglob("*" + suffix)))
        if collapsed:
            out.append(("INCOMPLETE", "COVERAGE_COLLAPSE",
                        f"{where} 的 glob「{g}」：**目錄存在，但掃到 0 個檔**"
                        "——⚠️ 這不是「沒問題」，是**查不了**。"
                        "「查無比對對象」與「比對後一致」在輸出上長得一樣"))
        else:
            out.append(("WARN", "SCAN_GLOB_MATCHES_NOTHING",
                        f"{where} 的 glob「{g}」命中 0 個檔案（目錄尚不存在）"
                        "——**它目前保護不了任何東西**（⚠️ 不適用 ≠ 通過）"))
    return out
