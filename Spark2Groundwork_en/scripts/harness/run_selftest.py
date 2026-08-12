#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired seeded-defect self-test (cross-platform)

⚠️ **Both halves are necessary.**
Testing only "does it catch what it should" cannot distinguish "the sensor works" from
"the sensor errors on everything" — a predecessor project's harness once false-alarmed
on every file and looked entirely normal.

⛔ **When the self-test fails, first assume the sensors are broken, not your documents.**
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "selftest"
PY = sys.executable
ok = bad = 0


def run(sensor, root):
    r = subprocess.run([PY, str(HERE / sensor), "--root", str(root)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def expect(desc, want_code, sensor, fixture, needle=None):
    global ok, bad
    root = FIX / fixture
    if not root.exists():
        print(f"  FAIL {desc} (fixture missing: {fixture})"); bad += 1; return
    code, out = run(sensor, root)
    hit = (code == want_code) and (needle is None or needle in out)
    if hit:
        print(f"  ok   {desc}"); ok += 1
    else:
        extra = f" containing '{needle}'" if needle else ""
        print(f"  FAIL {desc} (expected exit {want_code}{extra}, got exit {code})"); bad += 1


print("-- Paired seeded-defect self-test ------------------------")

# Conjecture ledger
expect("empty falsification warns", 0, "sensor_conjecture_ledger.py",
       "conj_nofalsif", "FALSIFICATION_UNADJUDICATED")
expect("filled but unadjudicated still warns", 0, "sensor_conjecture_ledger.py",
       "conj_filled_unadjudicated", "FALSIFICATION_UNADJUDICATED")
expect("missing rival fails", 1, "sensor_conjecture_ledger.py", "conj_norival", "RIVAL_EMPTY")
expect("correct ledger does not false-alarm", 0, "sensor_conjecture_ledger.py", "conj_clean")

# Claim ledger (anchors)
expect("missing anchor fails", 1, "sensor_claim_ledger.py", "claim_ghost", "ANCHOR_NOT_IN_SOURCE")
expect("ligature and hyphenation do not false-alarm", 0, "sensor_claim_ledger.py", "claim_ligature")
expect("correct anchor does not false-alarm", 0, "sensor_claim_ledger.py", "claim_clean")

# Self-certification
expect("self-certification is caught", 1, "sensor_self_certification.py", "selfcert_bad")
expect("gate-style requirement does not false-alarm", 0, "sensor_self_certification.py", "selfcert_clean")

# Governance text
expect("cross-file duplicate warns", 0, "sensor_governance_text.py", "gov_dup", "DUPLICATE_RULE_TEXT")
expect("dangling section citation warns", 0, "sensor_governance_text.py",
       "gov_badref", "SECTION_REF_UNRESOLVED")
expect("clean governance text does not false-alarm", 0, "sensor_governance_text.py", "gov_clean")

print("\n" + "=" * 56)
print(f"  passed {ok} | failed {bad}")
print("  Result: " + ("all self-tests passed" if not bad
                      else "SELF-TEST FAILED — ⛔ do not commit sensor changes"))
sys.exit(1 if bad else 0)
