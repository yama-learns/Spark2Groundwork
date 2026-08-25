#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：治理文本一致性

## 四項檢查

    DUPLICATE_RULE_TEXT      跨檔完全相同的長句（同一規則有兩個家）      WARN
    SECTION_REF_UNRESOLVED   `<檔>.md` §N 的引用無法唯一解析              WARN
    STATE_IN_SPEC_DOC        規格類文件混入狀態（待辦／進度）           WARN
    SCAN_GLOB_MATCHES_NOTHING  掃描 glob 命中 0 檔                      WARN

## 為什麼需要它

**一次性掃描不是保證。** 某專案清掉 17 條跨檔重複後，那個掃描就再也沒跑過——
而它清乾淨的狀態是**一次性的成果，不是持續的保證**。

同理，「規則 → 唯一定義處」的對照表**是手維護白名單**：
新增規則時若忘了登錄，**就再也沒有機械方式知道它有沒有第二個家**——
**而那張表的職責恰恰是防止那件事。**

⛔ **本感測器不取代那張表。** 表回答「這條規則的家在哪」，
本感測器回答「有沒有規則長了第二個家」。**兩者的失效方向相反，都需要。**

## 已知盲區（⛔ 刻意保留，不得以「調鬆判準」處置）

1. 只比對**字面**相同，**抓不到語意相同而措辭不同的重複**——而那是更常見的漂移形態。
2. 全為 WARN 而非 FAIL：**精度優先於覆蓋**（R-19）。

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import re
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings          # noqa: E402
from framework_config import resolve_globs, excluded       # noqa: E402

# 🔴 **門檻以「資訊長度」計，⛔ 不以字元數計。**
#
# ⚠️ **實測個案：兩版的門檻原本不一樣**（中文版 24–80、英文版 40–220），
#    **而那個差異沒有任何地方登記為刻意分歧。**
#    後果具體可量：同一句規則
#      中文「順序不可調換：還原跨行斷字須在空白壓縮之前」→ 正規化後 **21 字元**
#      英文 "The order cannot be swapped: de-hyphenation..." → **68 字元**
#    **兩版都有這句重複，而只有英文版被抓到——中文版差 3 個字落在門檻外。**
#
# ⛔ **一個以字元數計的門檻，對中文的偵測力系統性地低於英文**，
#    因為中文表達同樣的內容只需要約三分之一的字元。
#    → 改以資訊長度計：**一個中日韓字元約當三個拉丁字元。**
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
CJK_WEIGHT = 3


def info_len(s):
    """資訊長度——⛔ 不是 len()。見上方說明。"""
    n = len(CJK.findall(s))
    return (len(s) - n) + n * CJK_WEIGHT


MIN_DUP, MAX_DUP = 40, 220
# ⚠️ **判準是結構，不是關鍵字。**
#    首版以「出現『待辦』二字」判定，於是**談論「不得含待辦」的規則文字本身被抓到**。
#    關鍵字獵巫的代價，是對正確文本報警——而那會教人關掉感測器（R-19）。
#    → 改為只認**待辦清單的結構**：核取方塊、「✅ 已完成」標記、或表格中的進度欄。
STATE_WORDS = re.compile(r"^\s*[-*]\s*\[[ xX]\]|✅\s*\*\*已完成|\|\s*✅\s*已完成\s*\|",
                         re.M)
REF = re.compile(r"`([\w一-鿿_/.-]+\.md)`\s*(?:之\s*)?§(\d+(?:\.\d+[a-z]?)?)")


# ── 檔頭標語不是規則 ────────────────────────────────────────────────
# ⚠️ **實測個案：** `Claim_Ledger.md` 與 `Conjecture_Ledger.md` 的檔頭同樣寫著
#    「T1 資料類。AI 不得直接寫入本檔。」，於是被判為「同一規則有兩個家」。
#    **那一行是檔案的中繼資料，不是規則**——每個資料類檔案都必須各自寫上它，
#    否則讀者不知道手上這一份是什麼。**要求它只出現一次，等於要求它不成立。**
# ⛔ **這不是「因為誤報所以放寬判準」（R-20），是把判準的對象修正回規則本身。**
#    → 判準仍是結構，不是關鍵字：**整行只有一個粗體段、且位在第一個 `## ` 之前**。
#    章節內的重複規則文字不受影響——`gov_dup` 的「必須抓到」樣本守著這一點。
# ⚠️ **斷句器一度只認 `。` 與換行**，於是英文版只能比對「整行相同」——
#    `Audit_Protocol.md` 與 `HANDOFF.md` 共用的那句話，中文版抓到、英文版沒抓到，
#    **而兩版的文字其實一樣重複。** 感測器強弱不同，會被誤讀成兩版品質不同。
#    → 補上「句號（可帶收尾的 `**`、引號、括號）後接空白」為斷點；
#    `3.2`、`.md` 不會被切開（且行內程式碼已先移除）。
#    ⚠️ 收尾符號那一段是實測補的：`**...unfinished.** "None"...` 的句號後面是 `*` 不是空白，
#    **只認「句號＋空白」時整句仍然接在一起，於是照樣抓不到。**
SPLIT = re.compile(r"。|(?<=\.)[*_\"'’”)\]]*\s+|\n")


# ── 指名了定義處的句子，不是「第二個定義處」──────────────────────
# ⚠️ **實測個案：** 把一句重複的規則改成「見憲章 §3.4，⛔ 本處不重述」之後，
#    **那句「引用」本身在兩個檔案裡逐字相同，於是又被判為重複。**
# 🔴 **但那是反過來的：一句指名了定義處的話，⛔ 不可能是第二個定義處——
#    它正是防止第二個定義處存在的那個機制。**
# ⛔ **這不是「因為誤報所以放寬判準」（R-20），是把判準的對象修正回規則本身。**
#    → 判準仍是結構：**句中出現 `§` 章節號或 `R-nn` 規則號**，即視為指標。
#    ⚠️ 代價寫明：一條**同時指名了某個章節**的真重複規則會被漏掉。
#    **本感測器選擇漏掉它，⛔ 而不是對每一個引用報警**（`R-19`）。
POINTER = re.compile(r"§\s*\d|R-\d\d")


BANNER = re.compile(r"^\*\*[^*]+\*\*$")


def strip_banner(text):
    """移除檔頭標語行（中繼資料），保留其餘全文。"""
    out, in_header = [], True
    for line in text.split("\n"):
        if line.startswith("## "):
            in_header = False
        if in_header and BANNER.match(line.strip()):
            continue
        out.append(line)
    return "\n".join(out)


def sentences(text):
    text = strip_banner(text)
    text = re.sub(r"`[^`]*`", "", text)
    for raw in re.split(SPLIT, text):
        s = re.sub(r"[*⚠️⛔🔴🟢🟡🟤📌>#|\-—\s]", "", raw)
        if POINTER.search(raw):
            continue          # ⛔ 指標，不是規則
        if MIN_DUP <= info_len(s) <= MAX_DUP:
            yield s


def main():
    root, cfg, as_json, name = cli("governance_text")
    files, dead = resolve_globs(cfg["governance_globs"], root, cfg)
    findings = dead_glob_findings(dead, "governance_globs", root)
    if not files:
        findings.append(("INCOMPLETE", "GOV_DOCS_ABSENT",
                         "找不到任何治理文件——**本輪未檢查，這不等於通過**"))
        return emit("治理文本感測器", findings, {}, as_json, name)

    texts = {}
    for p in files:
        try:
            texts[p] = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} 非 UTF-8——**未檢查 ≠ 通過**"))

    # ① 跨檔重複
    idx = defaultdict(set)
    for p, t in texts.items():
        for s in sentences(t):
            idx[s].add(p.name)
    for s, where in sorted(idx.items()):
        if len(where) > 1:
            findings.append(("WARN", "DUPLICATE_RULE_TEXT",
                             f"同一長句出現於 {'／'.join(sorted(where))}：「{s[:40]}…」"
                             "——每條規則只有一個定義處"))

    # ② 章節引用可解析
    #    ⚠️ 索引以**檔名**為鍵；掃描全樹但依相對路徑排除（R-18）
    all_md = {q.name: q for q in root.rglob("*.md") if not excluded(q, root, cfg)}
    seen = set()
    for p, t in texts.items():
        for m in REF.finditer(t):
            fn, sec = pathlib.Path(m.group(1)).name, m.group(2)
            tgt = all_md.get(fn)
            if tgt is None or (p.name, fn, sec) in seen:
                continue
            body = tgt.read_text(encoding="utf-8", errors="replace")
            # §9 只配 "## 9." 不配 "### 9.1"
            hits = len(re.findall(rf"^#+\s*{re.escape(sec)}(?=[ .、（(])(?!\.\d)", body, re.M))
            if hits != 1:
                seen.add((p.name, fn, sec))
                findings.append(("WARN", "SECTION_REF_UNRESOLVED",
                                 f"{p.name} 引用 {fn} §{sec}，命中 {hits} 次"
                                 f"——{'不存在' if hits == 0 else '不唯一'}"))

    # ③ 規格類文件不得含狀態
    #    ⚠️ **豁免規則文字本身。** 定義「不得含待辦」的那一段必然含「待辦」二字。
    #    首版未豁免，對正確文本誤報——**豁免的粒度錯了，不是判準太嚴。**
    #    這與自我背書感測器豁免「閘門式要求」是同一個道理。
    for p, t in texts.items():
        hits = [para for para in t.split("\n\n")
                if STATE_WORDS.search(para) and not re.search(r"⛔|不得|必須|禁止", para)]
        if hits:
            findings.append(("WARN", "STATE_IN_SPEC_DOC",
                             f"{p.name} 含待辦或進度用語（{len(hits)} 段）——"
                             "**混入狀態的文件會繼承其最快變動部分的更新頻率**"))

    code = emit("治理文本感測器", findings, {"掃描治理文件": len(texts)}, as_json, name)
    if not as_json:
        print("      ⚠️ 只比對**字面**重複，抓不到語意相同而措辭不同者")
    return code


if __name__ == "__main__":
    sys.exit(main())
