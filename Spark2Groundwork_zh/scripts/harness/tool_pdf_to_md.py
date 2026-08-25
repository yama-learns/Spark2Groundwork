#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF → Markdown 提取工具（證據鏈第②層的基礎建設）

**這支工具本身不省任何 token。** 它的唯一價值是讓「這段話在不在原文裡」
變成一次字串比對——把主張台帳的錨點查證成本降為零。

設計原則
--------
* **純程式提取，不經任何模型。** 模型不參與，就不會有「以自撰摘要冒充原文」
  這一型失效（先行專案曾發生：宣稱完成 71 頁提取，實際以摘要與佔位符填補，
  僅完成 18%，而作者與年份皆正確故無法由書目檢查偵測）。
* **逐頁加 `<!-- page: N -->` 標記**，使錨點可回溯到頁。
* **不做任何清理、改寫、正規化。** 提取物與 PDF 文字層逐字相同。
  ⛔ **特別是不得還原跨行斷字**——`anchor_norm.py` 會在**比對時**處理它；
  在提取時處理等於把正規化寫回了一側（`R-28`）。

## 後端：PyMuPDF 優先，pypdf 後備

**觸發個案：** 同一批 11 篇論文的兩份提取物互測，錨點嚴格命中率僅 62.5%；
去除空白與標點後為 95.7%。**33.2 個百分點純粹是空白與連字號差異，內容相同。**

**根因：** pypdf 在部分 PDF 上遺失行尾空白，產生 `leadsto`、`havethe` 這類黏字，
而 `anchor_norm.py` 可以壓縮空白，**卻無法插入不存在的空白**。
→ 錨點查證會產生大量假陽性，而 `R-19`：**一支會對正確文本報警的感測器，會教人忽略它。**
**處置是修提取器，不是修比對器**（憲章 §7.3 第 1 步；`R-20`）。

⚠️ **後端名稱寫進檔頭與 manifest。** 某競品工具在主後端失敗時會**靜默改用另一條路徑而不留標記**
——兩種提取物混在同一批，而檔案裡看不出是哪一種。**降級可以，靜默不行。**

## manifest 的提取品質自檢

每份提取物登錄 `selfcheck_hit`：自它**自己**抽 N 個句子，套 `anchor_norm` 後回測它自己。

> **這個數字應該是 100%。不是 100% 就代表「照抄一句原文再拿去比對」這個動作本身會失敗**
> ——而那正是主張台帳每一筆都在做的事。

⛔ **本檔刻意不量「黏字率」。** 要判斷 `leadsto` 是不是黏字需要詞典，
而一支用啟發式猜黏字的檢查會對正確文本報警（`R-19`）。
**黏字只能靠兩份提取物互比才測得出來 → 用 `tool_extract_compare.py`。**

用法
----
  python3 tool_pdf_to_md.py [--pdf-dir <src>] [--out-dir <dst>] [--force]

  ⛔ 兩個預設值取自 `framework_config.py`（`pdf_dir`／`corpus_dir`）——路徑的單一定義處。
     不要在本檔硬編，那正是憲章 §3.2 記載的「三個目錄名」個案。

需要
----
  pip install pymupdf      # 主後端
  pip install pypdf        # 後備後端（選用）

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（查不了。**⛔ 這不等於通過**）
"""

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ⛔ 輸出編碼必須先固定成 UTF-8，⛔ 否則 Windows 上印到第一個符號就當掉。
#    唯一定義處：`_common._force_utf8`（見該處的實測個案）。
from _common import _force_utf8                            # noqa: E402
_force_utf8()
from framework_config import ROOT, load                      # noqa: E402
from anchor_norm import norm_for_anchor                      # noqa: E402

HEADER = """<!-- 本檔由 scripts/harness/tool_pdf_to_md.py 自 PDF 文字層程式化提取。
     未經任何模型處理，未做清理或改寫，與 PDF 文字層逐字相同。
     ⛔ 跨行斷字刻意未還原——還原屬於比對時的正規化（anchor_norm.py），不寫回本側。
     ⚠️ 提取物不得取代原文 PDF 作為最終引用依據；涉及關鍵數值時仍須回查 PDF。
     來源檔：{src}
     提取後端：{backend}
     PDF 頁數：{pages}
     提取字元：{chars}
     平均字元／頁：{density}
     自檢命中率：{selfcheck}
     來源指紋（PDF SHA-256 前 16 碼）：{fp}
-->

"""

COMMENT = re.compile(r"<!--.*?-->", re.S)
PAGE = re.compile(r"<!--\s*page:\s*\d+\s*-->")


def extract_pymupdf(pdf):
    """PyMuPDF 文字層抽取。**逐頁**，不合併、不重排、不還原斷字。"""
    import pymupdf
    doc = pymupdf.open(str(pdf))
    pages = [page.get_text("text") or "" for page in doc]
    doc.close()
    return pages


def extract_pypdf(pdf):
    """後備後端。⚠️ 已知在部分 PDF 上遺失行尾空白，見檔頭。"""
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]


BACKENDS = [("pymupdf", extract_pymupdf), ("pypdf", extract_pypdf)]


def _sent(text):
    out = []
    for s in re.split(r"(?<=[.!?。！？])\s+", COMMENT.sub(" ", text)):
        s = " ".join(s.split())
        if 60 <= len(s) <= 200 and sum(c.isalpha() for c in s) > 40:
            out.append(s)
    return out


def sentences(body):
    """抽出**合法的**錨點候選句，並回報有幾句因跨頁而被排除。

    ⚠️ **為什麼要逐頁抽，而不是整檔抽（實測個案）：**
    首版對 MAGIC 那篇實測得到 93.3%，兩筆未命中**全部是跨越 `<!-- page: N -->` 標記的句子**。
    原因是候選句這一側把註解換成了空白，而 haystack 那一側還留著註解——**必然落空。**

    ⛔ **依憲章 §7.3：先假設壞掉的是工具。壞的是這個檢查器，不是提取物。**

    ⚠️ 但更重要的是第二層：**一個跨頁的句子本來就不是合法錨點**——
    主張台帳的「頁」欄只能填一個頁碼。**它不該被抽中，也不該被算成失敗。**
    → 因此逐頁切開再抽句；跨頁的候選句**只回報數量，不計入命中率**。
    """
    chunks = PAGE.split(body)
    per_page = []
    for ch in chunks:
        per_page.extend(_sent(ch))
    ok = set(per_page)
    spanning = sum(1 for s in _sent(body) if s not in ok)
    return per_page, spanning


def selfcheck(body, n=30, seed=20260819):
    """自回測：從提取物自己抽句，套同一組正規化後回測它自己。

    ⚠️ **應為 100%。** 低於 100% 代表「照抄一句原文再拿去比對」本身會失敗——
    而主張台帳的每一筆錨點都在做這個動作。
    ⛔ 這不是提取品質的度量，是**錨點工作流是否成立**的度量。
    """
    cand, spanning = sentences(body)
    if not cand:
        return None, 0, spanning
    random.seed(seed)
    smp = random.sample(cand, min(n, len(cand)))
    hay = norm_for_anchor(body)
    hit = sum(1 for s in smp if norm_for_anchor(s) in hay)
    return hit / len(smp), len(smp), spanning


def convert(pdf: Path, out: Path):
    fp = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
    pages, backend, errors = None, None, []
    for name, fn in BACKENDS:
        try:
            pages = fn(pdf)
            backend = name
            break
        except Exception as e:                                # noqa: BLE001
            # ⛔ 不得靜默降級：每一次退回都要留下痕跡
            errors.append(f"{name}: {type(e).__name__}: {e}")
    if pages is None:
        raise RuntimeError("所有後端皆失敗 —— " + " ｜ ".join(errors))

    total = sum(len(t) for t in pages)
    n = len(pages)
    density = round(total / n) if n else 0
    body = "\n".join(f"<!-- page: {i} -->\n{t}\n" for i, t in enumerate(pages, 1))
    rate, sn, span = selfcheck(body)
    sc = "無足夠句子可測" if rate is None else f"{rate*100:.1f}%（抽樣 {sn} 句）"

    head = HEADER.format(src=pdf.name, backend=backend, pages=n, chars=total,
                         density=density, selfcheck=sc, fp=fp)
    if errors:
        head += ("<!-- ⚠️ 後端降級紀錄（**不是無害的實作細節**：不同後端的提取物不可互換）：\n     "
                 + "\n     ".join(errors) + "\n-->\n\n")
    out.write_text(head + body, encoding="utf-8")

    # ⚠️ fingerprint 是**來源 PDF** 的雜湊，md_sha256 是**提取物本身**的雜湊。
    #    前者證明「這份 md 出自哪一份 PDF」；後者讓「這份 md 有沒有被事後改過」可機械偵測。
    #    **錨點比對的對象若可被寫入者更動，整條證據鏈就是循環的。**
    return {"src": pdf.name, "md": out.name, "backend": backend, "pages": n,
            "chars": total, "density": density,
            "selfcheck_hit": None if rate is None else round(rate, 4),
            "selfcheck_n": sn, "anchors_spanning_pages": span,
            "degraded_from": errors or None,
            "md_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}


def main() -> int:
    cfg = load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default=cfg.get("pdf_dir", "corpus"))
    ap.add_argument("--out-dir", default=cfg.get("corpus_dir", "corpus_md"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src_dir, out_dir = ROOT / args.pdf_dir, ROOT / args.out_dir
    pdfs = sorted(src_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[FAIL] SCAN_GLOB_MATCHES_NOTHING: {args.pdf_dir}/ 中沒有 PDF"
              "——掃不到的地方等於沒有感測器")
        return 2

    # ⚠️ 建立輸出目錄**必須在確認有 PDF 之後**。
    #    實測個案：無 PDF 時仍先 mkdir，於是一次誤跑就在專案裡留下一個空的 corpus_md/，
    #    而 sensor_claim_ledger.py 對「目錄存在但沒有 manifest」報 INCOMPLETE
    #    ——**整套 harness 從 0 變成 2，而原因只是一個沒有任何內容的空資料夾。**
    #    ⚠️ 而 git 不追蹤空目錄，所以它不會出現在任何一份變更清單裡。
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest, low, degraded, failed, badself = [], [], [], [], []
    for pdf in pdfs:
        out = out_dir / (pdf.stem + ".md")
        if out.exists() and not args.force:
            print(f"  跳過（已存在，加 --force 覆寫）：{out.name}")
            continue
        try:
            rec = convert(pdf, out)
        except Exception as e:                                # noqa: BLE001
            print(f"  [FAIL] EXTRACTION_ERROR: {pdf.name} — {type(e).__name__}: {e}")
            failed.append(pdf.name)
            continue
        manifest.append(rec)
        if rec["degraded_from"]:
            degraded.append(rec)
        # ⚠️ 判準為「平均字元／頁 < 400」，不是「零字元」。
        #    出版社浮水印可使每頁有數十字元，零字元判準會漏判掃描檔。
        if rec["density"] < 400:
            low.append(rec)
        if rec["selfcheck_hit"] is not None and rec["selfcheck_hit"] < 1.0:
            badself.append(rec)
        sflag = "" if rec["selfcheck_hit"] is None else f" / 自檢 {rec['selfcheck_hit']*100:.0f}%"
        flag = "  🔴 文字層可能不可用" if rec["density"] < 400 else ""
        print(f"  ✅ {out.name}  {rec['pages']} 頁 / {rec['chars']} 字元 / "
              f"{rec['density']} 每頁 / {rec['backend']}{sflag}{flag}")

    mf = out_dir / "_manifest.json"
    existing = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else []
    by_src = {r["src"]: r for r in existing}
    by_src.update({r["src"]: r for r in manifest})
    mf.write_text(json.dumps(sorted(by_src.values(), key=lambda r: r["src"]),
                             ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  清單：{mf.relative_to(ROOT)}（{len(by_src)} 筆）")

    # ── 孤兒檢查：manifest 有紀錄但 md 不在，或 md 在而 manifest 沒有 ──
    # ⚠️ 語料庫目錄被人工搬動過一次，而**搬動本身不會產生任何錯誤訊息**。
    on_disk = {p.name for p in out_dir.glob("*.md")}
    in_mf = {r["md"] for r in by_src.values()}
    rc = 0
    if on_disk - in_mf:
        print(f"  [FAIL] CORPUS_ORPHAN_MD: {len(on_disk - in_mf)} 份 .md 不在清單內"
              "——**它們不受竄改偵測保護，且來源不明**：")
        for m in sorted(on_disk - in_mf):
            print(f"      - {m}")
        rc = 1
    if in_mf - on_disk:
        print(f"  [FAIL] CORPUS_ORPHAN_MANIFEST: {len(in_mf - on_disk)} 筆清單紀錄找不到對應檔案：")
        for m in sorted(in_mf - on_disk):
            print(f"      - {m}")
        rc = 1
    if degraded:
        print(f"  ⚠️ {len(degraded)} 份使用了後備後端（**不同後端的提取物不可互換**）：")
        for r in degraded:
            print(f"      - {r['src']} → {r['backend']}")
    if badself:
        print(f"  🔴 {len(badself)} 份自檢命中率 < 100%——"
              "**「照抄一句原文再拿去比對」在這些檔案上會失敗，而台帳每一筆都在做這件事**：")
        for r in badself:
            print(f"      - {r['src']}（{r['selfcheck_hit']*100:.1f}%，抽樣 {r['selfcheck_n']} 句）")
        print("      → ⛔ 不要調鬆比對判準（R-20）。先用 tool_extract_compare.py "
              "跟另一個後端互比，確認壞的是提取器還是正規化。")
        rc = max(rc, 1)
    if low:
        print(f"  ⚠️ {len(low)} 份平均字元／頁 < 400，文字層可能不可用，"
              f"錨點查證對這些檔案不可靠：")
        for r in low:
            print(f"      - {r['src']}（{r['density']} 字元／頁）")
        return 2
    if failed:
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
