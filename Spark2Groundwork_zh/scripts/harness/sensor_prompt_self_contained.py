#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：Prompt 自足性（隨選，一次一個檔案）

外部工具的每一次執行都在獨立對話中、不共享上下文，於是「同上」「參見前述」
「Same as R1」在**執行端等同空白**——被指涉的條款實質上不存在。

⚠️ **本感測器的存在，是因為規則本身擋不住這個錯誤：**
某份 prompt 的 §1 引述了第 11 條（「不得寫『同上』」），
**然後在下半部的 R3-2～R3-5 寫了「Same as R3-1」。引述規則與違反規則同處一檔。**
實測後果：`[NO-DOI]` 標記使用 **0 次**（定義從未出現在該 Prompt 內），
而條款完整的那一份使用 **12 次**。

## 🔴 兩層檢查，⛔ 不得混為一談

**這一節是本檔最重要的部分。**

| 層 | 檢查 | 適用範圍 |
|---|---|---|
| **① 自足性** | 跨 prompt 指涉、未組裝的區塊佔位符、prompt 汙染 | **所有 prompt** |
| **② DR 條款表** | LANG／VENUE-TYPE／NO-DOI／PASS A／PASS B／標題精確性／NONE RETRIEVED／OUTPUT CONTRACT | ⚠️ **只有 `--profile deep-research`** |

⚠️ **舊版把 ② 對所有 prompt 執行，後果實測如下：**
`prompts/TEMPLATE_decompose.txt` 是一份**完全自足**的拆解 prompt，
它開頭逐字寫著「⛔ 這一輪不要查文獻」——
**一份禁止查文獻的 prompt，不可能也不應該包含雙語檢索條款。**
**它被判 FAIL，而且組裝完成之後仍然會 FAIL，永遠。**

⛔ **那是 `R-19` 的完整形態，而且是兩層：**
一支對正確文本報警的感測器，**加上一份告訴讀者「這個 FAIL 是正確的、不用理」的官方說明**。
**第二層比第一層危險——它把「忽略這支感測器」寫成了制度。**

## 🔴 三種 `<<<…>>>` 佔位符，**只有一種是缺陷**

| 形態 | 例 | 判定 |
|---|---|---|
| **區塊佔位符** | `<<<貼上區塊 B（列舉，不要摘要）>>>` | ❌ **FAIL** — 這是真正的跨 prompt 指涉，尚未組裝 |
| **內容槽** | `<<<貼上你的構想全文>>>` | ✅ **不是缺陷** — 那是使用者在使用時才填的輸入位 |
| **填空槽** | `<<<填空:一句話>>>` | ⚠️ **WARN** — 提醒尚未填，但不阻擋 |

⚠️ **舊版把三者一律當缺陷**，於是 `TEMPLATE_decompose.txt` 因為
`<<<貼上你的構想全文>>>` 被判 FAIL——**而那個佔位符本來就該留在那裡。**

## 🔴 引述禁令 ≠ 違反禁令

**實測個案：** `TEMPLATE_decompose.txt` 有一行逐字是
「⛔ 不要在反證條件欄裡寫『待填』『見下方說明』之類的字」，
**而感測器把其中的「見下方」當成跨檔指涉判 FAIL。**

> **字串比對能辨認「有沒有這個詞」，不能辨認「這個詞是誰在說」。**
> 這是正則的能力邊界，先行專案在三個不同的感測器上各撞過一次。

→ **處置：同一行內若禁令標記（⛔／不得／不要／禁止）出現在該詞**之前**，
判定為引述，不計為缺陷。⛔ 而被豁免的行數一律印出**——
**靜默豁免與沒有豁免，在畫面上長得一樣。**

用法
----
    python3 sensor_prompt_self_contained.py <prompt.md|txt> [--profile deep-research] [--json]

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（查不了。**⛔ 這不等於通過**）
"""
import argparse
import json
import pathlib
import re
import sys

# ⛔ 本檔的介面是「單一檔案」，⛔ 不經 `_common.cli`——但輸出編碼仍必須先固定。
#    ⚠️ 實測：漏掉這一步時，本感測器在 cp950 環境下當掉，
#    **而自測有四項因此變紅——紅的原因不是判斷錯，是它根本沒印完。**
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import _force_utf8                            # noqa: E402
_force_utf8()

# ── ① 自足性：所有 prompt 適用 ──────────────────────────────────
CROSSREF = [
    (r"(?i)\bsame as\s+R?\d", "Same as R#"),
    (r"(?i)\bas (?:in|above|described above)\b[^\n]{0,20}R?\d", "as in R#"),
    (r"(?i)\bsee (?:above|below|R\d|section)\b", "see above/below/§"),
    (r"(?i)\b(?:ditto|idem)\b", "ditto"),
    (r"同\s*上", "同上"),
    (r"參\s*見\s*前\s*述", "參見前述"),
    (r"如\s*前\s*所\s*述", "如前所述"),
    (r"見\s*下\s*方", "見下方"),
]
# 真正的缺陷：尚未組裝的區塊
BLOCK_SLOT = re.compile(r"<<<[^>]*(?:貼上區塊|PASTE BLOCK)[^>]*>>>", re.I)
# ✅ 不是缺陷：使用者在使用時才填的輸入位
CONTENT_SLOT = re.compile(r"<<<[^>]*(?:貼上你的|貼上待審|貼上原文|PASTE YOUR|PASTE THE)[^>]*>>>", re.I)
# ⚠️ 提醒但不阻擋
FILL_SLOT = re.compile(r"<<<\s*(?:填空|FILL IN)", re.I)
# 禁令標記——出現在被比對詞**之前**即視為引述
PROHIBITION = re.compile(r"⛔|不得|不要|禁止|(?i:do not|never write|must not)")

# prompt 汙染：對「每次重置、無跨次記憶」的執行端無意義的內容
POLLUTION = [
    (r"R3-\d\s*v\d", "版本代號"),
    (r"已廢止|前一版|上一版|先前版本|previous version|deprecated", "改版沿革"),
    (r"觸發個案|內部實測|internal (?:test|incident)", "內部實測記錄"),
]

# 通用提示（WARN）：任何外部 prompt 都該有的三件事
# ⚠️ **這三個樣式是以框架自己隨附的三份模板校準的。**
#    ⛔ 若某一項對一份寫得好的 prompt 報警，那是樣式錯了，不是 prompt 錯了（`R-19`）。
#    **校準參考：`prompts/TEMPLATE_decompose.txt`、`TEMPLATE_adversarial.txt`
#    （組裝後的 `TEMPLATE_prior_art.txt` 亦同）。**
GENERIC_HINTS = [
    ("幻覺護欄", r"不確定|不得(?:編造|捏造)|不要編|勿編|填不出來就|查無|"
                 r"uncertain|do not invent|do not make (?:it |them )?up|fabricat"),
    # ⚠️ 刻意**不含**裸的「列出」——實測會命中散文（對抗模板的「沒有被列出來」），
    #    那會讓一份其實沒有列舉要求的 prompt 看起來合格。**少報比誤報危險。**
    ("列舉要求", r"逐條|逐項|每行一筆|一行一|列舉|先列|"
                 r"NONE RETRIEVED|enumerate|one per line|list each|numbered from"),
    ("輸出契約", r"輸出格式|輸出契約|回報格式|報告格式|涵蓋範圍|回報以下|"
                 r"OUTPUT CONTRACT|output contract|report the following|coverage"),
]

# ── ② Deep Research 專用條款表 ──────────────────────────────────
# ⚠️ **只在 --profile deep-research 下執行。** 見檔頭「兩層檢查」。
DR_REQUIRED = [
    (r"\[LANG:", "LANG 標籤定義"),
    (r"\[VENUE-TYPE:", "VENUE-TYPE 標籤定義"),
    (r"\[NO-DOI", "NO-DOI 機制"),
    (r"(?i)PASS A", "PASS A 英文檢索"),
    (r"(?i)PASS B", "PASS B 中文檢索"),
    (r"(?i)TITLE ACCURACY|paraphrase, shorten, or improve", "標題精確性條款"),
    (r"(?i)NONE RETRIEVED", "枚舉版 NONE RETRIEVED"),
    (r"(?i)OUTPUT CONTRACT", "OUTPUT CONTRACT"),
]


def quoted(line, start):
    """該詞是否在同一行的禁令標記之後出現（＝被引述，不是被使用）。"""
    m = PROHIBITION.search(line)
    return bool(m and m.start() < start)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--profile", default="generic", choices=["generic", "deep-research"],
                    help="deep-research 才執行 DR 專用條款表")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    p = pathlib.Path(a.prompt)
    if not p.exists():
        print(f"[INCOMPLETE] PROMPT_NOT_FOUND: {p}——**本項未檢查，這不等於通過**")
        return 2
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"[INCOMPLETE] PROMPT_NOT_DECODABLE: {p}（{type(e).__name__}）"
              "——**未檢查 ≠ 通過**")
        return 2

    findings, exempt = [], []
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        # 內容槽整段跳過：它不是指涉，是輸入位
        scrub = CONTENT_SLOT.sub(" ", line)
        for pat, label in CROSSREF:
            for m in re.finditer(pat, scrub):
                if quoted(scrub, m.start()):
                    exempt.append(f"L{i}「{label}」")
                    continue
                findings.append(("FAIL", "CROSS_PROMPT_REFERENCE",
                                 f"L{i}：「{label}」——**在執行端等同空白**"))
        for m in BLOCK_SLOT.finditer(line):
            findings.append(("FAIL", "PROMPT_NOT_ASSEMBLED",
                             f"L{i}：{m.group(0)[:40]}——**零件尚未貼進成品**"))
        if FILL_SLOT.search(line):
            findings.append(("WARN", "TEMPLATE_NOT_FILLED", f"L{i}：尚有填空槽未填"))

    for pat, label in POLLUTION:
        if re.search(pat, text):
            findings.append(("FAIL", "PROMPT_POLLUTION",
                             f"{label}——**執行端每次重置，沒有跨次記憶**"))

    for label, pat in GENERIC_HINTS:
        if not re.search(pat, text):
            findings.append(("WARN", "GENERIC_CLAUSE_MISSING",
                             f"找不到{label}——這份 prompt 真的自足嗎？"))

    if a.profile == "deep-research":
        miss = [lab for pat, lab in DR_REQUIRED if not re.search(pat, text)]
        if miss:
            findings.append(("FAIL", "DR_CLAUSE_MISSING",
                             f"缺 {'、'.join(miss)}——缺任一項即表示該機制在這份 prompt 上不會生效"))

    fails = [f for f in findings if f[0] == "FAIL"]
    code = 1 if fails else 0

    if a.json:
        print(json.dumps({"sensor": "prompt_self_contained", "profile": a.profile,
                          "status": "FAIL" if fails else "PASS",
                          "findings": [{"level": l, "code": c, "message": m}
                                       for l, c, m in findings],
                          "quoted_exemptions": exempt}, ensure_ascii=False, indent=2))
        return code

    print(f"── Prompt 自足性 ｜ {p.name} ｜ profile={a.profile} " + "─" * 8)
    for l, c, m in findings:
        print(f"  [{l}] {c}: {m}")
    if exempt:
        # ⛔ 豁免必須看得見（「靜默過濾」家族）
        print(f"  ⚠️ 判定為**引述禁令**而豁免 {len(exempt)} 處：{'、'.join(exempt[:6])}"
              + ("…" if len(exempt) > 6 else ""))
        print("      理由：同一行內禁令標記出現在該詞之前。**豁免不是沒有發生。**")
    if a.profile != "deep-research":
        print("  ℹ️ **未執行** DR 專用條款表（8 項）——"
              "本 profile 不適用（⚠️ **不適用 ≠ 通過**）。")
        print("      要檢查 DR prompt 請加 `--profile deep-research`。")
    print(f"  結果：{'FAIL' if fails else 'PASS'}"
          f"（WARN {len(findings) - len(fails)} 項）")
    return code


if __name__ == "__main__":
    sys.exit(main())
