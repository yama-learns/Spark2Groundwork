#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF -> Markdown extraction tool (the plumbing under link ② of the evidence chain)

**This tool saves no tokens.** Its only value is that it turns "is that passage actually in
the source" into a single string comparison — dropping the cost of verifying a Claim Ledger
anchor to zero.

Design principles
-----------------
* **Programmatic extraction, no model in the loop.** With no model involved, the failure mode
  "a self-written summary passed off as the source" cannot occur. (A predecessor project logged
  exactly that: a claimed 71-page extraction that was 18% complete, padded with summaries and
  placeholders — and because authors and years were correct, no bibliographic check caught it.)
* **A `<!-- page: N -->` marker per page**, so an anchor traces back to a page.
* **No cleaning, no rewriting, no normalisation.** The extract is verbatim the PDF text layer.
  ⛔ **In particular, line-break hyphenation is NOT undone here** — `anchor_norm.py` handles it
  **at comparison time**. Doing it during extraction writes normalisation back into one side (`R-28`).

## Backends: PyMuPDF first, pypdf as fallback

**Triggering case:** two extractions of the same 11 papers were cross-tested; strict anchor hit
rate was only 62.5%, and 95.7% after stripping whitespace and punctuation.
**33.2 points were purely whitespace and hyphen differences — the content was identical.**

**Root cause:** pypdf drops end-of-line spaces on some PDFs, producing glued words like
`leadsto` and `havethe`. `anchor_norm.py` can collapse whitespace **but cannot insert
whitespace that is not there.** → anchor verification produces a flood of false positives,
and `R-19` says: **a sensor that fires on correct text teaches people to ignore it.**
**The fix is the extractor, not the comparator** (constitution §7.3 step 1; `R-20`).

⚠️ **The backend name goes into the header and the manifest.** A comparable tool silently fell
back to a different extraction path leaving no marker — two kinds of extract mixed in one batch
with no way to tell them apart from the file. **Degrading is fine; degrading silently is not.**

## The manifest's extraction-quality self-check

Every extract records `selfcheck_hit`: N sentences are sampled from **the extract itself**,
normalised with `anchor_norm`, and looked up in **the extract itself**.

> **This number should be 100%. Anything less means the act of "copy a sentence out of the
> source and then compare it" fails on this file** — and that is exactly what every row of
> the Claim Ledger does.

⛔ **This file deliberately does not measure a "glued word rate".** Deciding whether `leadsto`
is glued requires a lexicon, and a heuristic guess would fire on correct text (`R-19`).
**Glued words are only detectable by comparing two extractions → use `tool_extract_compare.py`.**

Usage
-----
  python3 tool_pdf_to_md.py [--pdf-dir <src>] [--out-dir <dst>] [--force]

  ⛔ Both defaults come from `framework_config.py` (`pdf_dir` / `corpus_dir`) — the single home
     for paths. Do not hard-code them here; that is the "three directory names" case recorded
     in constitution §3.2.

Requires
--------
  pip install pymupdf      # primary backend
  pip install pypdf        # fallback backend (optional)

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (could not check. **⛔ that is not a pass**)
"""

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()
from framework_config import ROOT, load                      # noqa: E402
from anchor_norm import norm_for_anchor                      # noqa: E402

HEADER = """<!-- Extracted programmatically from the PDF text layer by
     scripts/harness/tool_pdf_to_md.py. No model touched it; nothing was cleaned or rewritten;
     it is verbatim the PDF text layer.
     ⛔ Line-break hyphenation is deliberately NOT undone — that belongs to comparison-time
        normalisation (anchor_norm.py) and is not written back into this side.
     ⚠️ An extract does not replace the source PDF as the citation of record. For any
        load-bearing figure, go back to the PDF.
     Source file: {src}
     Backend: {backend}
     PDF pages: {pages}
     Characters: {chars}
     Mean chars/page: {density}
     Self-check hit rate: {selfcheck}
     Source fingerprint (PDF SHA-256, first 16): {fp}
-->

"""

COMMENT = re.compile(r"<!--.*?-->", re.S)
PAGE = re.compile(r"<!--\s*page:\s*\d+\s*-->")


def extract_pymupdf(pdf):
    """PyMuPDF text-layer extraction. **Per page**; no merging, no reflow, no de-hyphenation."""
    import pymupdf
    doc = pymupdf.open(str(pdf))
    pages = [page.get_text("text") or "" for page in doc]
    doc.close()
    return pages


def extract_pypdf(pdf):
    """Fallback backend. ⚠️ Known to drop end-of-line spaces on some PDFs; see header."""
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
    """Pull out **legitimate** anchor candidates, and report how many were excluded
    for spanning a page break.

    ⚠️ **Why sample per page rather than across the file (measured case):**
    the first version scored 93.3% on the MAGIC paper, and **both misses were sentences that
    crossed a `<!-- page: N -->` marker**. The candidate side replaced the comment with a
    space while the haystack side still contained it — **a guaranteed miss.**

    ⛔ **Per constitution §7.3: assume the tool is what is broken. It was this checker,
    not the extract.**

    ⚠️ But the second layer matters more: **a sentence that spans a page break is not a
    legitimate anchor in the first place** — the Claim Ledger's page field holds one page
    number. **It should not be sampled, and it should not count as a failure.**
    → So sentences are drawn per page; cross-page candidates are **counted and reported,
    but excluded from the hit rate**.
    """
    per_page = []
    for ch in PAGE.split(body):
        per_page.extend(_sent(ch))
    ok = set(per_page)
    spanning = sum(1 for s in _sent(body) if s not in ok)
    return per_page, spanning


def selfcheck(body, n=30, seed=20260819):
    """Round-trip: sample sentences from the extract, normalise, look them up in itself.

    ⚠️ **Should be 100%.** Below 100% means "copy a sentence out and compare it" itself
    fails — and that is what every anchor in the Claim Ledger does.
    ⛔ This is not a measure of extraction quality; it measures **whether the anchor
    workflow holds at all**.
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
            # ⛔ No silent degradation: every fallback leaves a trace
            errors.append(f"{name}: {type(e).__name__}: {e}")
    if pages is None:
        raise RuntimeError("all backends failed -- " + " | ".join(errors))

    total = sum(len(t) for t in pages)
    n = len(pages)
    density = round(total / n) if n else 0
    body = "\n".join(f"<!-- page: {i} -->\n{t}\n" for i, t in enumerate(pages, 1))
    rate, sn, span = selfcheck(body)
    sc = "not enough sentences to test" if rate is None else f"{rate*100:.1f}% ({sn} sentences sampled)"

    head = HEADER.format(src=pdf.name, backend=backend, pages=n, chars=total,
                         density=density, selfcheck=sc, fp=fp)
    if errors:
        head += ("<!-- ⚠️ Backend degradation log (**not a harmless implementation detail**: extracts from\n     different backends are not interchangeable):\n     "
                 + "\n     ".join(errors) + "\n-->\n\n")
    out.write_text(head + body, encoding="utf-8")

    # ⚠️ `fingerprint` hashes the **source PDF**; `md_sha256` hashes the **extract itself**.
    #    The first proves which PDF this .md came from; the second makes "has this .md been
    #    edited since" mechanically detectable.
    #    **If whoever can write can also alter what anchors are compared against, the whole
    #    evidence chain is circular.**
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
        print(f"[FAIL] SCAN_GLOB_MATCHES_NOTHING: no PDFs in {args.pdf_dir}/"
              " — a place that is never scanned has no sensor over it")
        return 2

    # ⚠️ Create the output directory **only after** we know there are PDFs.
    #    Measured: mkdir ran first, so one accidental invocation left an empty corpus_md/
    #    behind, and sensor_claim_ledger.py reports INCOMPLETE for "directory exists but no
    #    manifest" — **the whole harness went from 0 to 2 because of an empty folder.**
    #    ⚠️ And git does not track empty directories, so it appears in no change list.
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest, low, degraded, failed, badself = [], [], [], [], []
    for pdf in pdfs:
        out = out_dir / (pdf.stem + ".md")
        if out.exists() and not args.force:
            print(f"  skipped (exists; use --force to overwrite): {out.name}")
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
        # ⚠️ The threshold is "mean chars/page < 400", not "zero characters".
        #    A publisher watermark puts dozens of characters on every page of a scan,
        #    so a zero-character threshold misses scanned documents entirely.
        if rec["density"] < 400:
            low.append(rec)
        if rec["selfcheck_hit"] is not None and rec["selfcheck_hit"] < 1.0:
            badself.append(rec)
        sflag = "" if rec["selfcheck_hit"] is None else f" / selfcheck {rec['selfcheck_hit']*100:.0f}%"
        flag = "  🔴 text layer may be unusable" if rec["density"] < 400 else ""
        print(f"  ✅ {out.name}  {rec['pages']} 頁 / {rec['chars']} 字元 / "
              f"{rec['density']} 每頁 / {rec['backend']}{sflag}{flag}")

    mf = out_dir / "_manifest.json"
    existing = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else []
    by_src = {r["src"]: r for r in existing}
    by_src.update({r["src"]: r for r in manifest})
    mf.write_text(json.dumps(sorted(by_src.values(), key=lambda r: r["src"]),
                             ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  manifest: {mf.relative_to(ROOT)} ({len(by_src)} entries)")

    # ── 孤兒檢查：manifest 有紀錄但 md 不在，或 md 在而 manifest 沒有 ──
    # ⚠️ The corpus directory was once reorganised by hand, and **the move itself produces
    #    no error message at all**.
    on_disk = {p.name for p in out_dir.glob("*.md")}
    in_mf = {r["md"] for r in by_src.values()}
    rc = 0
    if on_disk - in_mf:
        print(f"  [FAIL] CORPUS_ORPHAN_MD: {len(on_disk - in_mf)} 份 .md 不在清單內"
              " — **they are unprotected against tampering and of unknown origin**:")
        for m in sorted(on_disk - in_mf):
            print(f"      - {m}")
        rc = 1
    if in_mf - on_disk:
        print(f"  [FAIL] CORPUS_ORPHAN_MANIFEST: {len(in_mf - on_disk)} manifest entries have no file:")
        for m in sorted(in_mf - on_disk):
            print(f"      - {m}")
        rc = 1
    if degraded:
        print(f"  ⚠️ {len(degraded)} file(s) used the fallback backend "
              "(**extracts from different backends are not interchangeable**):")
        for r in degraded:
            print(f"      - {r['src']} → {r['backend']}")
    if badself:
        print(f"  🔴 {len(badself)} file(s) scored below 100% on the self-check — "
              "**\"copy a sentence out and compare it\" fails on these files, and every "
              "ledger row does exactly that**:")
        for r in badself:
            print(f"      - {r['src']} ({r['selfcheck_hit']*100:.1f}%, {r['selfcheck_n']} sampled)")
        print("      → ⛔ Do not loosen the comparison (R-20). First cross-check against "
              "another backend with tool_extract_compare.py to establish whether the "
              "extractor or the normalisation is what is broken.")
        rc = max(rc, 1)
    if low:
        print(f"  ⚠️ {len(low)} file(s) below 400 chars/page; the text layer may be unusable "
              f"and anchor verification is unreliable for them:")
        for r in low:
            print(f"      - {r['src']} ({r['density']} chars/page)")
        return 2
    if failed:
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
