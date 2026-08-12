#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF → Markdown 提取工具（證據鏈第②層的基礎建設）

**這支工具本身不省任何 token。** 它的唯一價值是讓「這段話在不在原文裡」
變成一次字串比對——把主張台帳的錨點查證成本降為零。

設計原則
--------
* **純程式提取，不經任何模型。** 模型不參與，就不會有「以自撰摘要冒充原文」
  這一型失效（參考專案曾發生：宣稱完成 71 頁提取，實際以摘要與佔位符填補，
  僅完成 18%，而作者與年份皆正確故無法由書目檢查偵測）。
* **逐頁加 `<!-- page: N -->` 標記**，使錨點可回溯到頁。
* **不做任何清理、改寫、正規化。** 提取物與 PDF 文字層逐字相同。
  任何「順手修正」都會使錨點比對失效，且失效方向是靜默的。

用法
----
  python3 tool_pdf_to_md.py --paper-dir paper --out-dir paper_md [--force]
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HEADER = """<!-- 本檔由 scripts/harness/tool_pdf_to_md.py 自 PDF 文字層程式化提取。
     未經任何模型處理，未做清理或改寫，與 PDF 文字層逐字相同。
     ⚠️ 提取物不得取代原文 PDF 作為最終引用依據；涉及關鍵數值時仍須回查 PDF。
     來源檔：{src}
     PDF 頁數：{pages}
     提取字元：{chars}
     平均字元／頁：{density}
     來源指紋（PDF SHA-256 前 16 碼）：{fp}
-->

"""


def convert(pdf: Path, out: Path):
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    fp = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
    parts, total = [], 0
    for i, page in enumerate(reader.pages, 1):
        txt = page.extract_text() or ""
        total += len(txt)
        parts.append(f"<!-- page: {i} -->\n{txt}\n")
    pages = len(reader.pages)
    density = round(total / pages) if pages else 0
    body = HEADER.format(src=pdf.name, pages=pages, chars=total,
                         density=density, fp=fp) + "\n".join(parts)
    out.write_text(body, encoding="utf-8")
    # ⚠️ fingerprint 是**來源 PDF** 的雜湊，md_sha256 是**提取物本身**的雜湊。
    #    兩者用途不同：前者證明「這份 md 出自哪一份 PDF」；
    #    後者讓「這份 md 有沒有被事後改過」變成可機械偵測。
    #    後者是 2026-08-08 開放研究 agent 寫入 paper_md/ 的前提——
    #    **錨點查證比對的對象若可被寫入者更動，整條證據鏈就是循環的。**
    md_sha = hashlib.sha256(out.read_bytes()).hexdigest()
    return {"src": pdf.name, "md": out.name, "pages": pages,
            "chars": total, "density": density, "fingerprint": fp,
            "md_sha256": md_sha}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-dir", default="paper")
    ap.add_argument("--out-dir", default="paper_md")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src_dir, out_dir = Path(args.paper_dir), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(src_dir.glob("*.pdf"))

    if not pdfs:
        print(f"[FAIL] SCAN_GLOB_MATCHES_NOTHING: {src_dir}/ 中沒有 PDF"
              "——掃不到的地方等於沒有感測器")
        return 2

    manifest, low = [], []
    for pdf in pdfs:
        out = out_dir / (pdf.stem + ".md")
        if out.exists() and not args.force:
            print(f"  跳過（已存在）：{out.name}")
            continue
        try:
            rec = convert(pdf, out)
        except Exception as e:
            print(f"  [FAIL] EXTRACTION_ERROR: {pdf.name} — {type(e).__name__}: {e}")
            continue
        manifest.append(rec)
        # ⚠️ 判準為「平均字元／頁 < 400」，不是「零字元」。
        #    出版社浮水印可使每頁有數十字元，零字元判準會漏判掃描檔。
        flag = "  🔴 文字層可能不可用" if rec["density"] < 400 else ""
        if rec["density"] < 400:
            low.append(rec)
        print(f"  ✅ {out.name}  {rec['pages']} 頁 / {rec['chars']} 字元 / "
              f"{rec['density']} 每頁{flag}")

    mf = out_dir / "_manifest.json"
    existing = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else []
    by_src = {r["src"]: r for r in existing}
    by_src.update({r["src"]: r for r in manifest})
    mf.write_text(json.dumps(sorted(by_src.values(), key=lambda r: r["src"]),
                             ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  清單：{mf}（{len(by_src)} 筆）")
    if low:
        print(f"  ⚠️ {len(low)} 份平均字元／頁 < 400，文字層可能不可用，"
              f"錨點查證對這些檔案不可靠：")
        for r in low:
            print(f"      - {r['src']}（{r['density']} 字元／頁）")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
