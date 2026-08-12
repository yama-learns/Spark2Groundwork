#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: prompt self-containment (on demand, takes one file)

External tools run in independent conversations that share no context, so
"as above", "see previous", and "same as R1" are **blank at the execution end** —
the referenced clause effectively does not exist.

⚠️ **This sensor exists because the rule alone could not stop the error:**
one prompt quoted the rule ("do not write 'as above'") in its §1,
**and wrote "Same as R3-1" in its lower half. Quoting the rule and breaking it in one file.**
Measured: the referenced marker was used **0 times** in that run, while the version
with the clause spelled out used it **12 times**.

⚠️ **A template with `<<<PASTE BLOCK X>>>` placeholders will FAIL. That is correct** —
at the execution end a placeholder is equivalent to "as above".
**Assemble the finished prompt first, then run this.**

Usage:  python3 sensor_prompt_self_contained.py <prompt.md> [--json]
Exit codes: 0 PASS | 1 FAIL | 2 execution error
"""
import argparse
import json
import pathlib
import re
import sys

CROSSREF = [
    (r"(?i)\bsame as\s+R?\d", "same as R#"),
    (r"(?i)\bas (?:in|above|described above)\b", "as in/above"),
    (r"(?i)\bsee (?:above|below|R\d|section)\b", "see above/section"),
    (r"(?i)\b(?:ditto|idem)\b", "ditto"),
    (r"<<<[^>]*(?:PASTE|BLOCK|\u8cbc\u4e0a)[^>]*>>>", "unfilled placeholder"),
]

REQUIRED_HINTS = [
    ("hallucination guard", r"(?i)uncertain|do not invent|fabricat"),
    ("enumeration requirement", r"(?i)enumerate|one per line|NONE RETRIEVED"),
    ("output contract", r"(?i)output contract|deliverable|report the following"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    p = pathlib.Path(a.prompt)
    if not p.exists():
        print(f"[INCOMPLETE] PROMPT_NOT_FOUND: {p}  -- not checked, and that is not a pass")
        return 2
    text = p.read_text(encoding="utf-8", errors="replace")

    findings = []
    for pat, label in CROSSREF:
        for m in re.finditer(pat, text):
            line = text[:m.start()].count("\n") + 1
            findings.append(("FAIL", "CROSS_PROMPT_REFERENCE",
                             f"line {line}: '{label}' -- blank at the execution end"))
    for label, pat in REQUIRED_HINTS:
        if not re.search(pat, text):
            findings.append(("WARN", "REQUIRED_CLAUSE_MISSING",
                             f"no {label} found -- is this prompt really self-contained?"))

    fails = [f for f in findings if f[0] == "FAIL"]
    if a.json:
        print(json.dumps({"sensor": "prompt_self_contained",
                          "status": "FAIL" if fails else "PASS",
                          "findings": [{"level": l, "code": c, "message": m}
                                       for l, c, m in findings]}, indent=2))
    else:
        print(f"-- Prompt self-containment: {p.name} " + "-" * 20)
        for l, c, m in findings:
            print(f"  [{l}] {c}: {m}")
        print(f"  Result: {'FAIL' if fails else 'PASS'} ({len(findings) - len(fails)} warnings)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
