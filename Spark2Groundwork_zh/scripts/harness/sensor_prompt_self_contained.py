#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
計算型感測器：Prompt 自足性（Prompt Self-Containment Sensor）
證據鏈位置：① 文獻搜尋之上游——Prompt 本身

AGENTS.md DR 規範第 11 條：**每份 DR Prompt 必須完全自足。**
DR 各次執行於獨立對話視窗，彼此不共享上下文，故「同上」「參見前述」
「Same as R3-1」在執行端**等同空白**——被指涉的條款實質上不存在。

⚠️ 本感測器的存在，是因為規則本身擋不住這個錯誤：
2026-07-28，Opus 5 在同一份文件的 §1 引述了第 11 條（「不得寫『同上』」），
然後在下半部的 R3-2～R3-5 寫了「Same as R3-1」。**引述規則與違反規則同處一檔。**
實測後果：R3-4 的 `[NO-DOI]` 標記使用 0 次（定義從未出現在該 Prompt 內），
而條款完整的 R3-5 使用 12 次。

用法： python3 sensor_prompt_self_contained.py <prompt文件.md> [--json]
退出碼： 0=PASS  1=FAIL  2=執行錯誤
"""
import re, os, sys, json, argparse

# 跨 Prompt 指涉（執行端等同空白）
CROSSREF_PAT = [
    (r'(?i)\bsame as\s+R?\d', 'Same as R#'),
    (r'(?i)\bas (?:in|above|described above)\b[^\n]{0,20}R?\d', 'as in R#'),
    (r'(?i)\bsee (?:above|R\d|section)', 'see above/R#'),
    (r'同\s*上', '同上'),
    (r'參\s*見\s*前\s*述', '參見前述'),
    (r'如\s*前\s*所\s*述', '如前所述'),
    (r'(?i)\bditto\b', 'ditto'),
]
# Prompt 汙染：對 DR 無意義的內容（DR 每次執行皆重置，無跨次記憶）
# 2026-07-28 使用者發現：Opus 5 與 3.1 Pro 都把「本次改版原因」「前一版問題點」
# 寫進 Prompt 程式碼區塊內。DR 不知道「R3-1 v2」是誰，也不知道「已廢止」指什麼。
# 兩位審計者皆未發現，是人工審查抓到的。
POLLUTION_PAT = [
    (r'R3-\d\s*v\d', '版本代號（DR 無跨次記憶）'),
    (r'(?i)\bv[123]\s*(?:的|之)', '版本指涉'),
    (r'已廢止|前一版|上一版|先前版本', '改版沿革'),
    (r'實測：|觸發個案|觸發此', '內部實測記錄'),
    (r'（見[^）]*評估|見\s*`[^`]*Assessment', '內部文件指涉'),
    (r'(?i)\bthis (?:was|is) (?:a )?(?:hallucinat|fabricat)', '內部失效敘述'),
]

# 每份 Prompt 都必須自帶的關鍵條款（缺一即為不自足）
REQUIRED = [
    (r'\[LANG:', 'LANG 標籤定義'),
    (r'\[VENUE-TYPE:', 'VENUE-TYPE 標籤定義'),
    (r'\[NO-DOI', 'NO-DOI 機制'),
    (r'(?i)PASS A', 'PASS A 英文檢索'),
    (r'(?i)PASS B', 'PASS B 中文檢索'),
    (r'(?i)TITLE ACCURACY|paraphrase, shorten, or improve', '標題精確性條款'),
    (r'(?i)NONE RETRIEVED', '枚舉版 NONE RETRIEVED'),
    (r'(?i)OUTPUT CONTRACT', 'OUTPUT CONTRACT'),
]

def split_prompts(text, whole_file=False):
    """以 ``` 圍欄切出各 Prompt 區塊；`.txt` 純淨 Prompt 則整檔視為一份"""
    if whole_file:
        return [('(整檔)', text)]
    out = []
    for m in re.finditer(r'```(.*?)```', text, re.S):
        body = m.group(1)
        if len(body) < 400:
            continue
        head = text[:m.start()]
        titles = re.findall(r'^#{2,3}\s*(.+)$', head, re.M)
        out.append((titles[-1].strip() if titles else '(未命名)', body))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if not os.path.exists(a.target):
        print('SENSOR ERROR: 找不到 %s' % a.target); sys.exit(2)
    raw = open(a.target, encoding='utf-8').read()
    # `prompts/` 內之 .txt 為純淨交付版：整檔即一份 Prompt，無 ``` 圍欄
    whole = a.target.endswith('.txt')
    # 已執行之 Prompt 檔（標有「已執行，勿重跑」）降為資訊性——
    # 其缺陷已成既成事實，阻擋進版無意義；但仍須顯示，因為它解釋了該輪的產出品質。
    archived = ('已執行，勿重跑' in raw or '已執行、勿重跑' in raw
                or '本檔為「設計文件」' in raw)
    prompts = split_prompts(raw, whole_file=whole)
    if not prompts:
        print('SENSOR ERROR: 檔內找不到 ``` 圍欄之 Prompt 區塊（.md）'); sys.exit(2)

    fails = []
    for name, body in prompts:
        cross = [lab for pat, lab in CROSSREF_PAT if re.search(pat, body)]
        miss = [lab for pat, lab in REQUIRED if not re.search(pat, body)]
        poll = [lab for pat, lab in POLLUTION_PAT if re.search(pat, body)]
        if poll:
            fails.append(('PROMPT_POLLUTION', '%s ← %s' % (name[:44], '、'.join(poll))))
        if cross:
            fails.append(('CROSS_PROMPT_REFERENCE', '%s ← %s' % (name[:44], '、'.join(cross))))
        if miss:
            fails.append(('REQUIRED_CLAUSE_MISSING', '%s ← 缺 %s' % (name[:44], '、'.join(miss))))

    if a.json:
        print(json.dumps({'prompts': len(prompts), 'fails': fails}, ensure_ascii=False, indent=1))
        sys.exit(1 if fails else 0)

    print('═' * 62)
    print('Prompt 自足性感測器 ｜ %s' % os.path.basename(a.target))
    print('═' * 62)
    print('偵測到 %d 份 Prompt' % len(prompts))
    print()
    if not fails:
        print('✅ PASS — 各 Prompt 皆自足。'); sys.exit(0)
    if archived:
        print('ℹ️  本檔標記為「已執行，勿重跑」→ 以下為**資訊性**，不阻擋進版。')
        print('   （這些缺陷已成既成事實，但它們解釋了該輪的產出品質）')
        print()

    HINT = {
        'CROSS_PROMPT_REFERENCE':
            'Prompt 內含跨 Prompt 指涉。→ **DR 各次執行不共享上下文，'
            '「同上」在執行端等同空白**，被指涉的條款實質不存在。\n'
            '     實測：R3-4 因 SOURCE STANDARDS 寫「Same as R3-1」，`[NO-DOI]` 使用 0 次；\n'
            '     條款完整的 R3-5 使用 12 次。**請逐字複製完整條款，不得省略。**',
        'PROMPT_POLLUTION':
            'Prompt 內含對 DR 無意義的內容（改版理由／版本代號／內部實測記錄）。\n'
            '     → **DR 每次執行皆重置，沒有跨次記憶**——它不知道「R3-1 v2」是誰，\n'
            '     也不知道「已廢止」指什麼。這些文字佔篇幅、增加誤解風險，且與任務無關。\n'
            '     **改版理由應寫在評估報告，不寫在 Prompt。** 純淨版見 `prompts/`。',
        'REQUIRED_CLAUSE_MISSING':
            '缺少必備條款。→ 每份 Prompt 都須自帶：標籤定義（LANG／VENUE-TYPE）、\n'
            '     NO-DOI 機制、雙語 PASS A/B、標題精確性、枚舉版 NONE RETRIEVED、OUTPUT CONTRACT。\n'
            '     缺任一項即表示該機制在這份 Prompt 上不會生效。',
    }
    for code in ('CROSS_PROMPT_REFERENCE', 'PROMPT_POLLUTION', 'REQUIRED_CLAUSE_MISSING'):
        items = [i for c, i in fails if c == code]
        if not items:
            continue
        print('❌ FAIL [%s] ×%d' % (code, len(items)))
        for it in items[:10]:
            print('     • %s' % it[:100])
        print('   → 修復指示：%s' % HINT[code])
        print()
    print('═' * 62)
    print('判定：%s' % ('INFO（已執行檔案，不阻擋）' if archived else 'FAIL'))
    sys.exit(0 if archived else 1)

if __name__ == '__main__':
    main()
