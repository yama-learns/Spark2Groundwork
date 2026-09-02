#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""錨點比對之正規化函式 —— **單一定義處**（`file_index.md` §0 登錄）。

## 為什麼需要它

主張帳的「原句錨點」要求逐字引錄，並在 `corpus_md/*.md`（程式化提取）中字串比對命中。
**但 PDF 提取必然產生下列變形，而它們每一個都會使逐字比對失敗：**

    跨行斷字      individ-\\nual differences
    軟連字號      individ­ual
    連字 ligature ﬁ ﬂ ﬀ ﬃ ﬄ
    全半形        （2024） vs (2024)
    引號          "…" vs “…”／‘…’
    多重空白      N  =  40
    不斷行空格    \\u00a0

失效方向是「查無」→ FAIL，於是**大量假陽性**，
而假陽性會教人忽略感測器（`RULES.md` R-19 精度優先於覆蓋）。

## 兩條硬性設計

1. **兩側必須套用同一個函式。** 單側正規化＝自製假陽性（`RULES.md` R-27）。
2. **正規化只在比對時發生，不寫回任何一側。**
   ⛔ 絕不可把正規化結果寫回 `corpus_md/*.md`——那會使雜湊防線失效，
   且提取物一經模型改寫，錨點查證就從可驗證變成循環（P2 §11.4 的洞見）。

## 順序不可調換（`RULES.md` R-27 的⚠️ 條）

    ①還原跨行斷字 → ②軟連字號 → ③ligature → ④全形 → ⑤引號 → ⑥空白壓縮

⚠️ **①必須在⑥之前。** 否則 `individ-\\nual` 會先被壓成 `individ- ual`，
再壓成 `individ-ual`，**永遠接不回去**。
"""
import re
import unicodedata

LIGATURES = {'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl',
             'ﬃ': 'ffi', 'ﬄ': 'ffl', 'ﬅ': 'st', 'ﬆ': 'st'}
QUOTES = {'“': '"', '”': '"', '‘': "'", '’': "'",
          '″': '"', '′': "'", '«': '"', '»': '"'}
DASHES = {'‐': '-', '‑': '-', '‒': '-', '–': '-',
          '—': '-', '―': '-', '−': '-'}


def norm_for_anchor(s):
    """回傳供錨點比對用的正規化字串。**兩側都必須經過本函式。**"""
    # ① 還原跨行斷字（必須最先做）
    #    ⚠️ **空白須涵蓋「換行」與「一般空格」兩種。**
    #    理由：錨點是人抄的，**抄寫時常把換行變成空格**——
    #    原文 `con-\nventional`，而台帳記成 `con- ventional`。
    #    只處理 `-\n` 會使兩側正規化不對稱，**原本通過的錨點會當場失敗**（實測 2 筆）。
    #    ⛔ 本規則會誤合少數合法斷字（`pre- and` → `preand`），**那是可接受的**：
    #    正規化只用於比對，且兩側套用同一個函式——**對稱的誤合不造成假陰性。**
    #    **會殺死比對的是不對稱，不是激進。**
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)
    # 一般換行轉空白（斷字已處理完）
    s = re.sub(r'\r?\n', ' ', s)
    # ② 軟連字號
    s = s.replace('­', '')
    # ③ ligature
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    # ④ 全形 → 半形（NFKC 一併處理全形括號、數字、標點）
    s = unicodedata.normalize('NFKC', s)
    # ⑤ 引號與各式連字號統一
    for k, v in QUOTES.items():
        s = s.replace(k, v)
    for k, v in DASHES.items():
        s = s.replace(k, v)
    # ⑥ 空白壓縮（含不斷行空格）
    s = s.replace(' ', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


if __name__ == '__main__':
    import sys
    print(norm_for_anchor(sys.stdin.read()))


# 別名：本框架的感測器一律 `from anchor_norm import norm`
norm = norm_for_anchor
