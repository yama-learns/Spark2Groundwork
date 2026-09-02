#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract interchangeability test — **can these two extracts serve as the same anchor haystack?**

## What this answers

Anchor verification in the Claim Ledger (evidence-chain link ②) is one string comparison:
**"is this sentence in the extract".** So when the same batch of PDFs has two extracts — from
different tools, different backends, or different dates — one question comes first:
**are they interchangeable?**

⚠️ **"Both are readable" is not "interchangeable".** Anchor comparison does not look at
readability. It looks at verbatim hits.

## How it tests

It samples complete 60-200 character sentences from side A and checks whether each one hits
in side B. **Both sides go through the same normalisation function** (`anchor_norm.py`, the
single home, `R-27`).

It then runs a second comparison with **all whitespace and punctuation stripped**.
The gap between the two is the share that is "purely whitespace / hyphen difference, same content".

⚠️ **That gap column is the reason this tool exists.** It separates two entirely different problems:

    large gap  -> same content, differs in hyphenation and spacing -> a **normalisation coverage** problem
    small gap  -> the text content itself differs                  -> an **extraction quality** problem

**Treating the first as the second means fixing an extractor that was not broken.**
(constitution §7.3, step 1)

⚠️ **Triggering case:** someone ran a one-way test, got 62.5%, and was about to report "this
extract is unusable". With whitespace and punctuation stripped the hit rate was 95.7% —
**33.2 points were purely whitespace, the content was identical.**
**What was broken was the extractor's whitespace handling, not the artefact under test.**

## Usage

    python3 tool_extract_compare.py --a corpus_md --b corpus_md_old
    python3 tool_extract_compare.py --a corpus_md --b corpus_md_old --n 40 --seed 20260819

⚠️ **Paths are relative to the project root.** Only files present on both sides are compared.

Exit codes: 0 = comparison completed (⚠️ **this does not mean they are interchangeable;
that judgement is still the human's**) | 2 = could not compare
"""

import argparse
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()
from anchor_norm import norm_for_anchor                      # noqa: E402
from framework_config import ROOT                            # noqa: E402

HARD = re.compile(r"[^0-9a-z一-鿿]")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def hard(s):
    """Loose side: strip all whitespace and punctuation; keep alphanumerics and CJK."""
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
    ap.add_argument("--a", required=True, help="anchor source side (sentences are sampled from here)")
    ap.add_argument("--b", required=True, help="haystack side (tested for whether the anchors hit)")
    ap.add_argument("--n", type=int, default=40, help="sentences sampled per file")
    ap.add_argument("--seed", type=int, default=20260819)
    args = ap.parse_args()

    A, B = ROOT / args.a, ROOT / args.b
    files = sorted(A.glob("*.md"), key=lambda p: p.as_posix())
    if not files:
        print(f"[FAIL] SCAN_GLOB_MATCHES_NOTHING: no .md files in {args.a}/"
              " — a place that is never scanned has no sensor over it")
        return 2

    random.seed(args.seed)
    print(f"anchors from: {args.a}    haystack: {args.b}    seed={args.seed}")
    print(f"{'file':46} {'n':>4} {'strict':>7} {'loose':>7} {'gap':>7}")
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
        print("[FAIL] no file present on both sides")
        return 2
    print(f"{'total':46} {tn:>4} {ts/tn*100:>6.1f}% {th/tn*100:>6.1f}% {(th-ts)/tn*100:>6.1f}%")
    print()
    print("  strict = anchor_norm applied (whitespace kept) -- **this is what the sensor uses**")
    print("  loose  = plus all whitespace and punctuation stripped")
    print(f"  gap    = {(th-ts)/tn*100:.1f}%  purely whitespace/hyphen difference, **same content**")
    print(f"  real content difference = {100-th/tn*100:.1f}%")
    print()
    print("  -> large gap, small real difference: a **normalisation coverage** problem. ⛔ Do not fix the extractor.")
    print("  -> small gap, large real difference: an **extraction quality** problem. ⛔ Do not loosen the comparison (R-20).")
    if missing:
        print(f"\n  ⚠️ {len(missing)} file(s) had no counterpart on the haystack side (excluded):")
        for m in missing[:5]:
            print(f"      - {m}")
        if len(missing) > 5:
            print(f"      ... and {len(missing)-5} more")
    print("\n  ⛔ This tool does not decide which extract is better. It answers only whether they are interchangeable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
