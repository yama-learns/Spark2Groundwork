#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runner for all sensors (cross-platform)

⚠️ **Python rather than shell, deliberately**: Windows has no built-in bash, and this
framework's users may not be able to install WSL.
**A sensor suite that cannot run is not a sensor suite.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (⛔ **incomplete is not a pass**)
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# sensor -> optional?
SENSORS = [
    ("sensor_conjecture_ledger.py", False),
    ("sensor_claim_ledger.py", False),
    ("sensor_self_certification.py", False),
    ("sensor_governance_text.py", False),
    ("sensor_scope_and_t0.py", False),
]

# ⚠️ **Not in the default suite: their interface is a single file, not a whole project.**
#    Forcing them into the runner only produces a permanently-INCOMPLETE false signal —
#    and INCOMPLETE is the one state this framework cannot afford to dilute.
#    Usage: see profiles/PROFILE_external_tools.md
#        python3 scripts/harness/sensor_prompt_self_contained.py <prompt.md>
ON_DEMAND = ["sensor_prompt_self_contained.py", "sensor_model_attribution.py"]


def main() -> int:
    results, worst = [], 0
    for name, optional in SENSORS:
        p = HERE / name
        if not p.exists():
            if not optional:
                print(f"  [INCOMPLETE] SENSOR_MISSING: {name} not found — **not checked, and that is not a pass**")
                worst = max(worst, 2)
            continue
        r = subprocess.run([sys.executable, str(p), "--root", str(ROOT)],
                           capture_output=True, text=True)
        print(r.stdout.rstrip())
        if r.returncode not in (0, 1, 2):
            # ⚠️ A crash is "could not check", not "found a problem". Conflating them makes
            #    "the sensor is broken" look like "the document has a problem", which sends
            #    someone to fix a document that was fine.
            print(f"  [INCOMPLETE] SENSOR_CRASHED: {name} exit code {r.returncode}")
            print((r.stderr or "").rstrip()[-600:])
            worst = max(worst, 2)
        else:
            worst = max(worst, r.returncode) if r.returncode != 1 else 1
            if r.returncode == 1:
                worst = 1 if worst != 2 else 2
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
