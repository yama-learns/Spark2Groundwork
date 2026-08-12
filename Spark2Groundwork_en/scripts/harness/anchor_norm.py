#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalisation for anchor comparison — **the single home** (registered in `file_index.md` §0).

## Why it is needed

The Claim Ledger requires anchors quoted verbatim, matched by string comparison against
programmatically extracted text. **But PDF extraction inevitably produces the following
distortions, and every one of them breaks a verbatim comparison:**

    line-break hyphenation   individ-\\nual differences
    soft hyphen              individ­ual
    ligatures                fi  fl  ff  ffi  ffl
    full-width forms         （2024） vs (2024)
    curly quotes             “…” vs "…"
    repeated whitespace      N  =  40
    non-breaking space       \\u00a0

The failure direction is "not found" → FAIL, producing **a flood of false positives** —
and false positives teach people to ignore the sensor (R-19, precision over coverage).

## Two hard design rules

1. **Both sides must pass through this same function.** One-sided normalisation manufactures false positives.
2. **Normalisation happens only at comparison time; it is never written back.**
   ⛔ Never write the normalised result back into the corpus — that breaks the hash defence,
   and once an extraction has been rewritten by a model, anchor checking goes from
   verifiable to circular.

## Order

    ① rejoin hyphenation -> ② soft hyphen -> ③ ligatures -> ④ full-width -> ⑤ quotes -> ⑥ whitespace

⚠️ **① must precede ⑥.** Otherwise `individ-\\nual` is first collapsed to `individ- ual`,
then to `individ-ual`, **and can never be rejoined.**
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
    """Return the normalised string used for anchor comparison.
    **Both sides must go through this function.**"""
    # (1) Rejoin line-break hyphenation (must come first)
    #     ⚠️ **The whitespace class must cover both newlines and plain spaces.**
    #     Reason: anchors are transcribed by hand, and **transcription often turns the
    #     newline into a space** — the source reads `con-\nventional` while the ledger
    #     records `con- ventional`.
    #     Handling only `-\n` leaves the two sides asymmetric, and **anchors that
    #     previously passed will fail** (measured: 2 entries).
    #     ⛔ This rule will wrongly join a few legitimate cases (`pre- and` -> `preand`).
    #     **That is acceptable**: normalisation is used only for comparison and both
    #     sides run the same function — **a symmetric wrong join causes no false negative.**
    #     **What kills a comparison is asymmetry, not aggressiveness.**
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)
    # Remaining newlines become spaces (hyphenation already handled)
    s = re.sub(r'\r?\n', ' ', s)
    # (2) Soft hyphen
    s = s.replace('­', '')
    # (3) Ligatures
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    # (4) Full-width -> half-width (NFKC also handles full-width brackets, digits, punctuation)
    s = unicodedata.normalize('NFKC', s)
    # (5) Unify quotes and the various dashes
    for k, v in QUOTES.items():
        s = s.replace(k, v)
    for k, v in DASHES.items():
        s = s.replace(k, v)
    # (6) Collapse whitespace (including non-breaking space)
    s = s.replace(' ', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


# Alias: sensors in this framework always do `from anchor_norm import norm`
norm = norm_for_anchor


if __name__ == '__main__':
    import sys
    print(norm_for_anchor(sys.stdin.read()))
