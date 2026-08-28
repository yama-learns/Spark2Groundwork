#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired seeded-defect self-test (cross-platform)

⚠️ **Both halves are required.**
Testing only "does it catch what it should" cannot distinguish "the sensor works" from
"the sensor fires on every file" — a predecessor project's harness once false-alarmed on
everything and still looked fine.

⛔ **When a self-test fails, assume the sensor is broken, not the project documents.**

## 🔴 Why the "must not false-alarm" half cannot check the exit code alone

**Triggering case (measured in another project, then confirmed to hold here):**
a `WARN`-level finding **does not change the exit code** (see `emit` in `_common.py`:
only FAIL→1 and INCOMPLETE→2). So a "must not false-alarm" test that asserts only
`exit == 0` **prints ✅ for any number of WARN-level false alarms.**

**Measured here, before this fix:** of the five "must not false-alarm" fixtures,
`selfcert_clean` emitted 2 WARNs and `gov_clean` emitted 3 — **and the self-test printed ✅
for both.**

→ So `expect()` gains **`forbid`**: the finding codes that must **never** appear on this
clean fixture.
⚠️ The criterion is deliberately **not "no WARN at all"** — a fixture directory does not
contain every glob, so `SCAN_GLOB_MATCHES_NOTHING` is infrastructure noise, not a sensor
false alarm. **Treating noise as a false alarm pushes the next person to add an exemption,
and exemptions hollow the self-test into a blind spot.**

⛔ **But tolerance must be visible:** every tolerated WARN code and count is printed at the
end. **Silent tolerance and no tolerance look the same on screen.**
"""

import os
import pathlib
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "selftest"
PY = sys.executable
ok = bad = 0
tolerated = Counter()


def run(sensor, root):
    # ⛔ Decode the child as UTF-8 and force the child to print UTF-8 as well.
    #    ⚠️ Measured: with only one half set, `_translate_newlines` raises UnicodeDecodeError —
    #    **the self-test itself dies on Windows, and it is the program whose whole job is to
    #    prove that nothing else died.**
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, str(HERE / sensor), "--root", str(root)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def expect(desc, want_code, sensor, fixture, needle=None, forbid=()):
    """desc: one line | want_code: expected exit code | needle: string that MUST appear
    forbid: finding codes that must NEVER appear (the "must not false-alarm" half)"""
    global ok, bad
    root = FIX / fixture
    if not root.exists():
        print(f"  ❌ {desc} (fixture directory missing: {fixture})"); bad += 1; return
    code, out = run(sensor, root)
    banned = [c for c in forbid if c in out]
    hit = (code == want_code) and (needle is None or needle in out) and not banned
    # Tally tolerated WARNs.
    # ⚠️ **The code named by `needle` is deliberately excluded** — that is the detection this
    #    test requires, and counting it as "tolerated" makes the number meaningless
    #    (the first version did exactly that: 18 reported, 13 real).
    for line in out.splitlines():
        if "[WARN]" not in line:
            continue
        for tok in line.replace("]", " ").replace("[", " ").replace(":", " ").split():
            if tok.isupper() and "_" in tok:
                if not (needle and tok in needle):
                    tolerated[tok] += 1
                break
    if hit:
        print(f"  ✅ {desc}"); ok += 1
    else:
        why = []
        if code != want_code:
            why.append(f"expected exit {want_code}, got {code}")
        if needle and needle not in out:
            why.append(f"output did not contain '{needle}'")
        if banned:
            why.append(f"⛔ **FALSE ALARM**: clean fixture produced {', '.join(banned)}")
        print(f"  ❌ {desc} ({'; '.join(why)})"); bad += 1


print("-- Paired seeded-defect self-test ----------------------")

# Conjecture Ledger
expect("empty falsification condition warns", 0, "sensor_conjecture_ledger.py", "conj_nofalsif", "FALSIFICATION_UNADJUDICATED")
expect("empty rival hypothesis FAILs", 1, "sensor_conjecture_ledger.py", "conj_norival", "RIVAL_EMPTY")
expect("correct ledger does not false-alarm", 0, "sensor_conjecture_ledger.py", "conj_clean",
       forbid=("FALSIFICATION_UNADJUDICATED", "RIVAL_EMPTY", "RIVAL_PREDICTION_EMPTY",
               "CONJECTURE_FIELD_MISSING", "CONJECTURE_ID_DUPLICATE"))
expect("filled but unadjudicated still warns", 0, "sensor_conjecture_ledger.py",
       "conj_filled_unadjudicated", "FALSIFICATION_UNADJUDICATED")
expect("state outside the six FAILs", 1, "sensor_conjecture_ledger.py",
       "conj_status_bad", "CONJECTURE_STATUS_INVALID")
# ⚠️ The next one is a **regression test**, not a new-feature test.
#    ⚫ retired and 🟤 dormant are legitimate states per ledger §0.1, and the old
#    four-state VALID set flagged them CONJECTURE_STATUS_INVALID; its `continue` then
#    meant they never reached the falsification check — **two defects masking each other,
#    so fixing one alone exposes the other.**
expect("retired and dormant do not false-alarm", 0, "sensor_conjecture_ledger.py",
       "conj_retired_dormant",
       forbid=("CONJECTURE_STATUS_INVALID", "FALSIFICATION_UNADJUDICATED",
               "EVIDENCE_MISSING_FOR_STATUS"))
expect("🟢/🔴 without basis FAILs", 1, "sensor_conjecture_ledger.py",
       "conj_evidence_missing", "EVIDENCE_MISSING_FOR_STATUS")
expect("citing an ID absent from the ledger FAILs", 1, "sensor_conjecture_ledger.py",
       "conj_citation_ghost", "CITATION_NOT_IN_LEDGER")
expect("citing an existing ID does not false-alarm", 0, "sensor_conjecture_ledger.py",
       "conj_citation_ok", forbid=("CITATION_NOT_IN_LEDGER",))
# 🔴 Decision 8: the proposal-file exemption. **Both halves are required —**
#    the previous case (`conj_citation_ghost`) guards "the exemption must not be too broad":
#    a file outside handoffs/ still FAILs.
#    This one guards "the exemption must take effect, and must be printed".
#    ⚠️ The criterion is deliberately **structural** (path + filename), not a free-text
#    reason — a predecessor project learned that one plausible sentence can silence a sensor
#    on a real fabrication for good, with the dashboard green.
expect("a proposal file is exempted, and the exemption is printed", 0,
       "sensor_conjecture_ledger.py", "conj_citation_proposal",
       "CITATION_CHECK_EXEMPTED", forbid=("CITATION_NOT_IN_LEDGER",))
# ⚠️ Both halves of this pair live on the **same fixture**: it must report "declared", and
#    it must **never** report "unadjudicated/empty". The second half is the point — the old
#    message printed "falsification condition empty" for a deliberate blank with a stated
#    reason, **word for word identical to a forgotten field**, so the next person fills it
#    in — exactly what ledger §0.3 rule 1 exists to prevent.
expect("deliberate blank with a reason reports as declared", 0, "sensor_conjecture_ledger.py",
       "conj_declared_unfalsifiable", "FALSIFICATION_DECLARED_UNFALSIFIABLE",
       forbid=("FALSIFICATION_UNADJUDICATED",))

# Claim Ledger (anchors)
expect("missing anchor FAILs", 1, "sensor_claim_ledger.py", "claim_ghost", "ANCHOR_NOT_IN_SOURCE")
expect("ligatures and hyphenation do not false-alarm", 0, "sensor_claim_ledger.py", "claim_ligature",
       forbid=("ANCHOR_NOT_IN_SOURCE", "ANCHOR_EMPTY"))
expect("correct anchor does not false-alarm", 0, "sensor_claim_ledger.py", "claim_clean",
       forbid=("ANCHOR_NOT_IN_SOURCE", "ANCHOR_EMPTY"))
# 🔴 **Three states, not two.** The framework now ships an empty `corpus_md/` so a new user can
#    see where extractions go -- **and every fresh project then reported INCOMPLETE on its first
#    run.** ⛔ A first run that cries wolf is what teaches people to ignore the output.
expect("an empty extraction folder is not 'could not check'", 0, "sensor_claim_ledger.py",
       "corpus_empty", "CORPUS_EMPTY", forbid=("CORPUS_MANIFEST_MISSING",))
# ⚠️ The paired half: extractions present but unprotected is still INCOMPLETE.
expect("extractions with no manifest are INCOMPLETE", 2, "sensor_claim_ledger.py",
       "corpus_unmanifested", "CORPUS_MANIFEST_MISSING")

# Self-certification
expect("self-certification is caught", 1, "sensor_self_certification.py", "selfcert_bad")
expect("gate-style requirements and honest disclosure do not false-alarm", 0,
       "sensor_self_certification.py", "selfcert_clean",
       forbid=("UNVERIFIABLE_SELF_CERT", "UNSUPPORTED_GLOBAL_APPRAISAL"))
# ⚠️ **Triggering case: a real cross-model audit report containing three terms banned
#    outright by `Audit_Protocol.md` §3 — and this sensor returned PASS.**
#    The cause was not APPRAISAL but SELF, which did not cover "this round / this project".
#    ⛔ SELF was widened for the **WARN branch only** — widening the FAIL branch would
#    false-alarm on honest disclosure, which is what the line added to the previous
#    fixture now guards.
expect("global appraisal warns", 0, "sensor_self_certification.py", "selfcert_appraisal",
       "UNSUPPORTED_GLOBAL_APPRAISAL", forbid=("UNVERIFIABLE_SELF_CERT",))

# Governance text
expect("duplicated long sentence across files warns", 0, "sensor_governance_text.py", "gov_dup", "DUPLICATE_RULE_TEXT")
# ⚠️ **A sentence that ends mid-line**: in `**...first.** Every audit...` the period is
#    followed by `*`, not whitespace. The old splitter knew only `。` and newlines, so the
#    English edition compared whole lines and **never saw this class of duplication**.
#    This fixture seeds that defect alone -- the kind `gov_dup` catches is absent here.
expect("duplicated sentence ending mid-line warns", 0, "sensor_governance_text.py",
       "gov_dup_midline", "DUPLICATE_RULE_TEXT")
expect("dangling section citation warns", 0, "sensor_governance_text.py", "gov_badref", "SECTION_REF_UNRESOLVED")
# 🔴 **Short form.** The long `` `<file>.md` §N `` form was the only one checked, while the
#    framework writes "constitution §N" in 58 places -- **three dangling citations lived there
#    until they were found by hand at release time.**
expect("dangling short-form citation warns", 0, "sensor_governance_text.py",
       "secref_alias_bad", "SECTION_REF_UNRESOLVED")
expect("resolvable short-form citation does not false-alarm", 0, "sensor_governance_text.py",
       "secref_alias_ok", forbid=("SECTION_REF_UNRESOLVED", "ALIAS_TARGET_MISSING"))
# ⚠️ **Scope, not form:** this citation lives in a `.py` header. `sensor_reference_integrity`
#    was built because those were never scanned -- ⛔ but it only covered *file* references.
expect("short-form citation in a .py header warns", 0, "sensor_governance_text.py",
       "secref_py", "SECTION_REF_UNRESOLVED")
# ⚠️ **Paired sample for the fence fix.** `HANDOFF.md` was reported as having two `## 3.`
#    headings; one was a line inside a fenced template. ⛔ Sample text is not a heading.
expect("a heading inside a fenced block is not counted", 0, "sensor_governance_text.py",
       "secref_fence", forbid=("SECTION_REF_UNRESOLVED",))
expect("clean governance text does not false-alarm", 0, "sensor_governance_text.py", "gov_clean",
       forbid=("DUPLICATE_RULE_TEXT", "SECTION_REF_UNRESOLVED", "STATE_IN_SPEC_DOC"))


# -- Scope and T0: needs a real git repo, so one is built in the system temp dir --
# ⚠️ **Why not a fixed fixture under selftest/:** this sensor reads `git status`, and a
#    nested `.git` inside the repo makes it refuse to report ("inside another repo") —
#    exactly what it is designed to refuse. **So the test environment must live outside
#    this repo.**
# ⚠️ Per `governance/WORKFLOW_CONSTITUTION.md` §7.1: every branch of a branching sensor needs a self-test. This section
#    exercises the "write_scopes is set" branch; the "not set" branch is covered by every
#    real run of `run_all_sensors.py`.
# ⚠️ **The base files must be committed first.** The first version did not commit, so
#    `governance/AGENTS.md` and `governance_config.json` counted as changes themselves and
#    **all three tests failed** — caught by the self-test, not by reading the code.
def scope_case(desc, changed_files, want_code, needle=None, forbid=(), scopes=None, deny=None):
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_scope_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance_config.json").write_text(json.dumps({
            "write_scopes": scopes if scopes is not None else {
                "governance": ["governance", "policy"], "_human": ["ledgers"]},
            "deny": deny if deny is not None else ["ledgers"]},
            ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
        for rel in changed_files:
            f = tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("changed\n", encoding="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("expected exit " + str(want_code) + ", got " + str(r.returncode))
        if needle and needle not in out:
            why.append("output lacks " + needle)
        if banned:
            why.append("⛔ false alarm: " + ", ".join(banned))
        if why:
            print("  ❌ " + desc + " (" + "; ".join(why) + ")"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


scope_case("writing into deny FAILs", ["ledgers/Claim_Ledger.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "policy"]})
# 🔴 **The paired sample for D1 (v1.4.1).**
#    ⚠️ **The old code folded `t0_docs` into `denied` unconditionally, so no configuration
#    could turn T0 protection off — while the comment in `framework_config.py` said
#    "a governance agent may maintain them".**
#    **⛔ Both of the following must hold; either one failing means the old behaviour is back.**
scope_case("with T0 in deny, editing a T0 FAILs",
           ["governance/AGENTS.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "policy"]},
           deny=["ledgers", "governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"])
scope_case("🔴 with T0 ⛔ not in deny, editing a T0 must ⛔ NOT fail (it is switchable)",
           ["governance/AGENTS.md"], 0,
           scopes={"governance": ["governance", "policy"]},
           deny=["ledgers"], forbid=("WRITE_TO_DENIED_PATH",))

# 🔴 **The paired sample for D2 (v1.4.1).**
#    ⚠️ **The old code skipped the whole block when `write_scopes` was empty, ⛔ `deny`
#    included — and `PROFILE_solo.md` tells a solo project to leave it empty. So `deny`
#    had never once been in effect in a solo project.**
#    ⛔ **The verdict is WARN plus names, ⛔ not FAIL**: the principal editing their own
#    ledger is normal (`R-19`), ⛔ and silence is not an option either (`R-22`).
scope_case("🔴 solo project edits a ledger: must be listed, ⛔ must not FAIL",
           ["ledgers/Claim_Ledger.md"], 0, "DENIED_PATH_TOUCHED_UNATTRIBUTED",
           scopes={}, forbid=("WRITE_TO_DENIED_PATH", "WRITE_OUT_OF_SCOPE"))
scope_case("solo project edits an ordinary file: ⛔ that WARN must not appear",
           ["policy/SOURCES.md"], 0, scopes={},
           forbid=("DENIED_PATH_TOUCHED_UNATTRIBUTED",))
scope_case("covered by _human: no false alarm, and the count is printed",
           ["ledgers/Claim_Ledger.md"], 0, "_human", forbid=("WRITE_TO_DENIED_PATH",))
scope_case("an in-scope change does not false-alarm", ["policy/SOURCES.md"], 0,
           forbid=("WRITE_TO_DENIED_PATH", "WRITE_OUT_OF_SCOPE"))


# -- Prompt self-containment: both profiles need a self-test (`governance/WORKFLOW_CONSTITUTION.md` §7.1) ------------
# ⚠️ **This sensor's interface is one file, not one root**, so expect() does not fit.
# 🔴 **The same fixture has different expectations under the two profiles — that is the
#    point of a branch test:** `generic` checks self-containment only; `deep-research` adds
#    the 8-item DR clause list.
#    **The old version ran ② on every prompt, so the framework's own decomposition template
#    FAILed forever.**
def prompt_case(desc, fixture, want_code, needle=None, forbid=(), profile=None):
    global ok, bad
    import subprocess
    f = FIX / "prompts" / (fixture + ".txt")
    if not f.exists():
        print("  ❌ " + desc + " (fixture missing: " + fixture + ")"); bad += 1; return
    cmd = [PY, str(HERE / "sensor_prompt_self_contained.py"), str(f)]
    if profile:
        cmd += ["--profile", profile]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    banned = [c for c in forbid if c in out]
    why = []
    if r.returncode != want_code:
        why.append("expected exit " + str(want_code) + ", got " + str(r.returncode))
    if needle and needle not in out:
        why.append("output lacks " + needle)
    if banned:
        why.append("⛔ false alarm: " + ", ".join(banned))
    if why:
        print("  ❌ " + desc + " (" + "; ".join(why) + ")"); bad += 1
    else:
        print("  ✅ " + desc); ok += 1


prompt_case("cross-prompt reference FAILs", "prompt_crossref", 1, "CROSS_PROMPT_REFERENCE")
prompt_case("unassembled block slot FAILs", "prompt_unassembled", 1, "PROMPT_NOT_ASSEMBLED")
prompt_case("a self-contained prompt does not false-alarm", "prompt_clean", 0,
            forbid=("CROSS_PROMPT_REFERENCE", "PROMPT_NOT_ASSEMBLED", "DR_CLAUSE_MISSING"))
# ⚠️ Regression: ⛔ quoting a prohibition is not breaking it. The old version read
#    '⛔ Do not write "see below"' as a cross-prompt reference.
prompt_case("quoted prohibition does not false-alarm, and the exemption is printed",
            "prompt_quoted_prohibit", 0, "exempted",
            forbid=("CROSS_PROMPT_REFERENCE",))
# ⚠️ Regression: a content slot is the user's input, ⛔ not a defect.
prompt_case("content slot does not false-alarm", "prompt_content_slot", 0,
            forbid=("CROSS_PROMPT_REFERENCE", "PROMPT_NOT_ASSEMBLED"))
# 🔴 Branch test: same fixture, PASS under generic and FAIL under deep-research.
prompt_case("generic does not run the DR clause list", "prompt_clean", 0,
            "not applicable is not a pass",
            forbid=("DR_CLAUSE_MISSING",))
prompt_case("deep-research runs the DR clause list", "prompt_clean", 1, "DR_CLAUSE_MISSING",
            profile="deep-research")


# -- Model attribution (decision 12: full rewrite) ------------------------------
# ⚠️ **The old version emitted three WARNs on a brand-new clean template**, because it
#    scanned the project root, whose .md files are framework templates that were never
#    supposed to carry an author field.
#    **It used a hard-coded whitelist to suppress alarms it created for itself — a whitelist
#    compensating for a wrong scan scope.**
expect("an artefact with no model field FAILs", 1, "sensor_model_attribution.py", "attrib_missing",
       "MODEL_ATTRIBUTION_MISSING")
expect("a family name alone FAILs", 1, "sensor_model_attribution.py", "attrib_vague",
       "MODEL_ATTRIBUTION_VAGUE")
expect("a platform name FAILs", 1, "sensor_model_attribution.py", "attrib_platform",
       "MODEL_ATTRIBUTION_VAGUE")
expect("a concrete model does not false-alarm", 0, "sensor_model_attribution.py", "attrib_clean",
       forbid=("MODEL_ATTRIBUTION_VAGUE", "MODEL_ATTRIBUTION_MISSING"))
# 🔴 The most important of this group: ⛔ "cannot read" is the **only correct output** per
#    MODEL_IDENTITY §3.6 rule 1. FAILing it would push the next model back to writing a
#    platform name, and §3.6 rule 2 says that is worse than a blank.
#    **The direction of degradation must be "I do not know", not "a vaguer name".**
expect("a correct 'cannot read' declaration is not a defect", 0, "sensor_model_attribution.py",
       "attrib_unreadable", "MODEL_UNREADABLE_DECLARED",
       forbid=("MODEL_ATTRIBUTION_VAGUE", "MODEL_ATTRIBUTION_MISSING"))


# -- Reference integrity (decision 14: new sensor) -------------------------------
# ⚠️ Four triggering cases, **all inside the framework itself**, one of them created while
#    rewriting another sensor by quoting the old whitelist's filenames as examples in a
#    comment — **do not instantiate a defect while describing it.**
expect("a reference to a missing file FAILs", 1, "sensor_reference_integrity.py", "ref_dangling",
       "DANGLING_FILE_REF")
# ⚠️ **Self-containment: this folder must work when copied out on its own.**
#    Measured: the figure once lived at the repository root and the README cited it as
#    `../docs/...` — **perfectly fine in the repository, broken once copied out.**
#    This class of dependency never errors in place.
expect("reference climbing out of the folder FAILs", 1, "sensor_reference_integrity.py",
       "ref_escapes", "REF_ESCAPES_EDITION")
expect("relative reference inside the folder does not false-alarm", 0,
       "sensor_reference_integrity.py", "ref_selfcontained",
       forbid=("REF_ESCAPES_EDITION", "DANGLING_FILE_REF"))
expect("a reference to an existing file does not false-alarm", 0, "sensor_reference_integrity.py", "ref_ok",
       forbid=("DANGLING_FILE_REF",))
# ⚠️ Regression: `<filename>.md` in a format description is a placeholder, ⛔ not a reference.
expect("a format placeholder does not false-alarm", 0, "sensor_reference_integrity.py", "ref_placeholder",
       forbid=("DANGLING_FILE_REF",))
# 🔴 Explicit exemption: ⛔ the criterion is a marker on the same line, not an exemption
#    list — **and it must be printed**.
expect("an explicitly not-shipped reference is exempted, and printed", 0, "sensor_reference_integrity.py",
       "ref_not_shipped", "REF_EXEMPTED_NOT_SHIPPED", forbid=("DANGLING_FILE_REF",))


# -- Coverage collapse (decision 20: three states, ⛔ not two) --------------------
# ⚠️ Triggering case (measured elsewhere): adversarial testing found **five sensors** printing
#    PASS whenever the comparison set became empty — **"nothing to compare" and "everything
#    matched" are identical on screen.**
# ⛔ But promoting every case to exit 2 is wrong: a new project's first run would be
#    INCOMPLETE, and constitution §4.1.1 says exit 2 means "stop and report" — a direct
#    contradiction of `SETUP.md`.
# 🔴 **The first version used two states (directory exists = collapse) and a live run hit it
#    immediately: the framework itself had an empty handoffs/.** → narrowed to three states.
expect("directory absent: warn only", 0, "sensor_self_certification.py", "collapse_absent",
       "SCAN_GLOB_MATCHES_NOTHING", forbid=("COVERAGE_COLLAPSE",))
expect("directory freshly created and empty: warn only", 0, "sensor_self_certification.py", "collapse_created",
       "SCAN_GLOB_MATCHES_NOTHING", forbid=("COVERAGE_COLLAPSE",))
expect("directory holds files but none match the glob: INCOMPLETE", 2, "sensor_self_certification.py",
       "collapse_empty", "COVERAGE_COLLAPSE")

# -- Clause-list synchronisation (decision 18) ---------------------------------
# ⚠️ **What each of the three does:** ① a one-character difference must FAIL;
#    ② **a different order must not false-alarm** -- ⛔ without ②, the next person will
#    tighten the criterion to "identical order", which FAILs on both editions as they stand;
#    ③ a missing home means **cannot check**, ⛔ not pass.
expect("a one-character difference in the list FAILs", 1, "sensor_clause_sync.py",
       "sync_drift", "SYNC_LIST_DRIFT")
expect("same set in a different order does not false-alarm", 0, "sensor_clause_sync.py",
       "sync_ok", forbid=("SYNC_LIST_DRIFT", "SYNC_HOME_MISSING", "SYNC_NO_COPY"))
expect("missing home is INCOMPLETE", 2, "sensor_clause_sync.py", "sync_home_missing",
       "SYNC_HOME_MISSING")



# -- A crash must be INCOMPLETE, ⛔ never FAIL (`R-22`, constitution §7.4) -------
# 🔴 **Measured case:** on Traditional-Chinese Windows two sensors died of
#    `UnicodeEncodeError`. **An uncaught Python exception always exits 1, and 1 means
#    "found a defect"** — so the summary printed "the whole suite FAILED" while what
#    actually happened is that they never finished running.
# ⛔ **This is tested with a fake sensor that always crashes, ⛔ not with a real one** —
#    **a real sensor gets fixed one day, and what this test checks is the runner's behaviour.**
def crash_case():
    import os as _os
    env = dict(_os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, str(HERE / "_selftest_crasher.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    crashed = r.returncode != 0 and "Traceback (most recent call last)" in (r.stderr or "")
    global ok, bad
    if crashed:
        print("  ✅ a crashed sensor is judged INCOMPLETE, not FAIL"); ok += 1
    else:
        print("  ❌ a crashed sensor must be judged INCOMPLETE"
              f" (exit {r.returncode}, traceback on stderr: "
              f"{'yes' if 'Traceback' in (r.stderr or '') else 'no'})"); bad += 1


crash_case()


# -- The upgrade tool must never touch a folder it does not recognise -----------
# 🔴 **The guarantee people actually rely on is not the "your data" list.**
#    ⚠️ Users create folders of their own — notes, figures, submitted drafts.
#    ⛔ None of those can be named in a list written in advance, and the tool must still
#    leave them alone. **The mechanism that does that is the replaceable list, not the
#    protected one**: a target that is not a framework item is refused outright.
# **This test exists so the guarantee is a measured fact rather than a sentence in a guide.**
def upgrade_case():
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_upg_"))
    try:
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance" / "AGENTS.md").write_text("# A\n", encoding="utf-8")
        shutil.copy(HERE / "checkpoint.py", root / "scripts_stub.py")  # presence only
        (root / "scripts" / "harness").mkdir(parents=True)
        shutil.copy(HERE / "checkpoint.py", root / "scripts" / "harness" / "checkpoint.py")
        # a folder the user invented; the tool has never heard of it
        mine = root / "my notes"
        mine.mkdir()
        (mine / "keep.md").write_text("do not lose me\n", encoding="utf-8")
        before = (mine / "keep.md").read_text(encoding="utf-8")
        # an upgrade source that happens to contain a folder of the same name
        (tmp / "project" / "_upgrade" / "my notes").mkdir(parents=True)
        (tmp / "project" / "_upgrade" / "my notes" / "keep.md").write_text(
            "REPLACED\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "my notes",
                            "--root", str(root)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env)
        after = (mine / "keep.md").read_text(encoding="utf-8")
        refused = r.returncode == 1
        intact = after == before
        if refused and intact:
            print("  ✅ a folder the tool does not recognise is refused and left untouched")
            ok += 1
        else:
            print("  ❌ an unrecognised folder must be refused and left untouched "
                  f"(exit {r.returncode}, content {'unchanged' if intact else 'OVERWRITTEN'})")
            bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



# ── Paired samples for D3 / D6 (v1.4.1) ────────────────────────
# 🔴 **`my/MY_RULES.md` is a copy of the framework's rules, ⛔ and a copy cannot be unwatched.**
#    ⚠️ **"One fact, two copies, only one updated" is failure axis two itself.**
def my_rules_case(desc, rules, my_rules, want_code, needle=None, forbid=()):
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_myrules_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance/RULES.md").write_text(rules, encoding="utf-8")
        if my_rules is not None:
            (tmp / "my/MY_RULES.md").write_text(my_rules, encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_my_rules.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("expected exit " + str(want_code) + ", got " + str(r.returncode))
        if needle and needle not in out:
            why.append("output lacks " + needle)
        if banned:
            why.append("⛔ false alarm: " + ", ".join(banned))
        if why:
            print("  ❌ " + desc + " (" + "; ".join(why) + ")"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


_FW = "## A\n\n**R-05** alpha.\n**R-06** beta.\n"
_HDR = "# My rules\n\n## 1. Framework rules\n\n"
_TAIL = "\n<!-- FRAMEWORK_RULES_END -->\n\n---\n\n## 2. This project's own rules\n"

my_rules_case("a framework rule missing from MY_RULES FAILs", _FW,
              _HDR + "**R-05** alpha.\n" + _TAIL, 1, "RULE_MISSING_IN_MY")
my_rules_case("identical copies ⛔ must not false-alarm", _FW,
              _HDR + "**R-05** alpha.\n**R-06** beta.\n" + _TAIL, 0,
              forbid=("RULE_MISSING_IN_MY", "RULE_TEXT_DRIFT", "OVERRIDE_WITHOUT_REASON"))
my_rules_case("edited text with no override marker FAILs", _FW,
              _HDR + "**R-05** alphaalpha.\n**R-06** beta.\n" + _TAIL, 1, "RULE_TEXT_DRIFT")
# 🔴 **This one is this sensor's own regression test.**
#    ⚠️ **The first criterion was "there is text after the marker", so
#    `**R-05** [project override] alpha.` passed — ⛔ because that text is the clause itself.**
my_rules_case("🔴 marker on the rule's own line FAILs (⛔ never counts as a reason)", _FW,
              _HDR + "**R-05** [project override] alphaalpha.\n**R-06** beta.\n" + _TAIL, 1,
              "RULE_TEXT_DRIFT")
my_rules_case("marker on its own line with a reason ⛔ must not FAIL", _FW,
              _HDR + "**R-05** alphaalpha.\n[project override] this project needs it tighter.\n"
              + "**R-06** beta.\n" + _TAIL, 0,
              forbid=("RULE_TEXT_DRIFT", "OVERRIDE_WITHOUT_REASON"))
my_rules_case("a missing MY_RULES is INCOMPLETE (⛔ not a PASS)", _FW, None, 2,
              "MY_RULES_MISSING")


# ── D6: an unrecognised config key must ⛔ never be absorbed silently (v1.4.1) ──
# ⚠️ **The old line was `cfg.update(data)`: misspell `deny` as `denny` and ⛔ nothing happens,
#    while the user believes the setting took effect. ⛔ "Silent filtering" at the front door.**
def config_key_case(desc, cfg_obj, want_ok, needle=None):
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_cfgkey_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance_config.json").write_text(
            json.dumps(cfg_obj, ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        # ⚠️ **The criterion is "did it report an unknown key", ⛔ not the exit code.**
        #    🔴 **Measured (this test caught it itself): the fixture has no git repo, so the
        #    two valid-key cases exit 2 (`SCOPE_UNCHECKABLE`) — ⛔ which is correct behaviour,
        #    and using the exit code as the criterion would call it a failure.**
        flag = "does not recognise" in out
        good = (not flag) if want_ok else flag
        if needle and needle not in out:
            good = False
        if good:
            print("  ✅ " + desc); ok += 1
        else:
            print("  ❌ " + desc + " (exit " + str(r.returncode) + ")"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


config_key_case("🔴 a misspelled key errors out and names the closest valid key",
                {"denny": ["ledgers"]}, False, "deny")
config_key_case("a valid key ⛔ must not error", {"deny": ["ledgers"]}, True)
config_key_case("an underscore key is for people and ⛔ must not error",
                {"_note": "for people", "deny": ["ledgers"]}, True)


# ── 🔴 git reports success but produces no output (v1.4.1, measured on the principal's machine) ──
# **`subprocess.run(..., capture_output=True, text=True)` returned exit 0 with `stdout` set to
#  `None`, so `top.stdout.strip()` raised AttributeError and the whole sensor crashed.**
# ⚠️ **The defect had been there since v1.0.0 and surfaced only in v1.4.1** —
#    🔴 **the old code skipped the whole block when `write_scopes` was empty, and a solo
#    project always leaves it empty: ⛔ that code had never run on a real user's machine.**
# ⛔ **This test does ⛔ not reproduce "stdout is None" (that is platform-dependent);
#    it reproduces the same branch: git said success and handed us nothing.**
def git_blind_case():
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_gitblind_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        shim = tmp / "bin"
        shim.mkdir()
        if sys.platform == "win32":
            (shim / "git.bat").write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        else:
            g = shim / "git"
            g.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            g.chmod(0o755)
        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   PATH=str(shim) + os.pathsep + os.environ.get("PATH", ""))
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        crashed = "Traceback" in out
        # 🔴 **"no output" must ⛔ never be read as "the project sits inside another
        #    repository"** — ⚠️ a diagnosis that reads plausibly and is wrong
        #    (`pathlib.Path("")` is the current directory).
        wrong_dx = "inside another repository" in out
        good = (not crashed) and (not wrong_dx) and r.returncode == 2 \
            and "SCOPE_UNCHECKABLE" in out
        if good:
            print("  ✅ 🔴 git says success with no output: INCOMPLETE, ⛔ no crash, ⛔ no misdiagnosis"); ok += 1
        else:
            why = []
            if crashed:
                why.append("⛔ crashed")
            if wrong_dx:
                why.append("⛔ misdiagnosed as 'inside another repository'")
            if r.returncode != 2:
                why.append("expected exit 2, got " + str(r.returncode))
            print("  ❌ git says success with no output (" + "; ".join(why) + ")"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


git_blind_case()


# ── 🔴 The project is a subdirectory of a repo (v1.4.1) ────────
# **This framework's own repository has exactly that shape: each edition is a subdirectory.**
# ⚠️ **The old code always refused to report and went INCOMPLETE — ⛔ a light always on (`R-19`).**
# 🔴 **Both must hold: changes inside the subtree are seen, ⛔ changes outside are not.**
#    **⛔ Doing only the first is "judging the wrong repo", which is what the old code feared.**
def subrepo_case():
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_subrepo_"))
    try:
        proj = tmp / "edition_en"
        (proj / "governance").mkdir(parents=True, exist_ok=True)
        (proj / "policy").mkdir(parents=True, exist_ok=True)
        (proj / "ledgers").mkdir(parents=True, exist_ok=True)
        (tmp / "something_else").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "policy/SOURCES.md").write_text("x\n", encoding="utf-8")
        (proj / "ledgers/Claim_Ledger.md").write_text("x\n", encoding="utf-8")
        (tmp / "something_else/note.md").write_text("x\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps(
            {"write_scopes": {"governance": ["governance", "policy"]},
             "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
        # one denied change inside the subtree, one change outside it
        (proj / "ledgers/Claim_Ledger.md").write_text("changed\n", encoding="utf-8")
        (tmp / "something_else/note.md").write_text("changed\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(proj)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        saw_inside = "WRITE_TO_DENIED_PATH" in out and "ledgers/Claim_Ledger.md" in out
        saw_outside = "something_else" in out
        refused = "SCOPE_UNCHECKABLE" in out
        if saw_inside and not saw_outside and not refused:
            print("  ✅ 🔴 project inside a repo subdirectory: subtree seen, ⛔ outside not seen"); ok += 1
        else:
            why = []
            if refused:
                why.append("⛔ still refused to report")
            if not saw_inside:
                why.append("⛔ the denied change inside the subtree was missed")
            if saw_outside:
                why.append("🔴 ⛔ reported a file outside the subtree")
            print("  ❌ project inside a repo subdirectory (" + "; ".join(why) + ")"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


subrepo_case()


# ── 🔴 `subprocess.run` decoding must be stated, ⛔ never left to the locale (v1.4.1) ──
#
# **Measured (Traditional-Chinese Windows, Python 3.14.2): with `text=True` and no
#  `encoding`, Python decoded git's UTF-8 output as `cp950` → `UnicodeDecodeError`.**
# 🔴 **And it blew up inside `subprocess`'s reader thread: the thread died, the exception
#    never propagated, and `communicate()` returned `None` — so the caller saw
#    "exit 0 and no output".**
# ⛔ **"Succeeded but produced nothing" and "succeeded and genuinely had nothing"
#    look identical there.**
#
# ⚠️ **This test is a **static** check: it reads the harness's source, ⛔ it does not run it.**
#    🔴 **Why: the defect only occurs on a machine with a non-UTF-8 locale, ⛔ and a
#    self-test has to reach the same conclusion on every machine.**
#    **⛔ A criterion that cannot fire on my machine is not a criterion.**
def subprocess_encoding_case():
    global ok, bad
    import ast as _ast
    offenders = []
    for f in sorted(HERE.glob("*.py")):
        if f.name.startswith("_selftest"):
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ could not parse ({e})")
            continue
        for node in _ast.walk(tree):
            if not isinstance(node, _ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, _ast.Attribute) and fn.attr == "run"
                    and isinstance(fn.value, _ast.Name) and fn.value.id == "subprocess"):
                continue
            kw = {k.arg for k in node.keywords if k.arg}
            decodes = "text" in kw or "universal_newlines" in kw
            if decodes and "encoding" not in kw:
                offenders.append(f"{f.name}:{node.lineno}")
    if not offenders:
        # ⚠️ **Print the denominator** (`R-35`): "0" is the result of taking stock,
        #    ⛔ not the absence of stocktaking.
        n = len([f for f in HERE.glob("*.py")])
        print(f"  ✅ 🔴 every subprocess decode names its encoding ({n} files scanned, 0 exceptions)"); ok += 1
    else:
        print("  ❌ subprocess.run calls that would decode with the locale: " + ", ".join(offenders)); bad += 1


subprocess_encoding_case()


# ── 🔴 Your own file index (v1.4.1) ────────────────────────────
# **Measured case: a project adopted the framework and stopped maintaining its own file index.**
# 🔴 **The key property: the criterion is "everything the framework does ⛔ not own",
#    ⛔ never a list of what to include — so a folder the user invents must appear in the
#    index automatically (`R-21`).**
def my_index_case(desc, build, want_code, needle=None, forbid=(), regen=True,
                  in_index=None):
    """⚠️ `needle` checks **the sensor's output**; `in_index` checks **the generated index**.

    🔴 **They are ⛔ not the same thing, and the first version treated them as one:**
    **the sensor prints counts, ⛔ never the file list — so "is this file in the index"
    could never be answered by `needle`.**
    ⚠️ **The self-test caught it, ⛔ and what it caught was my criterion aimed at the
    wrong object.**
    """
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_myindex_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "PROJECT.md").write_text("# p\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        build(tmp)
        r = subprocess.run([PY, str(HERE / "sensor_my_index.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("expected exit " + str(want_code) + ", got " + str(r.returncode))
        if needle and needle not in out:
            why.append("output lacks " + needle)
        if in_index is not None:
            idxf = tmp / "my/MY_INDEX.md"
            body = idxf.read_text(encoding="utf-8") if idxf.is_file() else ""
            if in_index not in body:
                why.append("index file lacks " + in_index)
        if banned:
            why.append("⛔ false alarm: " + ", ".join(banned))
        if why:
            print("  ❌ " + desc + " (" + "; ".join(why) + ")"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ⚠️ **`tool_my_index.py` derives the project root from its own location, ⛔ so a fixture
#    cannot rely on cwd. Copy the harness files the tool needs into the fixture instead.**
def _gen(tmp):
    import subprocess
    (tmp / "scripts" / "harness").mkdir(parents=True, exist_ok=True)
    for f in ("tool_my_index.py", "framework_config.py", "_common.py", "upgrade.py"):
        (tmp / "scripts" / "harness" / f).write_bytes((HERE / f).read_bytes())
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run([PY, str(tmp / "scripts/harness/tool_my_index.py")],
                   capture_output=True, text=True,
                   encoding="utf-8", errors="replace", env=env)


my_index_case("a never-generated index is INCOMPLETE (⛔ not a PASS)",
              lambda t: None, 2, "MY_INDEX_MISSING")
my_index_case("a freshly generated index ⛔ must not false-alarm",
              _gen, 0, forbid=("MY_INDEX_STALE", "INDEX_NOTE_DANGLING", "MY_INDEX_MISSING"))
my_index_case("🔴 a folder the user invented must appear in the index (⛔ not a whitelist)",
              lambda t: (_gen(t), (t / "deepresearch").mkdir(),
                         (t / "deepresearch/draft.md").write_text("x", encoding="utf-8"),
                         _gen(t), None)[-1], 0, in_index="deepresearch/draft.md",
              forbid=("MY_INDEX_STALE",))
my_index_case("a file added after generation: must report stale",
              lambda t: (_gen(t), (t / "new_thing.md").write_text("x", encoding="utf-8"),
                         None)[-1], 1, "MY_INDEX_STALE")
my_index_case("a description pointing at a missing file: FAIL",
              lambda t: ((t / "my/MY_INDEX_notes.json").write_text(
                             '{"no_such_file.md": "x"}', encoding="utf-8"),
                         _gen(t), None)[-1], 1, "INDEX_NOTE_DANGLING")
my_index_case("a broken notes file: INCOMPLETE (⛔ never 'there are no descriptions')",
              lambda t: (_gen(t),
                         (t / "my/MY_INDEX_notes.json").write_text("{broken", encoding="utf-8"),
                         None)[-1], 2, "INDEX_NOTES_UNREADABLE")


# ── 🔴 The index order must be identical across platforms (v1.4.2) ──
# **Measured: `sorted(root.rglob("*"))` sorts `Path` objects, and `WindowsPath` casefolds first.**
# **⇒ `PROJECT.md` sorts before `corpus/` on Linux and after it on Windows.**
# 🔴 **The index shipped with v1.4.1 was generated on Linux, so it reported "stale" on the
#    principal's Windows machine on the first run — ⛔ reporting not "the index is stale"
#    but "your operating system is not the one that generated it".**
#
# ⚠️ **⛔ Honest about this test's reach: it only lights up on a platform whose filenames are
#    case-insensitive (Windows, macOS by default). ⛔ On Linux the old and new code agree,
#    so it cannot fire.**
# **⚠️ It is kept because the release procedure runs the self-test on Windows as step one.**
def index_order_case():
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_idxorder_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        (tmp / "apple").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        # 🔴 `Z` (0x5A) < `a` (0x61): by string order Zed.md comes first;
        #    ⛔ after casefolding, apple/ jumps ahead of it.
        (tmp / "Zed.md").write_text("x", encoding="utf-8")
        (tmp / "apple/x.md").write_text("x", encoding="utf-8")
        (tmp / "scripts" / "harness").mkdir(parents=True, exist_ok=True)
        for f in ("tool_my_index.py", "framework_config.py", "_common.py", "upgrade.py"):
            (tmp / "scripts" / "harness" / f).write_bytes((HERE / f).read_bytes())
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        subprocess.run([PY, str(tmp / "scripts/harness/tool_my_index.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
        body = (tmp / "my/MY_INDEX.md").read_text(encoding="utf-8")
        if "Zed.md" not in body or "apple/x.md" not in body:
            print("  ❌ index order: not both sample files reached the index"); bad += 1
        elif body.index("Zed.md") < body.index("apple/x.md"):
            print("  ✅ 🔴 the index is sorted by string (identical across platforms)"); ok += 1
        else:
            print("  ❌ the index is sorted by platform — ⛔ one project, two machines, two indexes"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


index_order_case()

upgrade_case()

print("\n" + "=" * 48)
print(f"  passed {ok} | failed {bad}")
if tolerated:
    total = sum(tolerated.values())
    print(f"  ⚠️ {total} WARN(s) tolerated this run (**tolerated is not absent**):")
    for code, n in sorted(tolerated.items()):
        print(f"      {code} ×{n}")
    print("      Reason: a fixture directory does not contain every glob, so these are")
    print("      infrastructure noise rather than sensor false alarms.")
    print("      ⛔ If a code here relates to the tested sensor's own job, it IS a false alarm.")
print("  Result: " + ("all self-tests passed" if not bad
                       else "self-test FAILED — ⛔ sensor changes must not be committed"))
sys.exit(1 if bad else 0)
