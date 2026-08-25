#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: prompt self-containment (on demand, one file at a time)

External tools run each execution in an independent conversation with no shared context, so
"as above", "see previous" and "same as R1" are **blank at the execution end** — the clause
they point at effectively does not exist.

⚠️ **This sensor exists because the rule alone could not stop the error:**
one prompt quoted the rule ("do not write 'as above'") in its §1
**and wrote "Same as R3-1" in its lower half. Quoting the rule and breaking it in one file.**
Measured: the referenced marker was used **0 times** in that run, while the version with the
clause spelled out used it **12 times**.

## 🔴 Two layers, ⛔ never conflated

**This section is the most important part of this file.**

| Layer | Checks | Applies to |
|---|---|---|
| **① Self-containment** | cross-prompt references, unassembled block slots, prompt pollution | **every prompt** |
| **② Deep Research clause list** | LANG / VENUE-TYPE / NO-DOI / PASS A / PASS B / title accuracy / NONE RETRIEVED / OUTPUT CONTRACT | ⚠️ **only under `--profile deep-research`** |

⚠️ **The old version ran ② against every prompt. Measured consequence:**
`prompts/TEMPLATE_decompose.txt` is a **fully self-contained** decomposition prompt whose
opening line says verbatim "⛔ do not search the literature this round" —
**a prompt that forbids literature search cannot and should not carry bilingual search
clauses. It FAILed, and it would keep FAILing after assembly, forever.**

⛔ **That is `R-19` in full, in two layers:** a sensor that fires on correct text, **plus an
official note telling the reader the FAIL is correct and can be ignored.**
**The second layer is the more dangerous one — it turns "ignore this sensor" into policy.**

## 🔴 Three kinds of `<<<...>>>` slot; **only one is a defect**

| Kind | Example | Verdict |
|---|---|---|
| **Block slot** | `<<<PASTE BLOCK B (enumerate, do not summarise)>>>` | ❌ **FAIL** — a real cross-prompt reference, not yet assembled |
| **Content slot** | `<<<PASTE YOUR IDEA IN FULL>>>` | ✅ **Not a defect** — the user fills it at use time |
| **Fill-in slot** | `<<<FILL IN: one sentence>>>` | ⚠️ **WARN** — a reminder, not a blocker |

⚠️ **The old version treated all three as defects**, so `TEMPLATE_decompose.txt` FAILed on
`<<<PASTE YOUR IDEA IN FULL>>>` — **a placeholder that is supposed to stay there.**

## 🔴 Quoting a prohibition is not breaking it

**Measured case:** `TEMPLATE_decompose.txt` contains the line
"⛔ Do not write 'pending', 'see below', or similar in the falsification field",
**and the sensor flagged the 'see below' inside it as a cross-prompt reference.**

> **String matching can tell whether a phrase is present. It cannot tell whose statement it is.**
> That is the limit of a regex; predecessor projects hit it once each on three different sensors.

→ **Handling: if a prohibition marker (⛔ / "do not" / "never write" / "must not") appears
*before* the phrase on the same line, treat it as a quotation, not a defect.
⛔ And the exempted lines are always printed** — **a silent exemption and no exemption look
the same on screen.**

Usage
-----
    python3 sensor_prompt_self_contained.py <prompt.md|txt> [--profile deep-research] [--json]

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (could not check. **⛔ that is not a pass**)
"""
import argparse
import json
import pathlib
import re
import sys

# ⛔ This file's interface is a single file, ⛔ not `_common.cli` — but the output
#    encoding still has to be pinned first.
#    ⚠️ Measured: without this the sensor died under cp950, **and four self-tests went
#    red — not because a judgement was wrong, but because it never finished printing.**
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import _force_utf8                            # noqa: E402
_force_utf8()

# -- (1) Self-containment: applies to every prompt ------------------------------
CROSSREF = [
    (r"(?i)\bsame as\s+R?\d", "same as R#"),
    (r"(?i)\bas (?:in|above|described above)\b[^\n]{0,20}R?\d", "as in R#"),
    (r"(?i)\bsee (?:above|below|R\d|section)\b", "see above/below/section"),
    (r"(?i)\b(?:ditto|idem)\b", "ditto"),
    (r"同\s*上", "tong-shang (as above)"),
    (r"參\s*見\s*前\s*述", "see previous"),
]
BLOCK_SLOT = re.compile(r"<<<[^>]*(?:PASTE BLOCK|貼上區塊)[^>]*>>>", re.I)
CONTENT_SLOT = re.compile(r"<<<[^>]*(?:PASTE YOUR|PASTE THE|貼上你的"
                          r"|貼上待審)[^>]*>>>", re.I)
FILL_SLOT = re.compile(r"<<<\s*(?:FILL IN|填空)", re.I)
PROHIBITION = re.compile(r"⛔|(?i:do not|never write|must not|avoid writing)"
                         r"|不得|不要|禁止")

POLLUTION = [
    (r"R3-\d\s*v\d", "version code"),
    (r"(?i)previous version|deprecated|superseded by", "changelog prose"),
    (r"(?i)internal (?:test|incident)|triggering case", "internal incident notes"),
]

# ⚠️ **These three patterns are calibrated against the framework's own shipped templates.**
#    ⛔ If one of them fires on a well-formed prompt, the pattern is wrong, not the prompt
#    (`R-19`). **Calibration reference: `prompts/TEMPLATE_decompose.txt`,
#    `TEMPLATE_adversarial.txt` (and `TEMPLATE_prior_art.txt` once assembled).**
GENERIC_HINTS = [
    ("hallucination guard", r"(?i)uncertain|do not invent|do not make (?:it |them )?up"
                              r"|fabricat|if you cannot say|say so rather than"),
    # ⚠️ `(?:answer|address) each` is here because the adversarial template phrases its
    #    enumeration requirement as "answer each separately, do not merge" — the Chinese
    #    edition matched it and this one did not. **A hint that fires on one edition and
    #    not the other is a drift, not a difference of language.**
    ("enumeration requirement", r"(?i)enumerate|one per line|list each|NONE RETRIEVED"
                                r"|list them|list the|itemis|itemiz|numbered from"
                                r"|(?:answer|address) each"),
    ("output contract", r"(?i)output contract|output format|report the following"
                           r"|reporting format|coverage"),
]

# -- (2) Deep Research clause list ---------------------------------------------
# ⚠️ **Only runs under --profile deep-research.** See "Two layers" in the module docstring.
DR_REQUIRED = [
    (r"\[LANG:", "LANG tag definition"),
    (r"\[VENUE-TYPE:", "VENUE-TYPE tag definition"),
    (r"\[NO-DOI", "NO-DOI mechanism"),
    (r"(?i)PASS A", "PASS A (English search)"),
    (r"(?i)PASS B", "PASS B (second-language search)"),
    (r"(?i)TITLE ACCURACY|paraphrase, shorten, or improve", "title accuracy clause"),
    (r"(?i)NONE RETRIEVED", "enumerated NONE RETRIEVED"),
    (r"(?i)OUTPUT CONTRACT", "OUTPUT CONTRACT"),
]


def quoted(line, start):
    """Is the phrase preceded on the same line by a prohibition marker (i.e. quoted)?"""
    m = PROHIBITION.search(line)
    return bool(m and m.start() < start)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--profile", default="generic", choices=["generic", "deep-research"],
                    help="deep-research also runs the DR clause list")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    p = pathlib.Path(a.prompt)
    if not p.exists():
        print(f"[INCOMPLETE] PROMPT_NOT_FOUND: {p} — **not checked, and that is not a pass**")
        return 2
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"[INCOMPLETE] PROMPT_NOT_DECODABLE: {p} ({type(e).__name__}) "
              "— **not checked is not a pass**")
        return 2

    findings, exempt = [], []
    for i, line in enumerate(text.splitlines(), 1):
        scrub = CONTENT_SLOT.sub(" ", line)     # a content slot is an input, not a reference
        for pat, label in CROSSREF:
            for m in re.finditer(pat, scrub):
                if quoted(scrub, m.start()):
                    exempt.append(f"L{i} '{label}'")
                    continue
                findings.append(("FAIL", "CROSS_PROMPT_REFERENCE",
                                 f"L{i}: '{label}' — **blank at the execution end**"))
        for m in BLOCK_SLOT.finditer(line):
            findings.append(("FAIL", "PROMPT_NOT_ASSEMBLED",
                             f"L{i}: {m.group(0)[:40]} — **the part was never pasted in**"))
        if FILL_SLOT.search(line):
            findings.append(("WARN", "TEMPLATE_NOT_FILLED", f"L{i}: a fill-in slot is still open"))

    for pat, label in POLLUTION:
        if re.search(pat, text):
            findings.append(("FAIL", "PROMPT_POLLUTION",
                             f"{label} — **the execution end resets each run and has no memory**"))

    for label, pat in GENERIC_HINTS:
        if not re.search(pat, text):
            findings.append(("WARN", "GENERIC_CLAUSE_MISSING",
                             f"no {label} found — is this prompt really self-contained?"))

    if a.profile == "deep-research":
        miss = [lab for pat, lab in DR_REQUIRED if not re.search(pat, text)]
        if miss:
            findings.append(("FAIL", "DR_CLAUSE_MISSING",
                             f"missing {', '.join(miss)} — a missing clause means that "
                             f"mechanism does not operate in this prompt"))

    fails = [f for f in findings if f[0] == "FAIL"]
    code = 1 if fails else 0

    if a.json:
        print(json.dumps({"sensor": "prompt_self_contained", "profile": a.profile,
                          "status": "FAIL" if fails else "PASS",
                          "findings": [{"level": l, "code": c, "message": m}
                                       for l, c, m in findings],
                          "quoted_exemptions": exempt}, indent=2))
        return code

    print(f"-- Prompt self-containment | {p.name} | profile={a.profile} " + "-" * 8)
    for l, c, m in findings:
        print(f"  [{l}] {c}: {m}")
    if exempt:
        # ⛔ An exemption must be visible (the "silent filtering" family)
        print(f"  ⚠️ {len(exempt)} match(es) exempted as **quoted prohibitions**: "
              + ", ".join(exempt[:6]) + ("..." if len(exempt) > 6 else ""))
        print("      Reason: a prohibition marker precedes the phrase on the same line. "
              "**An exemption is not an absence.**")
    if a.profile != "deep-research":
        print("  ℹ️ The DR clause list (8 items) was **not run** — not applicable to this "
              "profile (⚠️ **not applicable is not a pass**).")
        print("      To check a DR prompt, add `--profile deep-research`.")
    print(f"  Result: {'FAIL' if fails else 'PASS'} ({len(findings) - len(fails)} warnings)")
    return code


if __name__ == "__main__":
    sys.exit(main())
