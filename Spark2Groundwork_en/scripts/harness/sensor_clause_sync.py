#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: clause-list synchronisation -- **is the copied list still what its home says**

## Checks

    SYNC_LIST_DRIFT     a copy differs from its home (items added / missing)     FAIL
    SYNC_HOME_MISSING   the home is absent, or the home has no such list         INCOMPLETE
    SYNC_NO_COPY        the home holds a list but no copy exists anywhere        WARN
    SCAN_GLOB_MATCHES_NOTHING / COVERAGE_COLLAPSE                                WARN / INCOMPLETE

## Why this exists (**one observed case, produced by two rules excluding each other**)

`R-24` requires every prompt to be **fully self-contained** -- ⛔ no "as above", no "see earlier".
So an audit prompt **must** carry its own copy of the banned-word list from
`governance/Audit_Protocol.md` §3.

And constitution §3.2 requires **every rule to have exactly one home**.

> 🔴 **The two exclude each other here, and the product of that exclusion is drift.**

**Observed case:** `prompts/TEMPLATE_adversarial.txt` said "very 穩健" while
`governance/Audit_Protocol.md` §3 says "very 強健".
**One character, so that prompt's banned list guarded one word fewer, and both documents read
perfectly normally.**
⚠️ **It was found by a human comparing character by character -- while doing something else.**

## ⛔ This sensor does not resolve that exclusion; it only stops the drift being silent

⚠️ **Do not expect it to replace a decision:** which file is the home, and whether to copy at
all, remain human calls. It answers one mechanical question:
**"is the copy still identical to the home today?"**

## ⚠️ The criterion is set equality, ⛔ not identical order

Decision 18 said "verbatim identical". **It is implemented as set equality; the difference is
recorded here:** in both editions the banned list has **the same contents in a different order**
(the English home puts `airtight` fourth, the template puts it last).

> **Order carries no meaning in this list, and FAILing on a meaningless difference is exactly
> the kind of false alarm `R-19` says will teach people to switch the sensor off.**

⛔ **Every item must still match character for character** -- "very 穩健" and "very 強健" are two
different items and set equality fails on the spot. **What was relaxed is the order, not the
characters.**

## The criterion is structural, not a filename

⛔ **This sensor contains no hard-coded list of copy filenames.**
It scans `sync_scan_globs` and treats **every marked line** as a copy; the home is named by
`synced_lists[].home` (⚠️ that is a **pointer**, not a scan scope, so `R-21` is not violated).
**Adding a new template needs no change here; the one you forget to update reports itself.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (**⛔ incomplete is not a pass**)
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import resolve_globs                   # noqa: E402

# Quoted items: CJK 「」, curly quotes, or straight double quotes
TERM = re.compile(r"「([^」]+)」|“([^”]+)”|\"([^\"]+)\"")


def terms_on(line):
    """Every quoted item on the line (⛔ verbatim; no normalisation whatsoever)."""
    out = []
    for m in TERM.finditer(line):
        out.append(next(g for g in m.groups() if g is not None))
    return out


def find_list(text, marker):
    """Return (line number, set of items); (None, None) if the marker is absent."""
    for i, line in enumerate(text.splitlines(), 1):
        if marker.search(line):
            t = terms_on(line)
            if t:
                return i, frozenset(t)
    return None, None


def main():
    root, cfg, as_json, name = cli("clause_sync")
    specs = cfg.get("synced_lists", [])
    globs = cfg.get("sync_scan_globs", [])
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "sync_scan_globs", root)

    if not specs:
        findings.append(("WARN", "SYNC_NO_SPEC",
                         "`synced_lists` is empty -- **this sensor protects nothing right now**"
                         " (⚠️ not applicable is not a pass)"))
        return emit("Clause-sync sensor", findings, {}, as_json, name)

    checked = copies = 0
    for spec in specs:
        marker = re.compile(spec["marker"])
        home = root / spec["home"]
        if not home.is_file():
            findings.append(("INCOMPLETE", "SYNC_HOME_MISSING",
                             f"the home of list '{spec['id']}', {spec['home']}, does not exist"
                             " -- **not checked this round, which is not a pass**"))
            continue
        _, want = find_list(home.read_text(encoding="utf-8", errors="replace"), marker)
        if want is None:
            findings.append(("INCOMPLETE", "SYNC_HOME_MISSING",
                             f"the home of list '{spec['id']}', {spec['home']}, does not "
                             "contain that list -- ⚠️ **either the marker or the home is stale, "
                             "and a stale watch looks exactly like no watch**"))
            continue

        found_copy = False
        for p in files:
            if p.resolve() == home.resolve():
                continue                       # ⛔ the home is not compared with itself
            lineno, got = find_list(p.read_text(encoding="utf-8", errors="replace"), marker)
            if got is None:
                continue
            found_copy = True
            copies += 1
            if got != want:
                extra = sorted(got - want)
                miss = sorted(want - got)
                findings.append(("FAIL", "SYNC_LIST_DRIFT",
                                 f"{p.relative_to(root)}:{lineno} '{spec['id']}' differs from "
                                 f"its home {spec['home']}: "
                                 + (f"**missing** {miss}; " if miss else "")
                                 + (f"**extra** {extra}" if extra else "")
                                 + " -- ⛔ character for character; order does not matter"))
        checked += 1
        if not found_copy:
            findings.append(("WARN", "SYNC_NO_COPY",
                             f"the home of list '{spec['id']}' has content, **but no copy was "
                             "found in the scan scope** -- ⚠️ this entry currently watches nothing"))

    return emit("Clause-sync sensor", findings,
                {"lists": checked, "copies found": copies, "files scanned": len(files)},
                as_json, name)


if __name__ == "__main__":
    raise SystemExit(main())
