#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取物互換性檢定 —— **兩份提取物能不能當同一個錨點比對對象？**

## 這支工具回答什麼

主張台帳的錨點查證（證據鏈環②）是一次字串比對：**「這句話在不在提取物裡」。**
因此當同一批 PDF 存在兩份不同工具、不同後端或不同時間產生的提取物時，
必須先回答一件事：**它們可以互換嗎？**

⚠️ **「兩份都讀得懂」不等於「可以互換」。** 錨點比對不看可讀性，只看逐字命中。

## 它怎麼測

自 A 側抽取 60–200 字元的完整句子當錨點，測它能否在 B 側命中。
**兩側套用同一個正規化函式**（`anchor_norm.py`，單一定義處，`R-27`）。

同時做第二次比對：**去除所有空白與標點**後再測一次。
兩者的差額即為「純粹是空白／連字號差異，內容相同」的比例——

⚠️ **這一欄是本工具存在的理由。** 它區分了兩個完全不同的問題：

    差額大  → 兩份文字內容相同，差在斷字與空白 → 這是**正規化涵蓋範圍**的問題
    差額小  → 兩份的文字內容本身就不同         → 這是**提取品質**的問題

**把前者當成後者處理，會去修一個沒有壞的提取器。**（憲章 §7.3 第 1 步）

⚠️ **觸發個案：** 有人先跑了單向檢定得到 62.5%，正準備回報「這份提取物不可用」；
去除空白與標點後命中率是 95.7%——**33.2 個百分點純粹是空白差異，內容相同。**
**壞掉的是提取器的空白處理，不是被檢查的產物。**

## 用法

    python3 tool_extract_compare.py --a corpus_md --b corpus_md_old
    python3 tool_extract_compare.py --a corpus_md --b corpus_md_old --n 40 --seed 20260819

⚠️ **路徑相對於專案根目錄。** 兩側須有同名 `.md` 檔才會被比對。

退出碼：0 = 已完成比對（⚠️ **不代表兩份可互換，判斷仍是人的**）｜2 = 無法比對
"""
import argparse
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ 輸出編碼必須先固定成 UTF-8，⛔ 否則 Windows 上印到第一個符號就當掉。
#    唯一定義處：`_common._force_utf8`（見該處的實測個案）。
from _common import _force_utf8                            # noqa: E402
_force_utf8()
from anchor_norm import norm_for_anchor                      # noqa: E402
from framework_config import ROOT                            # noqa: E402

HARD = re.compile(r"[^0-9a-z一-鿿]")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def hard(s):
    """寬鬆側：去除所有空白與標點，只留字母數字與漢字。"""
    return HARD.sub("", s.lower())


def sentences(text):
    text = COMMENT.sub(" ", text)
    text = re.sub(r"[*_#`|]", " ", text)
    out = []
    for s in re.split(r"(?<=[.!?。！？])\s+", text):
        s = " ".join(s.split())
        if 60 <= len(s) <= 200 and sum(c.isalpha() for c in s) > 40:
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="錨點來源側（自這一側抽句）")
    ap.add_argument("--b", required=True, help="被查側（測錨點能否在這裡命中）")
    ap.add_argument("--n", type=int, default=40, help="每篇抽樣句數")
    ap.add_argument("--seed", type=int, default=20260819)
    args = ap.parse_args()

    A, B = ROOT / args.a, ROOT / args.b
    files = sorted(A.glob("*.md"), key=lambda p: p.as_posix())
    if not files:
        print(f"[FAIL] SCAN_GLOB_MATCHES_NOTHING: {args.a}/ 中沒有 .md"
              "——掃不到的地方等於沒有感測器")
        return 2

    random.seed(args.seed)
    print(f"錨點抽自：{args.a}　　被查側：{args.b}　　seed={args.seed}")
    print(f"{'檔案':46} {'抽樣':>4} {'嚴格':>6} {'寬鬆':>6} {'差額':>6}")
    print("-" * 78)
    tn = ts = th = 0
    missing = []
    for fa in files:
        fb = B / fa.name
        if not fb.exists():
            missing.append(fa.name)
            continue
        ta, tb = fa.read_text(encoding="utf-8"), fb.read_text(encoding="utf-8")
        soft_hay, hard_hay = norm_for_anchor(tb), hard(tb)
        cand = sentences(ta)
        if not cand:
            continue
        smp = random.sample(cand, min(args.n, len(cand)))
        s = sum(1 for x in smp if norm_for_anchor(x) in soft_hay)
        h = sum(1 for x in smp if hard(x) in hard_hay)
        tn += len(smp); ts += s; th += h
        print(f"{fa.stem[:44]:46} {len(smp):>4} {s/len(smp)*100:>5.1f}% "
              f"{h/len(smp)*100:>5.1f}% {(h-s)/len(smp)*100:>5.1f}%")
    print("-" * 78)
    if not tn:
        print("[FAIL] 兩側沒有任何同名檔案可比對")
        return 2
    print(f"{'合計':46} {tn:>4} {ts/tn*100:>5.1f}% {th/tn*100:>5.1f}% {(th-ts)/tn*100:>5.1f}%")
    print()
    print("  嚴格＝套用 anchor_norm（保留空白）── **這才是感測器實際用的比對**")
    print("  寬鬆＝再去除所有空白與標點")
    print(f"  差額＝{(th-ts)/tn*100:.1f}%　純粹空白／連字號差異，**內容相同**")
    print(f"  內容層真差異＝{100-th/tn*100:.1f}%")
    print()
    print("  → 差額大而真差異小：問題在**正規化涵蓋範圍**，⛔ 不要去修提取器")
    print("  → 差額小而真差異大：問題在**提取品質**，⛔ 不要去調鬆比對判準（R-20）")
    if missing:
        print(f"\n  ⚠️ {len(missing)} 份在被查側找不到同名檔案（未計入）：")
        for m in missing[:5]:
            print(f"      - {m}")
        if len(missing) > 5:
            print(f"      …… 另 {len(missing)-5} 份")
    print("\n  ⛔ 本工具不判定哪一份提取物比較好——它只回答「能不能互換」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
