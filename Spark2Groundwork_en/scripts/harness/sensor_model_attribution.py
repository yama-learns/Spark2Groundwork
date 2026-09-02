#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: model attribution (on demand)

**Rule source:** `governance/MODEL_IDENTITY.md` §3.4 (an artefact's author field must name the
concrete model) and §3.6 rule 2 (a platform name is not a model); `governance/HANDOFF.md` §3
(the first of the five required items in a handoff packet).

## Checks

    MODEL_ATTRIBUTION_MISSING     No model field in the artefact's header          FAIL
    MODEL_ATTRIBUTION_VAGUE       Only a family or platform name, no concrete model FAIL
    MODEL_UNREADABLE_DECLARED     Correctly declared "cannot read"                  WARN
    SCAN_GLOB_MATCHES_NOTHING     The scan matched zero files                       WARN

## 🔴 This sensor was rewritten from scratch, and the reason belongs here

**The old version carried two hard-coded whitelists** (`GRANDFATHERED`, 13 entries;
`FROZEN_HANDOFFS`, 12), every one of them **a filename from another project** — one under an `mve/` directory, one a
git-policy document under another directory, and so on — **none of which exists in this framework.**
⚠️ **Those filenames are deliberately not written out here**: writing them would make them
dangling references in this very file. **"Do not instantiate a defect while describing it"**
(predecessor projects hit this same mechanism three times).
It also carried five dangling section citations (⚠️ **same reason as above: the section
numbers are deliberately not written out here** — none of them exist in this framework's
constitution, and writing them would make them this file's own dangling references), and **it emitted three WARNs on a brand-new
clean template the very first time it ran.**

> ⛔ `R-21`: whitelists and hard-coded lists **must not** define scan scope.
> ⛔ `R-19`: a sensor that fires on correct text teaches people to ignore it.

### 🔴 But the root cause was not the whitelist. **The scan scope was wrong.**

The old version scanned every `.md` in the project root. **Those files are the framework's own
templates** (`README.md`, `SETUP.md`, `file_index.md`, ...) — **not AI output, and they were
never supposed to carry an author field.** So it needed an ever-growing exemption list to
suppress the alarms it created for itself.

> **That whitelist existed to compensate for a wrong scan scope.**
> **Fix the scope and the whitelist is unnecessary — this version contains no hard-coded
> filename at all.**

**The scope now: `attribution_globs` in `framework_config.py` (discovery-based, default
`handoffs/*.md`) — only what an AI actually produced.**

## ⚠️ How "concrete model" is decided mechanically

⛔ **No list of model names** — that is just another whitelist, and it will go stale.
**The test is structural: a concrete model almost always carries a version number**
(`opus-5`, `sonnet-5`, `gemini-3.7-flash`, `o4-mini`, `haiku-4.5`), **while a family or
platform name does not** (`Claude`, `Gemini`, `Antigravity`, `Cowork`).

⚠️ A platform-name list assists as a **value domain** (⛔ a value domain, not a scan scope,
so `R-21` is not violated — same as the role whitelist in `ai_checkpoint.sh`).

## ✅ "Cannot read" is the correct answer, ⛔ not a defect

`governance/MODEL_IDENTITY.md` §3.6.3 rule 1 says verbatim that when the marker is not in visible
context, **the only correct output** is `[Model: cannot read -- ...]`.
⛔ **FAILing it would push the next model back to writing a platform name, and §3.6 rule 2
says that is worse than leaving it blank.**
→ WARN instead, with a reminder to have the human backfill it per §3.6 rule 3.

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (**⛔ not a pass**)
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import resolve_globs                   # noqa: E402

# Two accepted forms: `[Model: X]` and `**Created:** X, date`
MODEL_TAG = re.compile(r"\[Model:\s*([^\]]+)\]", re.I)
AUTHOR_FIELD = re.compile(r"^\*{0,2}(?:建立|作者|撰寫|執行模型|Created|Author|Model)"
                          r"\*{0,2}\s*[:：]\s*\*{0,2}\s*([^\n，,]+)", re.M)
# ✅ The correct "could not read it" declaration -- ⛔ not a defect
UNREADABLE = re.compile(r"無法讀取|cannot read|unreadable|not in the visible context")
# ⚠️ A value domain, not a scan scope (so R-21 holds). One platform runs many models,
#    so writing the platform name says nothing.
PLATFORMS = ("antigravity", "cowork", "claude code", "ai studio", "gemini app",
             "chatgpt", "copilot", "openai", "anthropic", "google")
# A concrete model almost always carries a version number; a family/platform name does not.
HAS_VERSION = re.compile(r"\d")
HEAD_LINES = 15


def attribution(text):
    """Return the model string declared in the header, or None."""
    head = "\n".join(text.splitlines()[:HEAD_LINES])
    m = MODEL_TAG.search(head)
    if m:
        return m.group(1).strip()
    m = AUTHOR_FIELD.search(head)
    return m.group(1).strip() if m else None


def main():
    root, cfg, as_json, name = cli("model_attribution")
    globs = cfg.get("attribution_globs", ["handoffs/*.md"])
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "attribution_globs", root)
    vague = missing = unread = 0

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} is not UTF-8; not checked "
                             f"-- **and that is not a pass**"))
            continue
        who = attribution(text)
        if who is None:
            missing += 1
            findings.append(("FAIL", "MODEL_ATTRIBUTION_MISSING",
                             f"{p.relative_to(root)} has no model field in its header "
                             f"-- `governance/HANDOFF.md` §3: a missing item means not delivered"))
            continue
        if UNREADABLE.search(who):
            # ✅ This is the only correct output per MODEL_IDENTITY §3.6.3 rule 1
            unread += 1
            findings.append(("WARN", "MODEL_UNREADABLE_DECLARED",
                             f"{p.relative_to(root)} correctly declared 'cannot read' "
                             f"-- ⛔ not a defect. Per §3.6 rule 3, ask the human to backfill"))
            continue
        low = who.lower()
        if any(pf in low for pf in PLATFORMS) or not HAS_VERSION.search(who):
            vague += 1
            findings.append(("FAIL", "MODEL_ATTRIBUTION_VAGUE",
                             f"{p.relative_to(root)}: '{who[:40]}' is not a concrete model "
                             f"-- **a platform or family name is worse than a blank: it reads "
                             f"like an answer and stops the next reader from asking** "
                             f"(`governance/MODEL_IDENTITY.md` §3.6.3 rule 2)"))

    stats = {"artefacts scanned": len(files), "no model field": missing,
             "family/platform only": vague, "declared unreadable": unread}
    return emit("Model attribution sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
