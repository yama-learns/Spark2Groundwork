#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: Conjecture Ledger (evidence-chain links ①②③ — the field layer)

## Checks

    LEDGER_MISSING                Conjecture Ledger not found                          FAIL
    CONJECTURE_ID_DUPLICATE       Duplicate C-NN                                       FAIL
    CONJECTURE_STATUS_INVALID     State is not one of the six in §0.1                  FAIL
    CONJECTURE_FIELD_MISSING      A required field is absent                           FAIL
    TEMPLATE_NOT_FILLED           Entry still holds `<<<FILL IN...>>>` markers          WARN
    FALSIFICATION_UNADJUDICATED   Falsification condition not adjudicated by a human   WARN/FAIL
    RIVAL_EMPTY                   No named rival hypothesis                            FAIL
    RIVAL_PREDICTION_EMPTY        Rival's differing prediction not stated              FAIL
    EVIDENCE_MISSING_FOR_STATUS   Basis empty while the state is 🟢 or 🔴               FAIL
    CITATION_NOT_IN_LEDGER        Another document cites a C-NN not in the ledger       FAIL
    SCAN_GLOB_MATCHES_NOTHING     The citation scan matched zero files            INCOMPLETE

## Design

* **Precision over coverage** (`R-19`): a sensor that fires on correct text teaches people
  to ignore it.
* This sensor checks **whether a field holds something**, not whether what it holds is
  correct. The latter is evidence-chain links ⑥⑦ and is deliberately not mechanised
  (`governance/WORKFLOW_CONSTITUTION.md` §2).
* **Incomplete is not a pass** (`R-22`): when the citation scan matches nothing it reports
  INCOMPLETE, not PASS.

## 🔴 Why the warning condition is "not adjudicated" rather than "field is empty"

The first version warned only on an empty field. **Measured, in this framework's own live
test: putting a plausible-sounding fake condition into the field made the warning count drop
by one, with the exit code unchanged.**

The tested agent's own words:

> Leaving "-" makes it look like I did less; writing "if X exceeds r > .8 then this is refuted"
> reads as entirely acceptable, and **nobody, human or sensor, can tell it is decorative**.
> **The incentives run backwards: honesty gets a yellow light, invention does not.**

→ **Filling in text does not clear the warning. Only a human setting
`Falsification adjudicated: adjudicated` does.** ⛔ AI must not set that field.

ℹ️ ⚫ **Unfalsifiable (retired)** and 🟤 **Dormant** are exempt from the falsification check:
⚫ *means* "no observable falsification condition could be produced", and 🟤 means "not in
scope this round" — **that is not an epistemic verdict and should not be raised again every round**.

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (**⛔ not a pass**)
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                                 # noqa: E402
from framework_config import excluded                         # noqa: E402

HEAD = re.compile(r"^###\s+(C-\d+)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*$")
FIELD = re.compile(r"^\*\*(.+?)[:：]\*\*\s*(.*)$")
# ⚠️ Two digits minimum. `C-1` written for a work item would otherwise be read as a citation
#    of C-01 — see `ledgers/Conjecture_Ledger.md` §0.4.
CITATION = re.compile(r"\bC-(\d{2,})\b")
PLACEHOLDER = {"", "-", "—", "–", "TBD", "n/a", "N/A", "?", "pending", "..."}
REQUIRED = ["Statement", "Origin", "Falsification", "Strongest rival",
            "Rival's differing prediction", "Basis", "Log"]

# ⚠️ **Single home: `ledgers/Conjecture_Ledger.md` §0.1.** Keep these in step.
STATES = {"🔵": "Conjecture", "🟡": "Falsifiable", "🟢": "Literature-supported",
          "🔴": "Refuted", "⚫": "Unfalsifiable (retired)", "🟤": "Dormant"}
NO_FALSIFICATION_NEEDED = {"⚫", "🟤"}
EVIDENCE_REQUIRED = {"🟢", "🔴"}


def safe_read(path):
    """Read a text file; return None instead of raising when it is not UTF-8.

    ⚠️ **This function exists because of a real crash.** An audit agent's sandbox contained a
    UTF-16 file produced by PowerShell `echo`; its BOM's first byte 0xff made
    `read_text(encoding="utf-8")` raise `UnicodeDecodeError`, **two sensors died outright,
    and the runner counted the crash as "found a defect".**

    🔴 **Two independent defects there:**
    1. **One non-UTF-8 file anywhere can stop the whole harness** — and that file need not
       even belong to the project.
    2. **A crash was counted as FAIL.** A crash is "could not check", not "found a problem"
       (`R-22`). Conflating them makes "the sensor is broken" look like "the document has a
       problem", which sends someone to fix a document that was fine.
    """
    try:
        # ⛔ Must be path.read_text here. Rewriting it to safe_read recurses forever —
        #    a batch edit once did exactly that and killed two sensors at once.
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


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

    entries, dup = parse(safe_read(led) or "")
    findings = [("FAIL", "CONJECTURE_ID_DUPLICATE", f"{cid} appears twice (line {ln})")
                for cid, ln in dup]
    unadj = 0

    for cid, e in sorted(entries.items()):
        f, state = e["fields"], e["state"]
        sym = state.strip()[:1]

        # ⚠️ Template-not-filled is judged **once for the whole entry, before the
        #    per-field checks** — otherwise the next field still emits FAIL and a fresh
        #    project's first run is red anyway.
        if any(is_template(f.get(k, "")) for k in REQUIRED) or is_template(e["scope"]):
            findings.append(("WARN", "TEMPLATE_NOT_FILLED",
                             f"{cid} still holds template placeholders — "
                             f"fill them in before real use"))
            continue

        # ⚠️ Six states, not four. `ledgers/Conjecture_Ledger.md` §0.1 defines ⚫ and 🟤 as
        #    legitimate; a sensor that accepts only four **FAILs a correctly retired or
        #    dormant conjecture** — precisely the false alarm `R-19` forbids.
        if sym not in STATES:
            findings.append(("FAIL", "CONJECTURE_STATUS_INVALID",
                             f"{cid} state '{state}' is not one of the six in "
                             f"`ledgers/Conjecture_Ledger.md` §0.1"))
            continue

        for k in REQUIRED:
            if k not in f:
                findings.append(("FAIL", "CONJECTURE_FIELD_MISSING",
                                 f"{cid} is missing the required field '{k}'"))

        falsif = f.get("Falsification", "")
        adjudicated = f.get("Falsification adjudicated", "").strip().lower() == "adjudicated"

        # ⚫ and 🟤 are exempt — see the module docstring.
        if sym not in NO_FALSIFICATION_NEEDED and not adjudicated:
            # ⚠️ **Branch order: split on empty/filled first, then on state.**
            declared = f.get("Why I could not fill this", "")
            if is_placeholder(falsif) and not is_placeholder(declared):
                # 🔴 **"Deliberately blank, with a reason" and "the field is empty" are
                #    different states, and the message must say which one it is.**
                #    Ledger §0.3 rule 1 says verbatim that writing "—" is no worse than
                #    inventing something — **and the old message printed "falsification
                #    condition empty" for exactly that, word for word identical to a
                #    forgotten field.**
                #    ⚠️ The consequence is hard to see: **the next person reads "empty" and
                #    fills it in** — which is the behaviour §0.3 rule 1 exists to prevent.
                findings.append(("WARN", "FALSIFICATION_DECLARED_UNFALSIFIABLE",
                                 f"{cid} ({STATES[sym]}) declares no falsification condition "
                                 f"is possible and gives a reason — awaiting a human decision "
                                 f"on retiring (⚫) or splitting (ledger §0.1b)"))
            elif is_placeholder(falsif):
                unadj += 1
                if sym == "🔵":
                    findings.append(("WARN", "FALSIFICATION_UNADJUDICATED",
                                     f"{cid} ({STATES[sym]}) falsification condition empty — a "
                                     f"conjecture you cannot falsify is not a hypothesis, "
                                     f"it is a worldview"))
                else:
                    findings.append(("FAIL", "FALSIFICATION_UNADJUDICATED",
                                     f"{cid} ({STATES[sym]}) falsification condition empty, "
                                     f"but the state is beyond 'Conjecture'"))
            else:
                unadj += 1
                findings.append(("WARN", "FALSIFICATION_UNADJUDICATED",
                                 f"{cid} ({STATES[sym]}) falsification condition filled but not "
                                 f"adjudicated — **text in the field does not make it "
                                 f"observable; only a human can judge that**"))

        if is_placeholder(f.get("Strongest rival", "")):
            findings.append(("FAIL", "RIVAL_EMPTY", f"{cid} names no rival hypothesis"))
        if is_placeholder(f.get("Rival's differing prediction", "")):
            findings.append(("FAIL", "RIVAL_PREDICTION_EMPTY",
                             f"{cid} does not state where the rival's prediction differs "
                             f"— a decorative rival is worse than none"))
        if sym in EVIDENCE_REQUIRED and is_placeholder(f.get("Basis", "")):
            findings.append(("FAIL", "EVIDENCE_MISSING_FOR_STATUS",
                             f"{cid} is {sym} ({STATES[sym]}) but Basis is empty — a state "
                             f"upgrade needs independently checkable grounds"))

    # ── Citation consistency: every C-NN elsewhere must exist in the ledger ──────
    # ⚠️ The ledger itself is excluded by **resolved path**, not by filename.
    #    An earlier version compared `p.name` against the config value
    #    `"ledgers/Conjecture_Ledger.md"` — a path, never equal to a bare name — so the
    #    ledger was always in scope and `SCAN_GLOB_MATCHES_NOTHING` could never fire.
    #    **A guard that cannot trigger is the same shape as a dead exemption.**
    led_resolved = led.resolve()
    targets = [p for p in root.rglob("*.md")
               if p.resolve() != led_resolved and not excluded(p, root, cfg)]

    if not targets:
        findings.append(("INCOMPLETE", "SCAN_GLOB_MATCHES_NOTHING",
                         "the citation scan matched zero files — a place that is never "
                         "scanned has no sensor over it"))
    else:
        # 🔴 Proposal-file exemption (decision 8). The criterion is **structural**: under
        #    handoffs/ plus a filename marker. ⛔ Only this check is skipped; the rest run.
        #    ⛔ Exempted files are always printed.
        markers = cfg.get("proposal_markers", [])
        exempted = []
        for f_ in targets:
            rel = f_.relative_to(root).as_posix()
            if rel.startswith("handoffs/") and any(mk in f_.name for mk in markers):
                exempted.append(rel)
                continue
            for lineno, line in enumerate((safe_read(f_) or "").splitlines(), 1):
                for m in CITATION.finditer(line):
                    cid = f"C-{m.group(1)}"
                    if cid not in entries:
                        findings.append(("FAIL", "CITATION_NOT_IN_LEDGER",
                                         f"{rel}:{lineno} cites {cid}, "
                                         f"which is not in the ledger"))
        if exempted:
            findings.append(("WARN", "CITATION_CHECK_EXEMPTED",
                             f"{len(exempted)} proposal file(s) exempted from the citation "
                             f"existence check: {', '.join(exempted[:4])}"
                             f"{'...' if len(exempted) > 4 else ''}"
                             " — **an exemption is not an absence. Remove the marker once "
                             "the adjudication has landed.**"))

    stats = {"conjectures": len(entries), "unadjudicated": unadj,
             "files scanned for citations": len(targets),
             "by state": {STATES[s]: sum(1 for e in entries.values()
                                         if e["state"].strip()[:1] == s)
                          for s in STATES
                          if any(e["state"].strip()[:1] == s for e in entries.values())}}
    return emit("Conjecture Ledger sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
