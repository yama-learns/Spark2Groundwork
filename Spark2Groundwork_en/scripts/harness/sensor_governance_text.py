#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: governance-text consistency

## Four checks

    DUPLICATE_RULE_TEXT      A long sentence identical across files (one rule, two homes)   WARN
    SECTION_REF_UNRESOLVED   A `file.md` §N citation does not resolve uniquely              WARN
    STATE_IN_SPEC_DOC        A spec-class document contains state (to-dos / progress)       WARN
    SCAN_GLOB_MATCHES_NOTHING  A scan glob matched zero files                                 WARN

## Why this exists

**A one-off scan is not a guarantee.** One project cleared 17 cross-file duplicates and then
never ran that scan again — **a one-time result, not an ongoing assurance.**

Likewise, a "rule -> single home" table **is a hand-maintained whitelist**:
forget to register a new rule and **there is no longer any mechanical way to know
whether it has a second home** — **which is precisely what that table exists to prevent.**

⛔ **This sensor does not replace that table.** The table answers "where does this rule live";
this sensor answers "has any rule grown a second home".
**They fail in opposite directions, so both are needed.**

## Known blind spots (⛔ deliberately kept; do not "fix" by loosening)

1. Compares **literal** text only. **It cannot catch semantically identical wording that differs
   on the surface** — which is the more common form of drift.
2. All findings are WARN, not FAIL: **precision over coverage** (R-19).

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import re
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings          # noqa: E402
from framework_config import resolve_globs, excluded       # noqa: E402

# ⚠️ **Length bounds are language-dependent and must not be copied across languages.**
#    The Chinese edition used 24..80 characters. Ported unchanged to English, a rule sentence
#    of ~100 characters fell outside the window and **the duplicate check silently found nothing**
#    — caught by the paired fixture, not by reading the code.
#    A rule that is "the same rule" in two languages can still need different constants.
MIN_DUP, MAX_DUP = 40, 220
# ⚠️ **The criterion is structure, not keywords.**
#    The first version keyed on the word "to-do", so **the rule text discussing
#    "must not contain to-dos" was itself flagged.**
#    Keyword hunting costs you false alarms on correct text, which teaches people
#    to switch the sensor off (R-19).
#    -> Now it matches only the **structure** of a to-do list: checkboxes, "done" markers,
#    or a progress column in a table.
STATE_WORDS = re.compile(r"^\s*[-*]\s*\[[ xX]\]"
                         r"|\u2705\s*\*\*(?:done|\u5df2\u5b8c\u6210)"
                         r"|\|\s*\u2705\s*(?:done|\u5df2\u5b8c\u6210)\s*\|", re.M)
# Filenames may be non-Latin; \w with re.UNICODE covers CJK without hard-coding a range.
REF = re.compile(r"`([\w_/.-]+\.md)`\s*§(\d+(?:\.\d+[a-z]?)?)", re.UNICODE)


def sentences(text):
    text = re.sub(r"`[^`]*`", "", text)
    for raw in re.split(r"[。\n]", text):
        s = re.sub(r"[*⚠️⛔🔴🟢🟡🟤📌>#|\-—\s]", "", raw)
        if MIN_DUP <= len(s) <= MAX_DUP:
            yield s


def main():
    root, cfg, as_json, name = cli("governance_text")
    files, dead = resolve_globs(cfg["governance_globs"], root, cfg)
    findings = dead_glob_findings(dead, "governance_globs")
    if not files:
        findings.append(("INCOMPLETE", "GOV_DOCS_ABSENT",
                         "no governance documents found — **not checked, and that is not a pass**"))
        return emit("Governance-text sensor", findings, {}, as_json, name)

    texts = {}
    for p in files:
        try:
            texts[p] = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} is not UTF-8 — **not checked is not a pass**"))

    # (1) Cross-file duplicates
    idx = defaultdict(set)
    for p, t in texts.items():
        for s in sentences(t):
            idx[s].add(p.name)
    for s, where in sorted(idx.items()):
        if len(where) > 1:
            findings.append(("WARN", "DUPLICATE_RULE_TEXT",
                             f"identical long sentence in {'／'.join(sorted(where))}：「{s[:40]}…」"
                             " — every rule has exactly one home"))

    # (2) Section citations resolve
    #     ⚠️ Indexed by **filename**; scans the whole tree but excludes on relative paths (R-18)
    all_md = {q.name: q for q in root.rglob("*.md") if not excluded(q, root, cfg)}
    seen = set()
    for p, t in texts.items():
        for m in REF.finditer(t):
            fn, sec = pathlib.Path(m.group(1)).name, m.group(2)
            tgt = all_md.get(fn)
            if tgt is None or (p.name, fn, sec) in seen:
                continue
            body = tgt.read_text(encoding="utf-8", errors="replace")
            # §9 matches '## 9.' but not '### 9.1'
            hits = len(re.findall(rf"^#+\s*{re.escape(sec)}(?=[ .、（(])(?!\.\d)", body, re.M))
            if hits != 1:
                seen.add((p.name, fn, sec))
                findings.append(("WARN", "SECTION_REF_UNRESOLVED",
                                 f"{p.name} cites {fn} §{sec}，matched {hits}  time(s) — {'does not exist' if hits == 0 else 'not unique'}"))

    # (3) Spec-class documents must not contain state
    #    ⚠️ **Exempt the rule text itself.** The paragraph defining "must not contain to-dos"
    #    inevitably contains that phrase. The first version did not exempt it and fired on
    #    correct text — **the exemption granularity was wrong, not the criterion.**
    #    Same principle as exempting gate-style requirements in the self-certification sensor.
    for p, t in texts.items():
        hits = [para for para in t.split("\n\n")
                if STATE_WORDS.search(para) and not re.search(r"⛔|\bmust not\b|\bmust\b|\bshall not\b|\bforbidden\b", para)]
        if hits:
            findings.append(("WARN", "STATE_IN_SPEC_DOC",
                             f"{p.name} contains to-do or progress markers（{len(hits)}  paragraph(s)) — "
                             "**a document with state inherits the update frequency of its fastest-changing part**"))

    code = emit("Governance-text sensor", findings, {"governance documents scanned": len(texts)}, as_json, name)
    if not as_json:
        print("      ⚠️ Literal comparison only; semantically identical but differently worded text is not caught")
    return code


if __name__ == "__main__":
    sys.exit(main())
