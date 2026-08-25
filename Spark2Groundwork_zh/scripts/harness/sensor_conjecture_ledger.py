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
from _common import cli, emit                              # noqa: E402
from framework_config import load as _load_cfg, ROOT as _ROOT, excluded as _cfg_excluded
CFG = _load_cfg()

import re
import sys
from pathlib import Path

LEDGER_NAME = CFG["conjecture_ledger"]

# ⚠️ **單一定義處：`ledgers/Conjecture_Ledger.md` §0.1。本表須與它同步。**
#
# 🔴 **修正（本輪，移植至英文版時發現）：** 本集合原本只有 🔵🟡🟢🔴 四種，
#    而台帳 §0.1 定義的是**六種**——於是一筆**正確除役（⚫）或正確休眠（🟤）**的猜想
#    會被判 `CONJECTURE_STATUS_INVALID` FAIL。**那是 `R-19` 明文禁止的假陽性。**
#
# ⚠️ **兩個缺陷互相遮蔽：** 舊碼在狀態不合法時 `continue`，
#    所以 ⚫🟤 從來走不到下面的反證條件檢查——而那裡**同樣沒有為它們設豁免**。
#    **只修其中一個，會讓另一個當場現形。** 兩者本輪一併修。
VALID_STATUS = {"🔵", "🟡", "🟢", "🔴", "⚫", "🟤"}
# ⚫ 已判定不可證偽（反證條件本來就填不出來）；
# 🟤 休眠代表「這一輪不看它」，**不是知識論判定**，不應反覆提醒。
NO_FALSIFICATION_NEEDED = {"⚫", "🟤"}
EVIDENCE_REQUIRED = {"🟢", "🔴"}
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


# ⚠️ **此處原有一份硬編的 EXCLUDED_DIRS。已移除，理由有三：**
#    ① 它與 `framework_config.py` 的 `excluded_dirs` 重複——**憲章 §3.2：路徑只能有一個定義處**；
#    ② 兩者已經不同步（本檔少了 `node_modules` 與 `.venv`）；
#    ③ 其中一個項目是**另一個專案的資料夾名**，在本框架裡從不存在——死條目。
#    ⛔ `R-21`：白名單／硬編清單不得作為掃描範圍的定義方式。



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
    """排除判定一律委派給 `framework_config.excluded`（**單一定義處**）。

    ⚠️ 本檔第 30 行原本就 `import excluded as _excluded`，
    **然後在這裡用一個同名函式把它蓋掉了**——那個 import 從頭到尾是死的。
    **「改一層漏另一層」的一種形態：兩個定義並存，而只有一個被更新。**
    """
    return _cfg_excluded(path, root, CFG)


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
    # ⚠️ 參數解析與輸出格式一律走 `_common`（憲章 §3.2：每條規則只有一個定義處）。
    #    ⛔ 本檔原本自帶一份 `emit()`——**兩份實作，兩份同一則事故註記。**
    #    程式碼當時是對的，**但下一次只會有一份被更新，而那正是那則註記描述的失效。**
    root, _cfg, as_json, _name = cli("conjecture_ledger")
    findings = []          # (level, code, message)
    # ⚠️ 台帳缺失為「確定的缺陷」，不是「無法判定」，故判 FAIL 而非 INCOMPLETE。
    #    INCOMPLETE 保留給「感測器無法完成檢查」的情形（如掃描範圍落空）。
    ledger_path = root / LEDGER_NAME
    if not ledger_path.exists():
        findings.append(("FAIL", "LEDGER_MISSING", f"找不到 {LEDGER_NAME}（查找路徑：{ledger_path}）"))
        return emit("猜想台帳感測器", findings, {}, as_json, "conjecture_ledger")

    entries, dup = parse_ledger(safe_read(ledger_path))

    if not entries:
        findings.append(("FAIL", "LEDGER_MISSING", f"{LEDGER_NAME} 存在但解析不到任何 '### C-NN' 區塊——格式可能已變更"))
        return emit("猜想台帳感測器", findings, {}, as_json, "conjecture_ledger")

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
        #    **框架的模板，教人寫出一種會關掉框架自己感測器的寫法。** 那是「靜默過濾」家族。
        #
        #    → 修正：填了字**不會**讓警示消失。**只有人把 `反證條件裁決` 改成
        #      `已裁決` 才會。** ⛔ AI 不得自行改該欄。
        # ⚫ 與 🟤 豁免——見 VALID_STATUS 上方的說明。
        if status not in NO_FALSIFICATION_NEEDED and not adjudicated:
            declared = fields.get("填不出來的理由", "")
            if is_placeholder(falsif) and not is_placeholder(declared):
                # 🔴 **「刻意留白並寫下理由」與「欄位是空的」是兩種狀態，訊息必須說出是哪一種。**
                #    台帳 §0.3 第 1 條逐字寫著「填『—』不會比亂填更糟，這是刻意設計的」，
                #    而舊訊息對這種填法印的是「反證條件為空」——**與忘記填一字不差。**
                #    ⚠️ 後果很難察覺：**下一輪的人看到「為空」，很可能就去把它填上**，
                #    而那正是 §0.3 第 1 條想擋的行為。
                findings.append(("WARN", "FALSIFICATION_DECLARED_UNFALSIFIABLE",
                                 f"{cid}（{STATUS_NAME[status]}）已聲明填不出反證條件並附理由"
                                 f"——待人裁決是否除役（⚫）或切分（見台帳 §0.1b）"))
                continue
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

        if status in EVIDENCE_REQUIRED and is_placeholder(fields.get("依據", "")):
            findings.append(("FAIL", "EVIDENCE_MISSING_FOR_STATUS",
                             f"{cid} 狀態為 {status}（{STATUS_NAME[status]}）但依據為空——狀態升級須有可獨立複核的依據"))

    # ── 引用一致性：其他 .md 檔中的 C-NN 必須存在於台帳 ──────────────
    # ⚠️ 排除清單以「相對於 root 的路徑」判定，不用絕對路徑的 parts。
    #    否則 root 本身位於被排除的目錄下時（自測 fixture 即為此情形），
    #    掃描會全數落空而感測器仍印 PASS——這正是「掃不到即無紅燈」的失效形狀。
    # ⚠️ **台帳以「解析後的路徑」排除，⛔ 不是以檔名。**
    #    舊碼寫 `p.name != LEDGER_NAME`，而 LEDGER_NAME 是設定值
    #    `"ledgers/Conjecture_Ledger.md"`（一個**路徑**），永遠不等於裸檔名
    #    `"Conjecture_Ledger.md"` → **台帳自己一直在掃描範圍內，
    #    而 `SCAN_GLOB_MATCHES_NOTHING` 因此永遠不可能觸發。**
    #    **一個觸發不了的閘門，與死豁免同型。**
    _led_resolved = ledger_path.resolve()
    scan_targets = [p for p in root.rglob("*.md")
                    if p.resolve() != _led_resolved
                    and not _excluded(p, root)]

    if not scan_targets:
        # ⚠️ 「掃不到」是**查不了**，不是**查出缺陷**（`R-22`、憲章 §7.4）。
        findings.append(("INCOMPLETE", "SCAN_GLOB_MATCHES_NOTHING",
                         "引用掃描命中 0 個檔案——掃不到的地方等於沒有感測器"))
    else:
        # 🔴 提案檔豁免（裁決 8）。判準為**結構性**：位於 handoffs/ ＋ 檔名含標記。
        #    ⛔ 只豁免本項檢查，其餘照跑。⛔ 被豁免者一律印出。
        markers = CFG.get("proposal_markers", [])
        exempted = []
        for f_ in scan_targets:
            rel = f_.relative_to(root).as_posix()
            if rel.startswith("handoffs/") and any(mk in f_.name for mk in markers):
                exempted.append(rel)
                continue
            for lineno, line in enumerate((safe_read(f_) or "").splitlines(), 1):
                for m in CITATION_RE.finditer(line):
                    cid = f"C-{m.group(1)}"
                    if cid not in entries:
                        findings.append(("FAIL", "CITATION_NOT_IN_LEDGER",
                                         f"{rel}:{lineno} 引用了 {cid}，但台帳中無此編號"))
        if exempted:
            findings.append(("WARN", "CITATION_CHECK_EXEMPTED",
                             f"{len(exempted)} 個提案檔豁免引用存在性檢查："
                             f"{'、'.join(exempted[:4])}"
                             f"{'…' if len(exempted) > 4 else ''}"
                             "——**豁免不是沒有發生。裁決落地後請移除標記。**"))

    # ⚠️ ⛔ 不再傳一個獨立的 `incomplete` 布林。
    #    `_common.emit` 一律由 findings 的等級導出判定——**判定只能有一個來源。**
    stats = {
        "猜想筆數": len(entries),
        "掃描檔案": len(scan_targets),
        "狀態分佈": {STATUS_NAME.get(s, s): sum(1 for e in entries.values()
                                              if e["status"] == s)
                     for s in VALID_STATUS
                     if any(e["status"] == s for e in entries.values())},
        "反證條件為空": sum(1 for e in entries.values()
                            if is_placeholder(e["fields"].get("反證條件", ""))),
    }
    return emit("猜想台帳感測器", findings, stats, as_json, "conjecture_ledger")


if __name__ == "__main__":
    sys.exit(main())
