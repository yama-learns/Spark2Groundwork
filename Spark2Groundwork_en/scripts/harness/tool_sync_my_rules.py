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

## ⛔ It does exactly one thing

**Append, verbatim, the rules that exist in the framework and not in `MY_RULES.md`
to the end of §1, and print which ones it added.**

⛔ **It does ⛔ NOT overwrite existing entries** — **if a rule's text differs, that is
`RULE_TEXT_DRIFT`, and a person decides whether to mark it as an override or put it back.
⚠️ A tool that overwrites silently erases the user's deliberate edits.**

Exit codes: 0 done (including "0 to add") | 1 file problem | 2 could not check
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import _force_utf8                            # noqa: E402
from framework_config import load                          # noqa: E402
from sensor_my_rules import parse                          # noqa: E402

_force_utf8()
MARKER = "<!-- FRAMEWORK_RULES_END"


def main():
    root = HERE.parents[1]
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

    fw, my = parse(fw_text), parse(my_text)
    missing = [k for k in sorted(fw) if k.startswith("R-") and k not in my]

    print(f"framework rules: {len([k for k in fw if k.startswith('R-')])}")
    print(f"already covered here: {len([k for k in my if k.startswith('R-')])}")
    if not missing:
        # ⚠️ **"0 to add" is the result of taking stock, ⛔ so print the denominator** (R-35).
        print("to add: 0. **⛔ This is a comparison that ran, not a comparison that was skipped.**")
        return 0

    block = "\n\n".join(fw[k] for k in missing)
    i = my_text.index(MARKER)
    my_p.write_text(my_text[:i] + block + "\n\n" + my_text[i:], encoding="utf-8")

    print(f"to add: {len(missing)} → appended verbatim at the end of §1:")
    for k in missing:
        print(f"  + {fw[k].split(chr(10), 1)[0]}")
    print("\n⚠️ **⛔ Read every rule that was just added.** They now bind you and your AI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
