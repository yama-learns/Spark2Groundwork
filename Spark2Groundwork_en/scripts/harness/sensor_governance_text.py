#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: governance-text consistency

## Four checks

    DUPLICATE_RULE_TEXT      A long sentence identical across files (one rule, two homes)   WARN
    SECTION_REF_UNRESOLVED   A section citation does not resolve uniquely — long form
                             `<file>.md` §N **and** short form "constitution §N"          WARN
    ALIAS_TARGET_MISSING     A configured short-form target is not in this tree      INCOMPLETE
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
from framework_config import (resolve_globs, excluded,
                              active_launcher_globs)       # noqa: E402

# ⚠️ **Length bounds are language-dependent and must not be copied across languages.**
#    The Chinese edition used 24..80 characters. Ported unchanged to English, a rule sentence
#    of ~100 characters fell outside the window and **the duplicate check silently found nothing**
#    — caught by the paired fixture, not by reading the code.
#    A rule that is "the same rule" in two languages can still need different constants.
# 🔴 **The threshold counts information length, ⛔ not characters.**
#
# ⚠️ **Measured: the two editions had different thresholds** (Chinese 24-80, English 40-220),
#    **and that difference was never registered as a deliberate divergence.**
#    The consequence is measurable: the same rule sentence normalises to
#      Chinese: **21 characters**
#      English: "The order cannot be swapped: de-hyphenation..." -> **68 characters**
#    **Both editions carried that duplicate, and only the English one was caught — the
#    Chinese one missed the threshold by three characters.**
#
# ⛔ **A character-count threshold is systematically weaker for Chinese**, which expresses
#    the same content in roughly a third of the characters.
#    → Counted as information length instead: **one CJK character counts as three Latin ones.**
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
CJK_WEIGHT = 3


def info_len(s):
    """Information length -- ⛔ not len(). See the note above."""
    n = len(CJK.findall(s))
    return (len(s) - n) + n * CJK_WEIGHT


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


# -- A header banner is not a rule ----------------------------------------------
# ⚠️ **Observed case:** `Claim_Ledger.md` and `Conjecture_Ledger.md` both carry the
#    header line "T1 data class. AI must not write to this file directly.", so it was
#    reported as one rule with two homes. **That line is file metadata, not a rule** --
#    every data-class file has to state it, or a reader cannot tell what they are holding.
#    **Demanding that it appear only once is demanding that it not work.**
# ⛔ **This is not "loosening the criterion because it false-alarmed" (R-20); it corrects
#    what the criterion is applied to.**
#    -> Still structural, not keyword-based: **a line that is one whole bold span and
#    sits before the first `## ` heading.** Rule text repeated inside a section is
#    unaffected -- the `gov_dup` must-catch fixture holds that line.
# ⚠️ **The splitter once recognised only `。` and newlines**, so the English edition could
#    only compare whole lines -- the sentence shared by `Audit_Protocol.md` and
#    `HANDOFF.md` was caught in Chinese and missed in English, **though both editions
#    duplicate it identically.** A weaker sensor reads as a cleaner edition.
#    -> A period (optionally followed by a closing `**`, quote or bracket) plus whitespace
#    is now a break; `3.2` and `.md` stay intact (inline code spans are stripped first).
#    ⚠️ The closing-marker part came from a real miss: in `**...unfinished.** "None"...`
#    the period is followed by `*`, not whitespace, **so period-plus-space still missed it.**
SPLIT = re.compile(r"。|(?<=\.)[*_\"'’”)\]]*\s+|\n")


# -- A sentence that names its home is not a second home ------------------------
# ⚠️ **Observed case:** after a duplicated rule was rewritten as "see constitution §3.4,
#    ⛔ not restated here", **that citation was itself word-for-word identical in two
#    files, so it was reported as a duplicate in turn.**
# 🔴 **But it is the opposite: a sentence naming the home ⛔ cannot be a second home —
#    it is the very mechanism that stops one from existing.**
# ⛔ **This is not "loosening the criterion because it false-alarmed" (R-20); it corrects
#    what the criterion is applied to.**
#    -> Still structural: **the sentence contains a `§` section number or an `R-nn` rule id**,
#    and is therefore a pointer.
#    ⚠️ Stated cost: a genuinely duplicated rule that also names a section will be missed.
#    **This sensor chooses to miss that rather than alarm on every citation** (`R-19`).
POINTER = re.compile(r"§\s*\d|R-\d\d")


# -- A `## 3.` inside a fenced block is not a section --------------------------
# 🔴 **Measured, on the first run after the scope was widened:** `HANDOFF.md` was reported as
#    having two `## 3.` headings. **One of them is a line inside the fenced template showing
#    the five required sections** — ⛔ it is sample text, not a heading.
# ⚠️ **The defect was already in the original long-form check**; it never fired only because
#    nothing inside `governance_globs` happened to cite `HANDOFF.md §3`.
#    **Widening the scope did not create it — it made it visible.**
# ⛔ **Not fixed with an exemption list (R-20/R-21): fenced blocks are stripped, which
#    corrects what the criterion is applied to.**
#    ⚠️ Stated cost: a real heading placed inside a fenced block becomes invisible.
#    **That is not a thing anyone writes.**
FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def strip_fences(text):
    return FENCE.sub("", text)


BANNER = re.compile(r"^\*\*[^*]+\*\*$")


def strip_banner(text):
    """Drop header banner lines (metadata); keep everything else."""
    out, in_header = [], True
    for line in text.split("\n"):
        if line.startswith("## "):
            in_header = False
        if in_header and BANNER.match(line.strip()):
            continue
        out.append(line)
    return "\n".join(out)


def sentences(text):
    text = strip_banner(text)
    text = re.sub(r"`[^`]*`", "", text)
    for raw in re.split(SPLIT, text):
        s = re.sub(r"[*⚠️⛔🔴🟢🟡🟤📌>#|\-—\s]", "", raw)
        if POINTER.search(raw):
            continue          # ⛔ 指標，不是規則
        if MIN_DUP <= info_len(s) <= MAX_DUP:
            yield s


def main():
    root, cfg, as_json, name = cli("governance_text")
    files, dead = resolve_globs(cfg["governance_globs"], root, cfg)
    findings = dead_glob_findings(dead, "governance_globs", root)
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
    # 🔴 **Two forms, one defect.** The long form `` `<file>.md` §N `` was the only one checked.
    #    ⚠️ **The angle brackets here are load-bearing** — ⛔ written as a real filename, this very
    #    comment becomes a dangling file reference (`sensor_reference_integrity` caught me doing
    #    exactly that, ⛔ I did not spot it myself).
    #    ⛔ **The short form ("constitution §N") is what the framework actually writes most of
    #    the time — 58 places in this edition — and nothing was checking it.**
    #    ⚠️ **Measured, found by hand at release time, ⛔ not by this sensor:**
    #      `§5.11` in a sensor header (a defect description that instantiated the defect it
    #      described), `§8.1` in `Audit_Protocol.md` (`## 8.` has no `### 8.1`),
    #      `§5.8` pointing at a section a T0 rewrite had removed.
    # ⛔ **The anchor words are configuration** (`section_ref_aliases`), not a hard-coded list:
    #    a downstream project's short name will differ, and `R-21` forbids a whitelist as scope.
    #     ⚠️ **Scope is the code scope, not the governance scope.** `sensor_reference_integrity`
    #     exists because `.py` headers were never scanned — ⛔ but it only fixed *file*
    #     references. **The same hole was still open for *section* references, and the half
    #     that was fixed made it look closed.**
    launchers = active_launcher_globs(cfg.get("launcher_globs", []), root)
    ref_globs = (cfg.get("code_globs", ["scripts/**/*.py", "scripts/**/*.sh"])
                 + launchers
                 + cfg["governance_globs"])
    # ⛔ **The dead-glob report for this exact glob set has one home: `sensor_reference_integrity`.**
    #    Emitting it here too would double the noise for zero information — **and a finding with
    #    two homes is the thing this sensor exists to catch.**
    #    ⚠️ Measured: re-emitting it took the self-test's tolerated-WARN count from 81 to 148.
    ref_files, _ref_dead = resolve_globs(ref_globs, root, cfg)

    all_md = {q.name: q for q in root.rglob("*.md") if not excluded(q, root, cfg)}
    aliases = cfg.get("section_ref_aliases", {})
    alias_res = [(a, re.compile(re.escape(a) + r"\s*§\s*(\d+(?:\.\d+[a-z]?)?)",
                                re.UNICODE | re.IGNORECASE), tgt)
                 for a, tgt in aliases.items()]

    def resolve(body, sec):
        # §9 matches '## 9.' but not '### 9.1'
        return len(re.findall(rf"^#+\s*{re.escape(sec)}(?=[ .、（(])(?!\.\d)", body, re.M))

    seen, checked = set(), 0
    for p in ref_files:
        try:
            t = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        pairs = [(pathlib.Path(m.group(1)).name, m.group(2), None) for m in REF.finditer(t)]
        for anchor, rx, tgt_rel in alias_res:
            pairs += [(pathlib.Path(tgt_rel).name, m.group(1), anchor) for m in rx.finditer(t)]
        for fn, sec, anchor in pairs:
            checked += 1
            tgt = all_md.get(fn)
            if tgt is None:
                if anchor is not None and (p.name, fn, "TARGET") not in seen:
                    # ⛔ An alias nobody can resolve is not "nothing to do" (R-33).
                    seen.add((p.name, fn, "TARGET"))
                    findings.append(("INCOMPLETE", "ALIAS_TARGET_MISSING",
                                     f"{p.name} cites “{anchor} §{sec}”, but the configured target "
                                     f"{fn} is not in this tree — **not checked is not a pass**"))
                continue
            if (p.name, fn, sec) in seen:
                continue
            hits = resolve(strip_fences(tgt.read_text(encoding="utf-8", errors="replace")), sec)
            if hits != 1:
                seen.add((p.name, fn, sec))
                cite = f"“{anchor} §{sec}”" if anchor else f"{fn} §{sec}"
                findings.append(("WARN", "SECTION_REF_UNRESOLVED",
                                 f"{p.name} cites {cite}，matched {hits}  time(s) — "
                                 f"{'does not exist' if hits == 0 else 'not unique'}"))

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

    code = emit("Governance-text sensor", findings, {"governance documents scanned": len(texts), "section citations checked": checked}, as_json, name)
    if not as_json:
        print("      ⚠️ Literal comparison only; semantically identical but differently worded text is not caught")
    return code


if __name__ == "__main__":
    sys.exit(main())
