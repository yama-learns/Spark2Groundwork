#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: is `my/MY_INDEX.md` stale?

## Why a generated index still needs a watcher

⚠️ **A generator only generates when somebody runs it.**
🔴 **An index nobody has regenerated for three months is ⛔ indistinguishable from a
hand-written one nobody updated** — **both look complete while missing half the files.**

⛔ **So this sensor does ⛔ not reimplement the generation: it calls
`tool_my_index.render()` and compares the result to the file, verbatim.**
⚠️ **If two generators differed anywhere, this criterion would say "stale" forever,
⛔ while the real cause is that the two programs are not the same (constitution §3.2).**

## Three checks

    MY_INDEX_MISSING        the index has never been generated       INCOMPLETE
    MY_INDEX_STALE          regenerating gives a different result    FAIL
    INDEX_NOTE_DANGLING     a description points at a missing file   FAIL
    INDEX_NOTE_EXCLUDED     the file is there, ⛔ just excluded        WARN

⚠️ **`INDEX_NOTE_DANGLING` is a dangling reference** — **the file was moved or renamed
⛔ and the description stayed behind.**
**It is the same thing `sensor_reference_integrity.py` blocks, ⛔ only about a different object.**

## ⛔ What this sensor does not claim

⛔ **It does ⛔ not judge whether a description is correct.** ⚠️ A description unrelated to the
file's contents looks fine to it.
⛔ **It does ⛔ not check that files that ought to exist do exist** — **the index is scanned
from disk, ⚠️ so a file that was never created ⛔ will not be found missing by it.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from tool_my_index import render                           # noqa: E402


def main():
    root, cfg, as_json, name = cli("my_index")
    findings, stats = [], {}
    idx = root / cfg.get("my_index", "my/MY_INDEX.md")

    text, st, err = render(root, cfg)
    if err:
        findings.append(("INCOMPLETE", "INDEX_NOTES_UNREADABLE",
                         f"{err} — **⛔ not checked, and that is not a pass**"))
        return emit("My-index sensor", findings, stats, as_json, name)

    stats["your files"] = st["files"]
    stats["described"] = st["described"]
    stats["not yet described"] = st["not yet described"]

    if not idx.is_file():
        findings.append(("INCOMPLETE", "MY_INDEX_MISSING",
                         f"{cfg.get('my_index', 'my/MY_INDEX.md')} has never been generated"
                         " — **run `python scripts/harness/tool_my_index.py`. "
                         "⛔ Not generated ≠ nothing to index**"))
        return emit("My-index sensor", findings, stats, as_json, name)

    if idx.read_text(encoding="utf-8") != text:
        findings.append(("FAIL", "MY_INDEX_STALE",
                         "the index does not match the files as they are now — **rerun "
                         "`python scripts/harness/tool_my_index.py`. ⚠️ A stale generated "
                         "index and a hand-written one nobody updated ⛔ are the same thing**"))

    dangling = st["notes pointing at missing files"]
    for d in dangling:
        findings.append(("FAIL", "INDEX_NOTE_DANGLING",
                         f"`{d}` has a description ⛔ and the file does not exist"
                         " — **it was moved or renamed and the description stayed behind**"))
    if dangling:
        stats["🔴 notes pointing at missing files"] = len(dangling)

    # ⚠️ **The file is there, just outside the scan** — ⛔ that is ⛔ not a dangling
    #    reference and ⛔ must not FAIL. 🔴 **⛔ Nor may it be silent:** a note that will
    #    never appear in the index is something the user has a right to know about.
    excluded = st.get("described but excluded", [])
    for e in excluded:
        findings.append(("WARN", "INDEX_NOTE_EXCLUDED",
                         f"`{e}` has a description and the file does exist, "
                         "⛔ but `my_index_exclude` keeps it out of the index"
                         " — **⇒ keeping the description is fine, ⛔ but the index "
                         "will never list it**"))
    if excluded:
        stats["described but excluded from the index"] = len(excluded)

    if st["files"] == 0:
        findings.append(("WARN", "MY_INDEX_EMPTY",
                         "there are currently ⛔ no files of your own in this project"
                         " — **⚠️ the result of taking stock, ⛔ not the absence of it**"))
    return emit("My-index sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
