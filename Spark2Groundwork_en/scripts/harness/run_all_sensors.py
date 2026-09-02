#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runner for all sensors (cross-platform)

⚠️ **Python rather than shell, deliberately**: Windows has no built-in bash, and this
framework's users may not be able to install WSL.
**A sensor suite that cannot run is not a sensor suite.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (⛔ **incomplete is not a pass**)
"""
import json
import os
import pathlib
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# sensor -> optional?
SENSORS = [
    ("sensor_conjecture_ledger.py", False),
    ("sensor_claim_ledger.py", False),
    ("sensor_self_certification.py", False),
    ("sensor_governance_text.py", False),
    ("sensor_scope_and_t0.py", False),
    ("sensor_reference_integrity.py", False),
    ("sensor_clause_sync.py", False),
    ("sensor_my_rules.py", False),
    ("sensor_my_index.py", False),
    ("sensor_version_consistency.py", False),
]

# ⚠️ **Not in the default suite: their interface is a single file, not a whole project.**
#    Forcing them into the runner only produces a permanently-INCOMPLETE false signal —
#    and INCOMPLETE is the one state this framework cannot afford to dilute.
#    Usage: see profiles/PROFILE_external_tools.md
#        python3 scripts/harness/sensor_prompt_self_contained.py <prompt.md>
ON_DEMAND = ["sensor_prompt_self_contained.py"]


def main() -> int:
    results, worst = [], 0
    for name, optional in SENSORS:
        p = HERE / name
        if not p.exists():
            if not optional:
                print(f"  [INCOMPLETE] SENSOR_MISSING: {name} not found — **not checked, and that is not a pass**")
                worst = max(worst, 2)
            continue
        # ⛔ Pin UTF-8 explicitly: ⚠️ `text=True` decodes the child with the system default,
        #    and on Windows that is the ANSI code page — **the child writes UTF-8 while the
        #    parent decodes cp950, and both ends break.**
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(p), "--root", str(ROOT)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        print(r.stdout.rstrip())
        # 🔴 **An uncaught Python exception always exits 1**, and 1 means "found a defect".
        #    ⚠️ Measured (Traditional-Chinese Windows): two sensors died of
        #    `UnicodeEncodeError` → exit 1 → the summary printed "the whole suite FAILED",
        #    **while what actually happened is that they never finished running.**
        #    ⛔ That is the confusion `R-22` / constitution §7.4 forbid, in the runner itself.
        #    → Criterion: **non-zero exit + a Python traceback on stderr = a crash, not a FAIL.**
        crashed = r.returncode != 0 and "Traceback (most recent call last)" in (r.stderr or "")
        if crashed:
            print(f"  [INCOMPLETE] SENSOR_CRASHED: {name} crashed — **not checked; ⛔ this is not a FAIL**")
            print((r.stderr or "").rstrip()[-600:])
            worst = max(worst, 2)
        elif r.returncode not in (0, 1, 2):
            # ⚠️ A crash is "could not check", not "found a problem". Conflating them makes
            #    "the sensor is broken" look like "the document has a problem", which sends
            #    someone to fix a document that was fine.
            print(f"  [INCOMPLETE] SENSOR_CRASHED: {name} exit code {r.returncode}")
            print((r.stderr or "").rstrip()[-600:])
            worst = max(worst, 2)
        else:
            # ⚠️ Precedence: 2 INCOMPLETE > 1 FAIL > 0 PASS. **Never the other way round.**
            # The old form overwrote worst with 1 unconditionally when returncode==1,
            # so an INCOMPLETE followed by a FAIL was swallowed (measured: [2,1] -> 1).
            # ⛔ **That is exactly the dilution §7.4 forbids, in the runner itself.**
            worst = max(worst, r.returncode)
        results.append({"sensor": name, "code": r.returncode})

    print("\n" + "=" * 48)
    label = {0: "✅ SUMMARY: PASS", 1: "❌ SUMMARY: FAIL",
             2: "⚠️  SUMMARY: INCOMPLETE (**incomplete is not a pass**)"}[worst]
    print(f"  {label} ({len(results)} sensors run)")
    print("      ⚠️ Green covers only what is mechanised.")
    print("      Argument quality, substantive support, and honest generalisation are not.")
    (HERE / "harness_status.json").write_text(
        json.dumps({"worst": worst, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return worst


if __name__ == "__main__":
    sys.exit(main())
