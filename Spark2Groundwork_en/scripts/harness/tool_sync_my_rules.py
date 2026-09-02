#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tool: copy newly added framework rules verbatim into `my/MY_RULES.md`

**⛔ This is not a sensor. It is the prescribed action after a sensor reports
`RULE_MISSING_IN_MY`.**

## Why this exists instead of "just paste it in yourself"

🔴 **That "paste it in yourself" step is exactly where "two copies, only one updated" comes from.**
⚠️ **A clause retyped from memory reads identically to the original ⛔ and is not the original** —
**the framework has been caught by this: the clause-sync sensor found `extremely` retyped
as `extremely high`.**

## It does two things, ⛔ and the second one writes nothing

**① Append, verbatim, the rules that exist in the framework and not in `MY_RULES.md`.**

**② List, line by line, the rules whose text differs ⛔ and that carry no override marker —
⛔ and leave the decision to you.**

## 🔴 Why ② is ⛔ not done for you (the v1.4.4 ruling)

⚠️ **During the previous version's development there was briefly an `--adopt` [withdrawn]
that replaced drifted rules with the framework wording. (That version would have been
`v1.4.3`, ⛔ and `v1.4.3` was never released — the defects were found in review before
release. ⇒ With that write path ruled back out, everything else ships as this version,
`v1.4.4`.)**
🔴 **Review found three defects in it: it wrote the file before printing the "preview", it
claimed "the checkpoint holds it" unconditionally, and it still wrote when the checkpoint
program had explicitly failed.**
**⇒ The principal ruled the entire write path back out.**

**⛔ This tool therefore ⛔ never overwrites a single existing word in `MY_RULES.md`.**
**⚠️ It prints a line-by-line difference instead, so you know which lines to paste** —
🔴 **between "a tool that silently overwrites your text" and "a difference you can read",
⛔ the risk of the first is not worth the seconds it saves.**

## What to do when the framework revises an existing rule

**Run this tool → read the difference → paste the `+` lines verbatim into that rule's body in
`my/MY_RULES.md`.**
⛔ **⛔ Never replace the whole `MY_RULES.md`** — that erases your `P-xx` rules and overrides.
⚠️ **Or, if the change was yours on purpose, add a line inside that rule with the override
marker and your reason.**

Exit codes: 0 done (including "0 to add") | 1 file problem | 2 could not check
"""
import argparse
import difflib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import _force_utf8                            # noqa: E402
from framework_config import load                          # noqa: E402
from sensor_my_rules import parse, is_override                          # noqa: E402

_force_utf8()
MARKER = "<!-- FRAMEWORK_RULES_END"



def preview(rid, old, new, limit=8):
    """Print the **actual changed lines** (adjudication `A4a: A`).

    🔴 **The old version printed "old first line → new first line", ⛔ and every change in
    `R-34` is on the second line or later** — **⇒ on the first real case (`R-34`), that
    preview printed two identical lines.**
    ⚠️ **That is ⛔ not merely unhelpful; it tells the user nothing changed.**

    Returns the number of difference lines found; **0 means the criterion claimed a drift while
    the diff is empty** — ⛔ **a contradiction, and the caller must refuse to write.**
    """
    o, n = old.split("\n"), new.split("\n")
    rows = [l for l in difflib.unified_diff(o, n, lineterm="", n=0)
            if not l.startswith(("---", "+++", "@@"))]
    print(f"  {rid}　body {len(o)} lines → {len(n)} lines")
    for l in rows[:limit]:
        print(f"    {l}")
    if len(rows) > limit:
        print(f"    …({len(rows) - limit} more lines not shown; "
              f"see {rid} in the framework's `governance/RULES.md` for the full text)")
    return len(rows)


def _skip_note(body, marker):
    """For a skipped rule, ⛔ say which kind of skip it is.

    🔴 **`is_override()` returns two values: `(marker present, reason long enough)`.**
    ⚠️ **The old version read only `[0]`, so a rule marked as an override with no reason was
    described here as "marked as an override" while `sensor_my_rules.py` was reporting
    `OVERRIDE_WITHOUT_REASON` FAIL against that very rule.**
    **⇒ The user was told the rule was properly recorded while sitting in a FAIL they could
    not clear.**

    ⛔ **The behaviour does ⛔ not change (a marker present means hands off, which is right);
    what changes is what this sentence says.**
    """
    marked, has_reason = is_override(body, marker)
    if marked and has_reason:
        return f"is marked {marker}"
    return (f"is marked {marker} ⛔ with no reason on that line — "
            "🔴 **this tool leaves it alone, ⛔ but the sensor reports "
            "`OVERRIDE_WITHOUT_REASON` FAIL against it.** "
            "→ add the reason, or remove the marker and paste the framework wording back "
            "yourself using the difference shown above")

def main(argv=None):
    # Parse every argument before any read or write. argparse still rejects an unknown
    # option with exit 2; harmonising that semantic is explicitly deferred to v1.5.0.
    ap = argparse.ArgumentParser(
        description="Append newly added framework rules verbatim to a project's my/MY_RULES.md")
    ap.add_argument("--root", default=None,
                    help="project root; defaults to the project containing this tool")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve() if a.root else HERE.parents[1]
    cfg = load(root)
    fw_p = root / cfg.get("framework_rules", "governance/RULES.md")
    my_p = root / cfg.get("my_rules", "my/MY_RULES.md")

    # ⛔ This is the R-33 position: a failed precondition must ⛔ not fall through to
    #    the "nothing to do" branch.
    for p in (fw_p, my_p):
        if not p.is_file():
            print(f"[INCOMPLETE] {p} does not exist — "
                  "**⛔ nothing was added, and that is not the same as nothing needing to be added**")
            return 2

    fw_text = fw_p.read_text(encoding="utf-8")
    my_text = my_p.read_text(encoding="utf-8")
    if MARKER not in my_text:
        print(f"[FAIL] no insertion point `{MARKER} …` in {my_p.name} — "
              "**⛔ that line was deleted. Take a fresh `MY_RULES.md` header from the framework**")
        return 1

    marker = cfg.get("override_marker", "[project override]")
    fw, my = parse(fw_text), parse(my_text)
    missing = [k for k in sorted(fw) if k.startswith("R-") and k not in my]

    # ⚠️ **Three piles, ⛔ and all three need a denominator** (`R-35`).
    drift, protected = [], []
    for k in sorted(fw):
        if not k.startswith("R-") or k not in my or my[k] == fw[k]:
            continue
        (protected if is_override(my[k], marker)[0] else drift).append(k)

    print(f"framework rules: {len([k for k in fw if k.startswith('R-')])}")
    print(f"already covered here: {len([k for k in my if k.startswith('R-')])}")
    print(f"text differs: {len(drift) + len(protected)} "
          f"({len(protected)} marked {marker}, ⛔ never touched by this tool)")

    # ⛔ R-33: "nothing to do" must ⛔ not be the default branch.
    #    ⚠️ **That judgement moved to after ①**: the criterion is "the computed text equals the
    #    original", ⛔ not "missing and drift are both empty" — **drift is always reported,
    #    ⛔ even when there is nothing to append.**

    # ── ① Compute: ⛔ this tool overwrites no existing text ───────
    text = my_text
    if missing:
        block = "\n\n".join(fw[k] for k in missing)
        i = text.index(MARKER)
        text = text[:i] + block + "\n\n" + text[i:]

    def _report_drift():
        """🔴 A read-only report: print the differing lines, ⛔ and leave the decision to a person."""
        if not drift:
            return
        print(f"\n🔴 **{len(drift)} rule(s) differ from the framework ⛔ and are not "
              f"marked {marker}:**")
        for k in drift:
            preview(k, my[k], fw[k])
        print("\n**⛔ This tool did not touch them, and never will.** Two ways forward:\n"
              "  ① the framework revised the rule →\n"
              "     **paste the `+` lines above verbatim into that rule's body in "
              "`my/MY_RULES.md`.**\n"
              "     ⛔ **⛔ Never replace the whole `MY_RULES.md`** — that erases your `P-xx` "
              "rules and overrides.\n"
              f"  ② you changed it on purpose → add a line inside that rule with {marker} "
              "and your reason\n"
              "⚠️ **⛔ Left alone, `sensor_my_rules.py` will keep reporting `RULE_TEXT_DRIFT`.**")

    def _report_protected():
        for k in protected:
            print(f"  (skipped) {k} {_skip_note(my[k], marker)}")

    if text == my_text:
        # ⛔ R-33: "nothing to do" must ⛔ not be the default branch.
        print("\n**⛔ There is nothing to append** — that is a computed result, not a skipped one.")
        _report_drift()
        _report_protected()
        return 0

    my_p.write_text(text, encoding="utf-8")
    print(f"\n  ✅ Appended {len(missing)}. "
          "⛔ **⛔ No existing text was overwritten** — this tool only appends at the end of §1.")
    for k in missing:
        print(f"  + {fw[k].split(chr(10), 1)[0]}")
    _report_drift()
    _report_protected()
    print("\n⚠️ **⛔ Read every rule that was just added.** They now bind you and your AI.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
