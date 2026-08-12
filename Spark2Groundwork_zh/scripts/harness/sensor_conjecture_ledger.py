#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猜想台帳感測器 — 證據鏈環①②③（欄位層）

檢查項目
--------
LEDGER_MISSING                找不到猜想台帳
SCAN_GLOB_MATCHES_NOTHING     掃描範圍命中 0 個檔案（掃不到的地方等於沒有感測器）
CONJECTURE_ID_DUPLICATE       同一編號出現多次
CONJECTURE_STATUS_INVALID     狀態不是四種之一
CONJECTURE_FIELD_MISSING      必填欄位缺漏
FALSIFICATION_EMPTY           反證條件為空（🔵 為 WARN，🟡🟢 為 FAIL）
RIVAL_EMPTY                   最強競爭解釋為空
RIVAL_PREDICTION_EMPTY        競爭解釋的不同預測為空
EVIDENCE_MISSING_FOR_STATUS   🟢／🔴 之依據為空
CITATION_NOT_IN_LEDGER        其他文件引用了台帳中不存在的編號

設計原則
--------
* 精度優先於覆蓋：對正確文本報錯的感測器會教會使用者忽略它。
* 本感測器只查「欄位是否填了東西」，不查「填的東西對不對」。
  後者屬證據鏈環⑥⑦，刻意不機械化（《研究憲章》§2）。
* 未完成 ≠ 通過：掃描範圍落空時回報 INCOMPLETE 並以 exit 2 結束。
"""

import sys, pathlib as _pl
_pl_here = _pl.Path(__file__).resolve().parent
sys.path.insert(0, str(_pl_here))
from framework_config import load as _load_cfg, ROOT as _ROOT, excluded as _excluded
CFG = _load_cfg()

import argparse
import json
import re
import sys
from pathlib import Path

LEDGER_NAME = CFG["conjecture_ledger"]

VALID_STATUS = {"🔵", "🟡", "🟢", "🔴"}
# ⚠️ 本表須與 `Conjecture_Ledger.md` §0.1 同步。
#    ⚫ 與 🟤 於此列出但不參與 FALSIFICATION_EMPTY 計數：
#    ⚫ 已判定不可證偽（反證條件本來就填不出來），
#    🟤 休眠代表「這一輪不看它」，**不是知識論判定**，不應反覆提醒。
STATUS_NAME = {"🔵": "猜想", "🟡": "已可證偽", "🟢": "文獻支持",
               "🔴": "已被推翻", "⚫": "不可證偽（已除役）", "🟤": "休眠"}

REQUIRED_FIELDS = ["表述", "來源", "反證條件", "最強競爭解釋", "競爭解釋的不同預測", "依據", "紀錄"]

# 佔位符：這些內容視同未填。刻意不含「無」——「無」有時是有意義的答案。
PLACEHOLDERS = {"", "—", "-", "–", "TBD", "tbd", "待填", "待定", "?", "？", "N/A", "n/a", "…"}

# 標題格式：### C-01 ｜ 🔵 猜想 ｜ 分支 A
HEADING_RE = re.compile(r"^###\s+(C-\d{2,})\s*[｜|]\s*(\S+)\s*(\S*)\s*[｜|]?\s*(.*)$")
FIELD_RE = re.compile(r"^\*\*(.+?)：\*\*\s*(.*)$")
# 引用格式：[C-01] 或 C-01（後者須非緊接數字，避免誤抓）
CITATION_RE = re.compile(r"\bC-(\d{2,})\b")


EXCLUDED_DIRS = {"archive", "其他專案治理文件供參", "selftest", "scratch", ".git", "__pycache__"}



def safe_read(path):
    """讀取文字檔；無法以 UTF-8 解碼時回傳 None 而不是拋出例外。

    ⚠️ **本函式來自一次真實當機（2026-08-08）。** 審計 agent 的沙盒中有一個
    由 PowerShell `echo` 產生的 UTF-16 檔案，其 BOM 首位元組 0xff 使
    `read_text(encoding="utf-8")` 拋出 `UnicodeDecodeError`，
    **兩支感測器直接崩潰，而總執行器把崩潰計為「回報缺陷」。**

    🔴 **兩個獨立的缺陷：**
    1. **任何一個非 UTF-8 檔案，可以讓整套 harness 停擺**——
       而那個檔案甚至不必屬於本專案。
    2. **崩潰被算成 FAIL。** 崩潰是「查不了」，不是「查出問題」——
       依本專案 INCOMPLETE ≠ PASS 的同一原則，**FAIL ≠ CRASH 亦然**：
       把兩者混為一談，會讓「感測器壞了」看起來像「文件有問題」。

    ⚠️ 審計報告曾把該 UTF-16 檔案記為「微小發現／PowerShell 行為」——
    **它是對的，但沒有人把它連到 harness 的健壯性上。**
    """
    try:
        # ⛔ 此處必須是 path.read_text，不得改寫成 safe_read——那會無窮遞迴。
        #    2026-08-08 一次批次改寫誤把本行也換掉，兩支感測器同時死當，
        #    **成對自測 15/15 全數失敗當場攔下。**
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

def _excluded(path: Path, root: Path) -> bool:
    """排除判定以相對路徑為準（見 scan_targets 處之註記）。"""
    return bool(EXCLUDED_DIRS & set(path.relative_to(root).parts[:-1]))


def is_placeholder(value: str) -> bool:
    return value.strip() in PLACEHOLDERS


def parse_ledger(text: str):
    """回傳 {編號: {'status':..., 'fields':{...}, 'line':int}} 與重複編號清單。"""
    entries, dup, current, cur_id = {}, [], None, None
    for lineno, line in enumerate(text.splitlines(), 1):
        m = HEADING_RE.match(line.rstrip())
        if m:
            cur_id, status = m.group(1), m.group(2)
            if cur_id in entries:
                dup.append((cur_id, lineno))
            current = {"status": status, "fields": {}, "line": lineno}
            entries[cur_id] = current
            continue
        if current is None:
            continue
        fm = FIELD_RE.match(line.rstrip())
        if fm:
            current["fields"][fm.group(1).strip()] = fm.group(2).strip()
    return entries, dup



def is_template(v):
    """A field still holding a `<<<填空...` marker means the template has not been filled.

    ⚠️ **An unfilled template and a filled-but-defective ledger are different states.**
    Reporting FAIL on a brand-new project contradicts the setup guide, which tells the user
    a batch of warnings on the first run is normal — **and a first run that fails teaches
    the user that red means nothing.**
    """
    return "<<<填空" in v or v.strip().startswith("<<<")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="專案根目錄")
    ap.add_argument("--json", action="store_true", help="以 JSON 輸出")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    findings = []          # (level, code, message)
    incomplete = False

    # ⚠️ 台帳缺失為「確定的缺陷」，不是「無法判定」，故判 FAIL 而非 INCOMPLETE。
    #    INCOMPLETE 保留給「感測器無法完成檢查」的情形（如掃描範圍落空）。
    ledger_path = root / LEDGER_NAME
    if not ledger_path.exists():
        findings.append(("FAIL", "LEDGER_MISSING", f"找不到 {LEDGER_NAME}（查找路徑：{ledger_path}）"))
        return emit(findings, {}, False, args.json)

    entries, dup = parse_ledger(safe_read(ledger_path))

    if not entries:
        findings.append(("FAIL", "LEDGER_MISSING", f"{LEDGER_NAME} 存在但解析不到任何 '### C-NN' 區塊——格式可能已變更"))
        return emit(findings, {}, False, args.json)

    for cid, lineno in dup:
        findings.append(("FAIL", "CONJECTURE_ID_DUPLICATE", f"{cid} 重複出現（第 {lineno} 行）"))

    for cid, e in sorted(entries.items()):
        status, fields = e["status"], e["fields"]

        if status not in VALID_STATUS:
            findings.append(("FAIL", "CONJECTURE_STATUS_INVALID",
                             f"{cid} 狀態 '{status}' 不是四種之一（🔵🟡🟢🔴）"))
            continue

        for f in REQUIRED_FIELDS:
            if f not in fields:
                findings.append(("FAIL", "CONJECTURE_FIELD_MISSING", f"{cid} 缺少必填欄位「{f}」"))

        falsif = fields.get("反證條件", "")
        adjudicated = fields.get("反證條件裁決", "").strip() in ("已裁決", "已裁決 ✅", "✅ 已裁決")

        # ⚠️ 🔴 **告警的條件是「尚未經人裁決」，不是「欄位為空」。**
        #
        #    首版只在欄位為空時告警。實測（框架自身的 solo agent 測試）發現：
        #    **誠實留白會亮黃燈，而編一句讀起來合格的假反證條件不會**——
        #    而沒有任何人或感測器分得出那是裝飾品。
        #    **獎懲方向是反的：誠實被罰，唬爛被獎。**
        #
        #    更糟的是，框架自己的拆解模板建議寫「反證條件待填——見下方說明」，
        #    **而那個寫法會使告警靜默消失**（實測：2 筆 → 1 筆，退出碼仍為 0）。
        #    **框架的模板，教人寫出一種會關掉框架自己感測器的寫法。** 那是失效家族④。
        #
        #    → 修正：填了字**不會**讓警示消失。**只有人把 `反證條件裁決` 改成
        #      `已裁決` 才會。** ⛔ AI 不得自行改該欄。
        if not adjudicated:
            if is_placeholder(falsif):
                lvl, why = ("WARN", "反證條件為空") if status == "🔵" else \
                           ("FAIL", "反證條件為空，但狀態已非「猜想」")
            else:
                lvl, why = ("WARN", "反證條件已填但未經人裁決——"
                                    "**填了字不代表它可觀察，這一項只有人能判**")
            findings.append((lvl, "FALSIFICATION_UNADJUDICATED",
                             f"{cid}（{STATUS_NAME[status]}）{why}"))

        if "最強競爭解釋" in fields and is_placeholder(fields["最強競爭解釋"]):
            findings.append(("FAIL", "RIVAL_EMPTY", f"{cid} 未指名最強競爭解釋"))

        if "競爭解釋的不同預測" in fields and is_placeholder(fields["競爭解釋的不同預測"]):
            findings.append(("FAIL", "RIVAL_PREDICTION_EMPTY",
                             f"{cid} 未說明競爭解釋的預測與本猜想何處不同——裝飾性的競爭假說比沒有更糟"))

        if status in {"🟢", "🔴"} and is_placeholder(fields.get("依據", "")):
            findings.append(("FAIL", "EVIDENCE_MISSING_FOR_STATUS",
                             f"{cid} 狀態為 {status}（{STATUS_NAME[status]}）但依據為空——狀態升級須有可獨立複核的依據"))

    # ── 引用一致性：其他 .md 檔中的 C-NN 必須存在於台帳 ──────────────
    # ⚠️ 排除清單以「相對於 root 的路徑」判定，不用絕對路徑的 parts。
    #    否則 root 本身位於被排除的目錄下時（自測 fixture 即為此情形），
    #    掃描會全數落空而感測器仍印 PASS——這正是「掃不到即無紅燈」的失效形狀。
    scan_targets = [p for p in root.rglob("*.md")
                    if p.name != LEDGER_NAME
                    and not _excluded(p, root)]

    if not scan_targets:
        findings.append(("FAIL", "SCAN_GLOB_MATCHES_NOTHING",
                         "引用掃描命中 0 個檔案——掃不到的地方等於沒有感測器"))
        incomplete = True
    else:
        for p in scan_targets:
            for lineno, line in enumerate((safe_read(p) or "").splitlines(), 1):
                for m in CITATION_RE.finditer(line):
                    cid = f"C-{m.group(1)}"
                    if cid not in entries:
                        findings.append(("FAIL", "CITATION_NOT_IN_LEDGER",
                                         f"{p.relative_to(root)}:{lineno} 引用了 {cid}，但台帳中無此編號"))

    stats = {
        "conjectures": len(entries),
        "by_status": {STATUS_NAME.get(s, s): sum(1 for e in entries.values() if e["status"] == s)
                      for s in VALID_STATUS},
        "falsification_empty": sum(1 for e in entries.values()
                                   if is_placeholder(e["fields"].get("反證條件", ""))),
        "scanned_files": len(scan_targets),
    }
    return emit(findings, stats, incomplete, args.json)


def emit(findings, stats, incomplete, as_json) -> int:
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    # ⚠️ INCOMPLETE 等級的 finding 必須同樣使整體判定為 INCOMPLETE。
    #    2026-08-08 新增 FILE_NOT_DECODABLE 時，它被列成一筆 finding，
    #    但 `incomplete` 是一個獨立的布林參數而非由 findings 導出，
    #    於是畫面印出 [INCOMPLETE] 卻同時總結為 PASS、退出碼 0。
    #    🔴 **那正是本專案最根本的一條規則被自己違反：INCOMPLETE ≠ PASS。**
    #    比缺陷本身更值得記的是它的形狀：**一個判定同時有兩個來源，
    #    而只有其中一個被更新。**
    incomplete = incomplete or any(f[0] == "INCOMPLETE" for f in findings)

    if as_json:
        print(json.dumps({
            "sensor": "conjecture_ledger",
            "status": "INCOMPLETE" if incomplete else ("FAIL" if fails else "PASS"),
            "fails": len(fails), "warns": len(warns),
            "findings": [{"level": l, "code": c, "message": m} for l, c, m in findings],
            "stats": stats,
        }, ensure_ascii=False, indent=2))
    else:
        print("── 猜想台帳感測器 ──────────────────────────────")
        if stats:
            print(f"  猜想筆數：{stats['conjectures']}　掃描檔案：{stats['scanned_files']}")
            print(f"  狀態分佈：{stats['by_status']}")
            print(f"  反證條件為空：{stats['falsification_empty']} 筆")
        for level, code, msg in findings:
            print(f"  [{level}] {code}: {msg}")
        if incomplete:
            print("  結果：INCOMPLETE（掃描範圍落空，未完成 ≠ 通過）")
        elif fails:
            print(f"  結果：FAIL（{len(fails)} 項）")
        else:
            print(f"  結果：PASS（WARN {len(warns)} 項）")

    if incomplete:
        return 2
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
