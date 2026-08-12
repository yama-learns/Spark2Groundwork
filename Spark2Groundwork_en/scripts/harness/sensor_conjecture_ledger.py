#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: Conjecture Ledger (evidence-chain link ③ — required fields)

## Checks

    FALSIFICATION_UNADJUDICATED   Falsification condition not adjudicated by a human   WARN/FAIL
    RIVAL_EMPTY                   No named rival hypothesis                            FAIL
    RIVAL_PREDICTION_EMPTY        Rival's differing prediction not stated               FAIL
    CONJECTURE_ID_DUPLICATE       Duplicate C-NN                                        FAIL
    CONJECTURE_FIELD_MISSING      A required field is absent                            FAIL

## 🔴 Why the warning condition is "not adjudicated" rather than "field is empty"

The first version warned only on an empty field. **Measured, in this framework's own
live test: putting a plausible-sounding fake condition into the field made the warning
count drop by one, with the exit code unchanged.**

The tested agent's own words:

> Leaving "-" makes it look like I did less; writing "if X exceeds r > .8 then this is refuted"
> reads as entirely acceptable, and **nobody, human or sensor, can tell it is decorative**.
> **The incentives run backwards: honesty gets a yellow light, invention does not.**

⚠️ Related: a placeholder list that matches exact strings only will treat
"falsification pending" as **filled**, and pass it silently.

→ **Filling in text does not clear the warning. Only a human setting
`Falsification adjudicated: adjudicated` does.** ⛔ AI must not set that field.

ℹ️ States above Conjecture do not need the field — **the state upgrade is itself the
adjudication** (it requires independently checkable grounds).
Not adding a redundant field to every entry is deliberate.

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                      # noqa: E402

HEAD = re.compile(r"^###\s+(C-\d+)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*$")
FIELD = re.compile(r"^\*\*(.+?)[:：]\*\*\s*(.*)$")
PLACEHOLDER = {"", "-", "—", "–", "TBD", "n/a", "N/A", "?", "pending"}
REQUIRED = ["Statement", "Origin", "Falsification", "Strongest rival",
            "Rival's differing prediction"]


def is_placeholder(v):
    return v.strip() in PLACEHOLDER


def is_template(v):
    """A field still holding a `<<<FILL IN...>>>` marker means the template is unfilled.

    ⚠️ **An unfilled template and a filled-but-defective ledger are different states.**
    Reporting FAIL on a brand-new project contradicts the setup guide, which tells the
    user that a batch of warnings on the first run is normal —
    **and a first run that fails teaches the user that red means nothing.**
    """
    return "<<<" in v


def parse(text):
    entries, dup, cur = {}, [], None
    for lineno, line in enumerate(text.splitlines(), 1):
        m = HEAD.match(line.rstrip())
        if m:
            cid = m.group(1)
            if cid in entries:
                dup.append((cid, lineno))
            cur = {"state": m.group(2), "scope": m.group(3), "fields": {}}
            entries[cid] = cur
            continue
        if cur is None:
            continue
        f = FIELD.match(line.rstrip())
        if f:
            cur["fields"][f.group(1).strip()] = f.group(2).strip()
    return entries, dup


def main():
    root, cfg, as_json, name = cli("conjecture_ledger")
    led = root / cfg["conjecture_ledger"]
    if not led.exists():
        return emit("Conjecture Ledger sensor",
                    [("INCOMPLETE", "LEDGER_MISSING",
                      f"{cfg['conjecture_ledger']} not found — "
                      f"**not checked, and that is not a pass**")],
                    {}, as_json, name)

    entries, dup = parse(led.read_text(encoding="utf-8"))
    findings = [("FAIL", "CONJECTURE_ID_DUPLICATE", f"{cid} appears twice (line {ln})")
                for cid, ln in dup]
    unadj = 0

    for cid, e in entries.items():
        f, state = e["fields"], e["state"]

        # ⚠️ Template-not-filled is judged **once for the whole entry, before the
        #    per-field checks** — otherwise the next field still emits FAIL and a fresh
        #    project's first run is red anyway.
        #    **Same shape as the branch-order bug in changelog #1: the guard sat in the
        #    right place for one field and the wrong place for the one after it.**
        if any(is_template(f.get(k, "")) for k in REQUIRED):
            findings.append(("WARN", "TEMPLATE_NOT_FILLED",
                             f"{cid} still holds template placeholders — "
                             f"fill them in before real use"))
            continue

        for k in REQUIRED:
            if k not in f:
                findings.append(("FAIL", "CONJECTURE_FIELD_MISSING",
                                 f"{cid} is missing the required field '{k}'"))

        falsif = f.get("Falsification", "")
        adjudicated = f.get("Falsification adjudicated", "").strip().lower() == "adjudicated"
        is_conjecture = "conjecture" in state.lower()

        # ⚠️ **Branch order: split on empty/filled first, then on state.**
        #    The first version tested emptiness first, so an empty field on a
        #    non-Conjecture state was swallowed by the earlier branch and
        #    **silently downgraded from FAIL to WARN**. The self-test caught it.
        if is_placeholder(falsif):
            unadj += 1
            if is_conjecture:
                findings.append(("WARN", "FALSIFICATION_UNADJUDICATED",
                                 f"{cid} ({state}) falsification condition empty — a conjecture "
                                 f"you cannot falsify is not a hypothesis, it is a worldview"))
            else:
                findings.append(("FAIL", "FALSIFICATION_UNADJUDICATED",
                                 f"{cid} ({state}) falsification condition empty, "
                                 f"but the state is beyond 'Conjecture'"))
        elif is_conjecture and not adjudicated:
            unadj += 1
            findings.append(("WARN", "FALSIFICATION_UNADJUDICATED",
                             f"{cid} ({state}) falsification condition filled but not "
                             f"adjudicated — **text in the field does not make it "
                             f"observable; only a human can judge that**"))

        if is_placeholder(f.get("Strongest rival", "")):
            findings.append(("FAIL", "RIVAL_EMPTY", f"{cid} names no rival hypothesis"))
        if is_placeholder(f.get("Rival's differing prediction", "")):
            findings.append(("FAIL", "RIVAL_PREDICTION_EMPTY",
                             f"{cid} does not state where the rival's prediction differs "
                             f"— a decorative rival is worse than none"))

    return emit("Conjecture Ledger sensor", findings,
                {"conjectures": len(entries), "unadjudicated": unadj}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
