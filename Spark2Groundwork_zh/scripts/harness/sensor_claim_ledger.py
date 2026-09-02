#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：主張台帳（證據鏈環②）—— **本框架的支點**

## 它檢查什麼

**「那段話在不在原文裡」——用字串比對回答，零成本，任何人可複核。**

⛔ **它不檢查「那段話是否支持該主張」**（環⑥）。那是人的工作，**刻意不機械化**。
**錨點的作用是讓「有沒有人真的看過原文」變成可查的事實，不是替人看。**

## 兩項檢查

    ANCHOR_NOT_IN_SOURCE   錨點在提取物中查無                    FAIL
    CORPUS_MD_MODIFIED     提取物與 manifest 雜湊不符            FAIL

⚠️ **第二項是「允許 AI 寫入語料庫」的前提條件，不是附加品。**
錨點查證的全部效力來自「比對對象是程式化提取、模型未參與」這一件事。
**若可寫入者能更動該文本，證據鏈會從可驗證變成循環——而且是靜默的。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                      # noqa: E402
from anchor_norm import norm                       # noqa: E402

HEAD = re.compile(r"^###\s+(M-\d+)\s*$")
FIELD = re.compile(r"^-\s*\*\*(.+?)：\*\*\s*(.*)$")
PLACEHOLDER = re.compile(r"^(—|-|<<<.*>>>|)$")
SURNAME = re.compile(r"^\s*\**([A-Za-z一-鿿][\w一-鿿'’-]+)")


def parse(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = HEAD.match(line.rstrip())
        if m:
            cur = {}
            out[m.group(1)] = cur
            continue
        if cur is None:
            continue
        f = FIELD.match(line.rstrip())
        if f:
            cur[f.group(1).strip()] = f.group(2).strip()
    return out


def corpus_integrity(root, cfg, stats=None):
    """提取物完整性。

    ⚠️ **有三種狀態，⛔ 不是兩種。**「沒有語料庫」「有語料庫但裡面還是空的」
    「有語料庫但查不了」是三件不同的事：
      無目錄            → 本檢查不適用，靜默略過
      有目錄但無提取物   → 還沒有東西要保護，WARN
      有提取物但無 manifest → INCOMPLETE
    **一個判準涵蓋過廣，其代價是把「不適用」誤報成「有風險」。**

    🔴 **實測：** 框架開始隨附一個空的 `corpus_md/`，讓新使用者看得到提取物要放哪裡。
    **於是每一個新專案第一次執行都報 INCOMPLETE**——
    ⛔ **而一個一開始就狼來了的輸出，正是教會人忽略它的方式。**
    ⚠️ **這與先前一個缺陷同型：** 某支工具先建好輸出目錄，才去看有沒有東西要放進去。
    ⛔ **修法是結構性的，不是加豁免（`R-20`／`R-21`）：判準改為看「有沒有提取物」，
    ⛔ 而不是看「目錄在不在」。**

    🔴 **`B-3`（裁決 48）：本函式逐檔重算雜湊的筆數，⛔ 必須印在統計欄。**
    ⚠️ **實測理由（兩次，兩個不同的人）：** v1.3.0 的稽核者找不到「哪一支感測器在比對
    `_manifest.json`」，2026-09-02 專案 D 的使用者又寫了一次「我至今找不到」。
    **⛔ 而它一直都在這裡。** ⇒ **一個看不見的保護，與沒有那個保護，在畫面上長得一樣。**
    """
    stats = {} if stats is None else stats
    stats.setdefault("hash_compared", 0)
    out = []
    cdir = root / cfg["corpus_dir"]
    if not cdir.is_dir():
        return out
    mp = root / cfg["corpus_manifest"]
    extracts = sorted(cdir.glob("*.md"), key=lambda p: p.as_posix())
    if not extracts and not mp.exists():
        return [("WARN", "CORPUS_EMPTY",
                 f"{cfg['corpus_dir']}/ 裡還沒有提取物——"
                 "**沒有東西要保護，⛔ 也等於沒有查過任何東西**。"
                 "把 PDF 放進原文資料夾，再跑一次提取工具")]
    if not mp.exists():
        return [("INCOMPLETE", "CORPUS_MANIFEST_MISSING",
                 f"{cfg['corpus_dir']}/ 存在但找不到 manifest——"
                 "**提取物不受竄改偵測保護，本項未檢查，這不等於通過**")]
    try:
        man = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e:                                    # noqa: BLE001
        return [("INCOMPLETE", "CORPUS_MANIFEST_UNREADABLE", f"manifest 無法解析：{e}")]
    known = {e["md"]: e.get("md_sha256") for e in man if "md" in e}
    for f in sorted(cdir.glob("*.md"), key=lambda p: p.as_posix()):
        want = known.get(f.name)
        if want is None:
            out.append(("WARN", "CORPUS_FILE_UNTRACKED",
                        f"{f.name} 不在 manifest 中——新增文獻後請重跑提取工具"))
            continue
        stats["hash_compared"] += 1
        if hashlib.sha256(f.read_bytes()).hexdigest() != want:
            out.append(("FAIL", "CORPUS_MD_MODIFIED",
                        f"{f.name} 內容已與 manifest 不符——"
                        "**比對對象被更動，本輪所有錨點結果皆不可信**"))
    for name in known:
        if not (cdir / name).exists():
            out.append(("FAIL", "CORPUS_FILE_DELETED", f"{name} 已消失但仍列於 manifest"))
    return out


def main():
    root, cfg, as_json, name = cli("claim_ledger")
    cstats = {}
    findings = corpus_integrity(root, cfg, cstats)
    led = root / cfg["claim_ledger"]
    if not led.exists():
        findings.append(("INCOMPLETE", "CLAIM_LEDGER_MISSING",
                         f"找不到 {cfg['claim_ledger']}——**本項未檢查，這不等於通過**"))
        return emit("主張台帳感測器", findings,
                    {"逐檔比對雜湊": f"{cstats['hash_compared']} 份"}, as_json, name)

    entries = parse(led.read_text(encoding="utf-8"))
    cdir = root / cfg["corpus_dir"]
    corpus = {p.name: norm(p.read_text(encoding="utf-8", errors="replace"))
              for p in cdir.glob("*.md")} if cdir.is_dir() else {}
    checked = matched = 0

    for cid, f in entries.items():
        anchor = f.get("原句錨點", "").strip().strip("`")
        src = f.get("來源", "")
        if PLACEHOLDER.match(anchor) or "<<<" in anchor:
            findings.append(("WARN", "ANCHOR_EMPTY", f"{cid} 原句錨點為空或仍是樣板"))
            continue
        if not corpus:
            findings.append(("INCOMPLETE", "CORPUS_ABSENT",
                             f"{cid} 無法比對：語料庫為空——**未檢查 ≠ 通過**"))
            continue
        m = SURNAME.match(src)
        key = m.group(1).lower() if m else ""
        cands = [t for n, t in corpus.items() if key and key in n.lower()] or list(corpus.values())
        checked += 1
        if any(norm(anchor) in t for t in cands):
            matched += 1
        else:
            findings.append(("FAIL", "ANCHOR_NOT_IN_SOURCE",
                             f"{cid} 錨點在語料庫中查無：「{anchor[:56]}…」"))

    code = emit("主張台帳感測器", findings,
                {"主張筆數": len(entries), "提取檔": len(corpus),
                 "逐檔比對雜湊": f"{cstats['hash_compared']} 份",
                 "錨點查證": f"{matched}/{checked} 命中"}, as_json, name)
    if not as_json:
        print("      ⚠️ 本感測器只驗錨點存在，不驗原文是否支持該主張（環⑥⑦）")
    return code


if __name__ == "__main__":
    sys.exit(main())
