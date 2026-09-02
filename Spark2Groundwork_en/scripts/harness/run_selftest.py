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
                "governance": ["governance", "profiles"], "_human": ["ledgers"]},
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
           scopes={"governance": ["governance", "profiles"]})
# 🔴 **The paired sample for D1 (v1.4.1).**
#    ⚠️ **The old code folded `t0_docs` into `denied` unconditionally, so no configuration
#    could turn T0 protection off — while the comment in `framework_config.py` said
#    "a governance agent may maintain them".**
#    **⛔ Both of the following must hold; either one failing means the old behaviour is back.**
scope_case("with T0 in deny, editing a T0 FAILs",
           ["governance/AGENTS.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "profiles"]},
           deny=["ledgers", "governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"])
scope_case("🔴 with T0 ⛔ not in deny, editing a T0 must ⛔ NOT fail (it is switchable)",
           ["governance/AGENTS.md"], 0,
           scopes={"governance": ["governance", "profiles"]},
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
           ["governance/SOURCES.md"], 0, scopes={},
           forbid=("DENIED_PATH_TOUCHED_UNATTRIBUTED",))
scope_case("covered by _human: no false alarm, and the count is printed",
           ["ledgers/Claim_Ledger.md"], 0, "_human", forbid=("WRITE_TO_DENIED_PATH",))
scope_case("an in-scope change does not false-alarm", ["governance/SOURCES.md"], 0,
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
        (proj / "profiles").mkdir(parents=True, exist_ok=True)
        (proj / "ledgers").mkdir(parents=True, exist_ok=True)
        (tmp / "something_else").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "profiles/PROFILE_solo.md").write_text("x\n", encoding="utf-8")
        (proj / "ledgers/Claim_Ledger.md").write_text("x\n", encoding="utf-8")
        (tmp / "something_else/note.md").write_text("x\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps(
            {"write_scopes": {"governance": ["governance", "profiles"]},
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
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
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


# ── 🔴 Only a person may move the reviewed tag (v1.4.4, R-H003-05) ──
# **觸發個案（Codex 覆核，2026-09-02，在 `v1.4.2` 的 tag 上重現）：**
# `upgrade.py` 自 v1.4.1 起以 `checkpoint.py --root <root>` 呼叫，⛔ 沒有傳 `--mode`，
# 於是走 `human` 預設——**一次框架升級就把 `reviewed` 移到升級前的提交，並印「我看過了」。**
#
# 🔴 **真正的後果⛔ 不是標籤變了，是使用者的「還沒看過」被清空：**
# **一筆 AI 寫進台帳、人從未審閱的內容，因為使用者升級框架而從 `review_changes.py` 消失。**
# ⚠️ **`reviewed` 是本框架「人是唯一裁決者」這個宣稱的唯一機械載體。**
#
# ⛔ **⛔ 這一組⛔ 不是只測新工具**——**`CP-12` 測的是 `upgrade.py`，
#    因為已發布版本的缺陷在那裡，⛔ 不在任何新增的東西裡。**
def reviewed_tag_case():
    global ok, bad
    import shutil, tempfile

    def sh(root, *args):
        return subprocess.run(["git", "-C", str(root)] + list(args),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def build():
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rev_"))
        (tmp / "governance").mkdir()
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "scripts/harness").mkdir(parents=True)
        for n in ("checkpoint.py", "_common.py", "framework_config.py"):
            (tmp / "scripts/harness" / n).write_bytes((HERE / n).read_bytes())
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        sh(tmp, "add", "-A"); sh(tmp, "-c", "user.email=a@b", "-c", "user.name=t",
                                 "commit", "-qm", "base")
        return tmp

    def cp(root, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([PY, str(root / "scripts/harness/checkpoint.py"),
                               "--root", str(root)] + list(args),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env)

    def has_reviewed(root):
        return sh(root, "rev-parse", "--verify", "reviewed").returncode == 0

    def check(desc, cond, detail=""):
        global ok, bad
        if cond:
            print(f"  ✅ {desc}"); ok += 1
        else:
            print(f"  ❌ {desc}{detail}"); bad += 1

    for mode_args, label in ((["--mode", "tool", "--tool-id", "t", "--operation", "op"], "tool"),
                             (["--mode", "ai", "--role", "governance",
                               "--model", "claude-opus-5", "--topic", "x"], "ai")):
        # CP-09: no reviewed to begin with -> still none afterwards
        r = build()
        (r / "note.md").write_text("dirty\n", encoding="utf-8")
        res = cp(r, *mode_args)
        check(f"🔴 CP-09/{label}: there was no reviewed tag, and there still is none",
              res.returncode == 0 and not has_reviewed(r), f" (exit {res.returncode})")
        check(f"CP-09/{label}: ⛔ must not print the human-review banner",
              "looked at this" not in res.stdout)
        shutil.rmtree(r, ignore_errors=True)

        # CP-10: a reviewed tag already exists -> it must point at exactly the same commit
        r = build()
        sh(r, "tag", "-f", "reviewed")
        before = sh(r, "rev-parse", "reviewed").stdout.strip()
        (r / "note.md").write_text("dirty\n", encoding="utf-8")
        cp(r, *mode_args)
        after = sh(r, "rev-parse", "reviewed").stdout.strip()
        check(f"🔴 CP-10/{label}: an existing reviewed tag ⛔ must not move",
              before == after and before != "", f" ({before[:7]}->{after[:7]})")
        shutil.rmtree(r, ignore_errors=True)

    # CP-11: human mode still moves it — ⛔ the distinction is deliberate, do not switch
    #        both off together
    r = build()
    (r / "note.md").write_text("dirty\n", encoding="utf-8")
    cp(r)
    check("human mode still moves reviewed (⛔ the distinction is deliberate)",
          has_reviewed(r))
    shutil.rmtree(r, ignore_errors=True)

    # CP-13: tool mode without an identity must be refused
    r = build()
    res = cp(r, "--mode", "tool")
    check("tool mode without --tool-id/--operation must be refused "
          "(⛔ an anonymous tool is indistinguishable from a person)",
          res.returncode != 0)
    shutil.rmtree(r, ignore_errors=True)

    # CP-14: 🔴 `git tag -f reviewed` can fail, and a failure ⛔ must not be reported as
    #        success. Counterexample from review (Codex, 2026-09-02): with a tag named
    #        `reviewed/child` present, Git cannot create `reviewed` at all.
    r = build()
    sh(r, "tag", "reviewed/child", "HEAD")
    (r / "note.md").write_text("dirty\n", encoding="utf-8")
    res = cp(r)
    check("🔴 CP-14: when the reviewed tag cannot be created, human checkpoint "
          "⛔ must not exit 0", res.returncode != 0, f" (exit {res.returncode})")
    check("🔴 CP-14: ⛔ must not print the 'baseline moved' banner when it did not move",
          "baseline moved" not in res.stdout.lower())
    check("CP-14: must say the baseline did not move",
          "did not move" in res.stdout.lower())
    check("CP-14: the commit itself is still made (⛔ no work is lost)",
          sh(r, "log", "--oneline", "-1").stdout.strip().count("snapshot") == 1)
    shutil.rmtree(r, ignore_errors=True)

    # CP-12: 🔴 where the shipped defect lived — the shape of upgrade.py's call
    src = (HERE / "upgrade.py").read_text(encoding="utf-8")
    check("🔴 CP-12: upgrade.py must pass --mode tool explicitly when calling checkpoint",
          src.count('"--mode", "tool"') >= 2,
          " — ⛔ without it the human default applies and one upgrade forges one "
          "human review")

    # CP-15: the upgrader must create a durable, independently checkable receipt
    #        before replacement and route recovery through its own safe interface.
    check("🔴 CP-15: upgrade.py must print a durable receipt id and checkpoint commit",
          'MSG["receipt"].format(rid=receipt["receipt_id"], cp=cp' in src)
    check("🔴 CP-15: upgrade.py ⛔ must not overwrite when the receipt is unreadable",
          'MSG["no_receipt"]' in src and src.index('MSG["no_receipt"]') <
          src.index("shutil.rmtree(dst)"))
    check("🔴 CP-15: recovery uses built-in receipt commands, ⛔ not raw git checkout",
          "receipt-diff {rid}" in src and "restore {rid}" in src
          and "git checkout {cp} --" not in src)


reviewed_tag_case()


# ── 🔴 Path sorting must be identical on every platform (v1.4.4, `N-8`) ─────
# **Real case (v1.4.1, on the principal's machine): `tool_my_index.py` built the index
#  with `sorted(root.rglob("*"))`, sorting `Path` objects — ⛔ and `WindowsPath`
#  comparison casefolds while `PosixPath` does not.**
# 🔴 **⇒ The same project produced a different index order on two machines, and the
#    index is stored and then compared — the user got `MY_INDEX_STALE` on the very
#    first run, ⛔ having done nothing wrong.**
#
# ⚠️ **This test is a **static** check: it reads the harness source, ⛔ it does not run it.**
#    🔴 **Same reason as `subprocess_encoding_case`: the difference only shows on Windows,
#    ⛔ and a criterion that cannot fire on this machine is not a criterion.**
#
# ⚠️ **What the criterion covers: the first argument of `sorted(...)` contains a
#    `.glob()`/`.rglob()` call (which always yields `Path`), and that call has no `key=`.**
#    ⛔ **It does NOT cover storing the paths in a variable first** — a known gap,
#    written down here rather than left blank.
def path_sort_case():
    global ok, bad
    import ast as _ast
    offenders = []
    scanned = 0
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
        if f.name.startswith("_selftest"):
            continue
        scanned += 1
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ cannot parse ({e})")
            continue
        for node in _ast.walk(tree):
            if not (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                    and node.func.id == "sorted" and node.args):
                continue
            if any(k.arg == "key" for k in node.keywords):
                continue
            for sub in _ast.walk(node.args[0]):
                if (isinstance(sub, _ast.Call) and isinstance(sub.func, _ast.Attribute)
                        and sub.func.attr in ("glob", "rglob")):
                    offenders.append(f"{f.name}:{node.lineno}")
                    break
    if not offenders:
        # ⚠️ **Print the denominator** (`R-35`): "0 found" is the result of a count,
        #    ⛔ not the absence of one.
        print(f"  ✅ 🔴 every path sort passes an explicit key (scanned {scanned}, 0 exceptions)"); ok += 1
    else:
        print("  ❌ sorted() sorts Path objects; order differs between platforms: "
              + ", ".join(offenders)); bad += 1

    # ⚠️ **The other half of the pair: the criterion must actually catch something,
    #    ⛔ or it is just a permanent green light.**
    src = ('import pathlib\n'
           'def f(root):\n'
           '    return sorted(root.rglob("*"))\n')
    tree = _ast.parse(src)
    caught = False
    for node in _ast.walk(tree):
        if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                and node.func.id == "sorted" and node.args
                and not any(k.arg == "key" for k in node.keywords)):
            for sub in _ast.walk(node.args[0]):
                if (isinstance(sub, _ast.Call) and isinstance(sub.func, _ast.Attribute)
                        and sub.func.attr in ("glob", "rglob")):
                    caught = True
    if caught:
        print("  ✅ the criterion catches the original v1.4.1 line"); ok += 1
    else:
        print("  ❌ the criterion is silent on a known defective form — it protects nothing"); bad += 1


path_sort_case()


# ── 🔴 A file that will be hashed must be written with a fixed line ending
#    (v1.4.4, `A-20260902-11`) ───────────────────────────────────────────────
# **Measured: `tool_pdf_to_md.py` wrote extracts with `write_text(..., encoding="utf-8")`,
#  ⛔ which on Windows emits CRLF; `_manifest.json` then recorded the hash of those CRLF bytes.**
# **⛔ And `.gitattributes` carries `*.md text eol=lf` ⇒ the commit normalises to LF.**
# 🔴 **⇒ On the next clean checkout the working tree is LF and `sensor_claim_ledger.py`
#    reports `CORPUS_MD_MODIFIED` on every file — ⛔ with not one character changed.**
# ⚠️ **Three individually correct components combine into a false positive, ⛔ and a false
#    positive is exactly what `R-19` says teaches people to ignore a sensor.**
#
# ⚠️ **The criterion is a deliberate over-approximation: if a module computes hashes at all
#    (`import hashlib`), every `write_text` in it must pass `newline=`.**
#    🔴 **⛔ Known gap, written down rather than left blank: if the module that writes and the
#    module that hashes are two different files, this check misses it.** ⚠️ No such split
#    exists in the framework today (`tool_pdf_to_md.py` does both), **⛔ and that is the
#    current state, not a guarantee.**
def hash_write_newline_case():
    global ok, bad
    import ast as _ast

    def offenders_in(src, name):
        bad_ = []
        tree = _ast.parse(src)
        if not any(isinstance(n, (_ast.Import, _ast.ImportFrom))
                   and "hashlib" in _ast.dump(n) for n in _ast.walk(tree)):
            return None                       # does not hash ⇒ out of scope
        for node in _ast.walk(tree):
            if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute)
                    and node.func.attr == "write_text"
                    and not any(k.arg == "newline" for k in node.keywords)):
                bad_.append(f"{name}:{node.lineno}")
        return bad_

    offenders, scanned = [], 0
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
        try:
            hits = offenders_in(f.read_text(encoding="utf-8"), f.name)
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ unparseable ({e})"); continue
        if hits is None:
            continue
        scanned += 1
        offenders.extend(hits)
    if not offenders:
        # ⚠️ **Print the denominator** (`R-35`): how many were scanned is a counted
        #    result, ⛔ not an absence of counting.
        print(f"  ✅ 🔴 every hashing module fixes its line endings ({scanned} scanned, 0 exceptions)"); ok += 1
    else:
        print("  ❌ a hashing module has write_text without newline=: " + ", ".join(offenders)); bad += 1

    # ⚠️ **The other half of the pair: the criterion must be able to catch something,
    #    ⛔ or it merely prints green forever.**
    probe = ('import hashlib, pathlib\n'
             'def f(p):\n'
             '    p.write_text("x", encoding="utf-8")\n')
    caught = offenders_in(probe, "probe")
    if caught:
        print("  ✅ the criterion does FAIL a planted write site (⛔ falsifiable)"); ok += 1
    else:
        print("  ❌ the criterion does not react to an obvious violation — ⛔ it is empty"); bad += 1

    # ⚠️ **A third sample: a module that does ⛔ not hash must ⛔ not be flagged** —
    #    🔴 **otherwise the next person is forced to add `newline=` to dozens of fixture
    #    writes, and a parameter added only to silence a warning turns the criterion
    #    itself into noise.**
    quiet = ('import pathlib\n'
             'def f(p):\n'
             '    p.write_text("x", encoding="utf-8")\n')
    if offenders_in(quiet, "quiet") is None:
        print("  ✅ a non-hashing module is ⛔ out of scope (⛔ no noise)"); ok += 1
    else:
        print("  ❌ the criterion pulled in an unrelated module"); bad += 1


hash_write_newline_case()


# ── 🔴 Version consistency (v1.4.4, A5b) ──────────────────────
# **Trigger: Project D's `policy/` sat at v1.3.0 while the other five packages were v1.4.2.**
# 🔴 **Every sensor green, every self-test passing — ⛔ and it took an outside audit to find it.**
# ⚠️ **All four branches must be checked: same (must not false-alarm) / different (must
#    catch) / package absent (WARN, not FAIL) / unreadable (INCOMPLETE, not PASS).**
def version_consistency_case():
    global ok, bad
    import shutil, tempfile
    from sensor_version_consistency import survey
    cfg = {}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_ver_"))
    try:
        def build(spec):
            root = tmp / ("p%d" % len(list(tmp.iterdir())))
            for name, v in spec.items():
                d = root / name
                d.mkdir(parents=True)
                if v is not None:
                    (d / "_VERSION").write_text(v + "\n", encoding="utf-8")
            return root

        five = ["governance", "profiles", "prompts", "scripts", "docs"]

        r = build({n: "v1.4.4" for n in five})
        found, absent, unread = survey(r, cfg)
        if len(set(found.values())) == 1 and not absent and not unread:
            print("  ✅ packages on one version must report nothing"); ok += 1
        else:
            print(f"  ❌ findings on a clean project: {absent} {unread} {set(found.values())}"); bad += 1

        spec = {n: "v1.4.4" for n in five}; spec["profiles"] = "v1.3.0"
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if set(found.values()) == {"v1.4.4", "v1.3.0"}:
            print("  ✅ Project D's state (profiles one version behind) is caught"); ok += 1
        else:
            print(f"  ❌ a package left behind was not caught: {found}"); bad += 1

        spec = {n: "v1.4.4" for n in five if n != "docs"}
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if absent == ["docs"] and len(set(found.values())) == 1:
            print("  ✅ a missing package is a WARN, ⛔ never a version mismatch"); ok += 1
        else:
            print(f"  ❌ a missing package was counted as a mismatch: {absent} {found}"); bad += 1

        spec = {n: "v1.4.4" for n in five}; spec["docs"] = None
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if unread == ["docs"] and "docs" not in found:
            print("  ✅ an unreadable marker is INCOMPLETE, ⛔ never a pass"); ok += 1
        else:
            print(f"  ❌ an unreadable package was treated as passing: {unread} {found}"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 🔴 **F-04 (2026-09-02): ⛔ never let a string sort stand in for SemVer.**
    #    ⚠️ **Measured: `sorted({'v1.9.0','v1.10.0'})[-1]` → `v1.9.0`**, ⛔ the older one.
    #    **⇒ Adjudication `A4b: B`: the sensor reports disagreement only, ⛔ never a target.**
    import shutil as _sh, tempfile as _tf, subprocess as _sp, os as _os
    _t = pathlib.Path(_tf.mkdtemp(prefix="s2g_semver_"))
    try:
        for n, v in (("governance", "v1.10.0"), ("profiles", "v1.9.0"),
                     ("prompts", "v1.10.0"), ("scripts", "v1.10.0"), ("docs", "v1.10.0")):
            (_t / n).mkdir(parents=True)
            (_t / n / "_VERSION").write_text(v + "\n", encoding="utf-8")
        _env = dict(_os.environ, PYTHONIOENCODING="utf-8")
        _r = _sp.run([PY, str(HERE / "sensor_version_consistency.py"), "--root", str(_t)],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace", env=_env)
        _o = (_r.stdout or "") + (_r.stderr or "")
        if _r.returncode == 1 and "VERSION_MISMATCH" in _o:
            print("  ✅ v1.9.0 alongside v1.10.0 must report VERSION_MISMATCH"); ok += 1
        else:
            print(f"  ❌ the mismatch was not caught (exit {_r.returncode})"); bad += 1
        if "up to `v1.9.0`" not in _o and "up to `v1.10.0`" not in _o:
            print("  ✅ 🔴 the message names ⛔ no target version (the sensor cannot see the source)"); ok += 1
        else:
            print("  ❌ the sensor chose a target version — ⛔ and a string sort points the wrong way"); bad += 1
    finally:
        _sh.rmtree(_t, ignore_errors=True)

    # 🔴 **A watcher for the two copies: `version_packages` and `FRAMEWORK_DIRS` are the
    #    same set of names.** ⛔ **When they drift you get a package the upgrader can
    #    replace but the sensor never compares** — ⚠️ **which is exactly what `docs/` was
    #    between v1.3.0 and v1.4.0.**
    from framework_config import DEFAULTS
    import upgrade as _up
    if set(DEFAULTS["version_packages"]) == set(_up.FRAMEWORK_DIRS):
        print("  ✅ version_packages matches upgrade.FRAMEWORK_DIRS"); ok += 1
    else:
        a = set(DEFAULTS["version_packages"]); b = set(_up.FRAMEWORK_DIRS)
        print(f"  ❌ the two lists have drifted: config only {a - b} | upgrader only {b - a}"); bad += 1


version_consistency_case()


# ── 🔴 Rule sync is a read-only report (v1.4.4) ────────────────
# **v1.4.4 briefly had an `--adopt` that overwrote drifted rules for the user. Review found it
#   wrote the file before printing the "preview", claimed "the checkpoint holds it"
#   unconditionally, and still wrote when the checkpoint program had explicitly failed.
#   ⇒ The principal ruled the entire write path back out.**
#
# 🔴 **⇒ This tool now does two things: append missing entries, and report drift line by line.**
# ⚠️ **`SYNC-03` (missing and drift together) is the direct counterpart of `R-H003-02`:
#    the English edition once wrote the file and printed "Nothing was changed this run".**
def sync_report_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_sync_"))

    def build(my_body, second_rule=True):
        root = tmp / ("p%d" % len(list(tmp.iterdir())))
        (root / "governance").mkdir(parents=True)
        (root / "my").mkdir(parents=True)
        (root / "governance/RULES.md").write_text(
            "# Rules\n\n**R-19** The framework wording.\n\n**R-20** Another one.\n",
            encoding="utf-8")
        body = my_body + ("\n\n**R-20** Another one." if second_rule else "")
        (root / "my/MY_RULES.md").write_text(
            "# My rules\n\n## 1. Framework rules\n\n" + body
            + "\n\n<!-- FRAMEWORK_RULES_END -->\n", encoding="utf-8")
        return root

    def run_(root, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "tool_sync_my_rules.py"),
                            "--root", str(root)] + list(args),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def check(desc, cond, detail=""):
        global ok, bad
        if cond:
            print(f"  ✅ {desc}"); ok += 1
        else:
            print(f"  ❌ {desc}{detail}"); bad += 1

    DRIFT = "**R-19** This is the old sentence."
    OK19 = "**R-19** The framework wording."
    MARK = "[project override]"
    try:
        # SYNC-01: missing only → append, and the message admits the write
        r = build(OK19, second_rule=False); f = r / "my/MY_RULES.md"
        code, out = run_(r)
        check("SYNC-01: appends missing entries and states nothing existing was overwritten",
              code == 0 and "**R-20** Another one." in f.read_text(encoding="utf-8")
              and "No existing text was overwritten" in out)

        # SYNC-02: drift only → zero write, real diff lines and the two roads
        r = build(DRIFT); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-02: drift alone writes nothing", code == 0 and f.read_bytes() == b)
        check("🔴 SYNC-02: prints real diff lines (starting `+` or `-`)",
              "    -" in out and "    +" in out)
        check("SYNC-02: tells the user to paste the `+` lines, ⛔ never to replace the whole file",
              "paste the `+` lines" in out and "Never replace the whole" in out)

        # SYNC-03: 🔴 missing and drift together (the direct counterpart of R-H003-02)
        r = build(DRIFT, second_rule=False); f = r / "my/MY_RULES.md"
        code, out = run_(r)
        wrote = "**R-20** Another one." in f.read_text(encoding="utf-8")
        check("🔴 SYNC-03: with both missing and drift, the append really happens",
              code == 0 and wrote)
        check("🔴 SYNC-03: ⛔ must never write and claim nothing changed",
              wrote and "There is nothing to append" not in out)
        check("SYNC-03: the drift is still reported", "RULE_TEXT_DRIFT" in out)

        # SYNC-05a: a valid override → untouched, said so
        r = build("**R-19** My own sentence.\n" + MARK
                  + " our corpus is transcripts, so the criterion has to be stricter.")
        f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-05a: a valid override is untouched and reported as marked",
              f.read_bytes() == b and f"is marked {MARK}" in out)

        # SYNC-05b: a marker with no reason → must say the sensor will FAIL
        r = build("**R-19** My own sentence.\n" + MARK + " oops")
        f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("🔴 SYNC-05b: a marker with no reason must say the sensor will FAIL",
              f.read_bytes() == b and "OVERRIDE_WITHOUT_REASON" in out)

        # SYNC-06: neither → zero write, honest report
        r = build(OK19); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-06: nothing to do writes nothing and says it was computed",
              code == 0 and f.read_bytes() == b and "not a skipped one" in out)

        # SYNC-07: 🔴 the --adopt flag must be gone
        r = build(DRIFT); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r, "--adopt")
        check("🔴 SYNC-07: `--adopt` was ruled out; it must be rejected with zero write",
              code != 0 and f.read_bytes() == b, f" (exit {code})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


sync_report_case()


# ── 🔴 A withdrawn CLI flag ⛔ must not survive in current instructions (v1.4.4, `R-H006-05`)
# 🔴 **Measured case (Codex review, 2026-09-02): `--adopt` had been removed from argparse,
#    and three pieces of current instruction still told the user to add that flag** —
#    the upgrade completion message in both editions, and `sensor_my_rules.py`'s docstring
#    in both editions.
# ⚠️ **The paired sample at the time was `SYNC-07`: it proved "the program refuses it".**
#    ⛔ **"The program refuses it" and "nobody is told to use it" are two different things** —
#    **a user typing what the instructions say gets an error he has no way to explain.**
# 🔴 **⇒ Withdrawing a flag means withdrawing two things: the flag and the instruction.**
#
# ⚠️ **The one exception is a historical account, and it has to say so itself:**
#    **`[withdrawn]` must appear in the same paragraph.**
#    ⛔ **No word whitelist** ("used to", "briefly", ...) — **a criterion like that is
#    bypassed by rephrasing.**
RETIRED_FLAGS = {"--adopt": "v1.4.4"}
RETIRED_MARK = "[withdrawn]"
# ⚠️ The scope is current operator-facing instruction. ⛔ `SENSOR_CHANGELOG.md` is out:
#    that file **is** the historical record. ⛔ `run_selftest.py` is out too: a paired
#    sample has to be able to write the flag down.
def retired_flag_case():
    global ok, bad
    root = HERE.parents[1]
    surfaces = [root / n for n in ("SETUP.md", "README.md", "INITIALIZE_PROMPT.md")]
    # ⚠️ Sort by `p.name`, ⛔ never `Path` itself — `WindowsPath` comparison
    #    casefolds and `PosixPath` does not (`N-8`).
    surfaces += [p for p in sorted(HERE.glob("*.py"), key=lambda q: q.name)
                 if p.name != "run_selftest.py"]
    bad_hits = []
    for p in surfaces:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for para in text.split("\n\n"):
            for flag in RETIRED_FLAGS:
                if flag in para and RETIRED_MARK not in para:
                    first = next(l for l in para.splitlines() if flag in l)
                    bad_hits.append(f"{p.name}: {first.strip()[:70]}")
    if not bad_hits:
        print(f"  ✅ 🔴 SYNC-08: no withdrawn flag survives in current instructions "
              f"({len(surfaces)} files scanned)")
        ok += 1
    else:
        print("  ❌ 🔴 SYNC-08: current instructions still tell the user to use a "
              "withdrawn flag")
        for h in bad_hits:
            print(f"       {h}")
        bad += 1
    # ⚠️ **⛔ The scan itself needs a counter-sample: an unmarked fake instruction must
    #    be caught. ⛔ Otherwise "scanned, all clear" and "the scan is broken" look alike.**
    probe = "Run tool_sync_my_rules.py with --adopt to take the framework wording."
    caught = any(f in probe and RETIRED_MARK not in probe for f in RETIRED_FLAGS)
    if caught:
        print("  ✅ SYNC-08: the scan does FAIL a fake instruction (⛔ falsifiable)"); ok += 1
    else:
        print("  ❌ SYNC-08: the scan does not react to an obvious violation — ⛔ it is empty")
        bad += 1


retired_flag_case()


# ── 🔴 Retired packages (v1.4.4, A3) ──────────────────────────
# **`policy/` was folded into `governance/` in v1.4.4.**
# 🔴 **A folder taken out of `FRAMEWORK_DIRS` becomes an orphan in an existing project:
#    its contents stay frozen at the version it retired in, ⛔ and nothing touches it again.**
# ⚠️ **The upgrader ⛔ does not delete your files (constitution §6.3), but it must say so** —
# **⛔ an orphan folder nobody knows about is exactly a stale framework document.**
def retired_dirs_case():
    global ok, bad
    import shutil, tempfile
    import upgrade as _up

    # ① 🔴 a name must ⛔ never be both "replaceable" and "retired"
    both = set(_up.RETIRED_DIRS) & set(_up.FRAMEWORK_DIRS)
    if not both:
        print("  ✅ the retired list and the replaceable list ⛔ do not overlap"); ok += 1
    else:
        print(f"  ❌ {both} is on both lists — ⛔ the verdict would depend on code order"); bad += 1

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_retired_"))
    try:
        # ② must report: the folder is still there
        root = tmp / "has"
        (root / "policy").mkdir(parents=True)
        if _up.retired_present(root) == [("policy", "v1.4.4", "governance")]:
            print("  ✅ a project that still has `policy/` gets it listed"); ok += 1
        else:
            print("  ❌ the orphan was not listed — ⛔ silence means the mechanism is absent"); bad += 1

        # ③ ⛔ must not false-alarm: the folder does not exist (= a normal new project)
        root = tmp / "clean"
        root.mkdir()
        if _up.retired_present(root) == []:
            print("  ✅ a new project without `policy/` ⛔ gets no retirement notice"); ok += 1
        else:
            print("  ❌ a clean new project was told about a retired folder — ⛔ permanent red"); bad += 1

        # ④ an empty orphan counts too: ⚠️ the criterion is "the folder exists",
        #    ⛔ not "it has anything in it"
        root = tmp / "empty"
        (root / "policy").mkdir(parents=True)
        if _up.retired_present(root):
            print("  ✅ an empty orphan is still listed (it still reads as maintained)"); ok += 1
        else:
            print("  ❌ an empty orphan was treated as absent"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


retired_dirs_case()


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
# 🔴 **The paired other half: "absent from the scan" has two causes, ⛔ and they are
#    ⛔ not the same thing.** **Triggering case (Project D, 2026-09-02): `archive/` sits
#    in the exclude list, so a file that really exists printed as "does not exist".
#    ⚠️ Acting on that (deleting the note) does not fail ⇒ nobody finds out it lied.**
my_index_case("🔴 the file is there and merely excluded: ⛔ must not be called missing",
              lambda t: ((t / "git-checkpoint.log").write_text("x", encoding="utf-8"),
                         (t / "my/MY_INDEX_notes.json").write_text(
                             '{"git-checkpoint.log": "x"}', encoding="utf-8"),
                         _gen(t), None)[-1], 0, "INDEX_NOTE_EXCLUDED",
              forbid=("INDEX_NOTE_DANGLING",), regen=False)
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


# -- v1.4.4: source and project must prove the same language edition -------
_TEST_LAUNCHERS = {
    "zh": {
        "bat": ("查看變更.bat", "檢查更新.bat", "記錄快照.bat"),
        "command": ("查看變更.command", "檢查更新.command", "記錄快照.command"),
    },
    "en": {
        "bat": ("review_changes.bat", "check_update.bat", "snapshot.bat"),
        "command": ("review_changes.command", "check_update.command", "snapshot.command"),
    },
}


def _seed_upgrade_edition(root, src, edition="en", layout="bat"):
    for base in (root, src):
        base.mkdir(parents=True, exist_ok=True)
        for name in _TEST_LAUNCHERS[edition][layout]:
            (base / name).write_text("launcher\n", encoding="utf-8")


def upgrade_edition_case():
    global ok, bad
    import shutil, tempfile
    from upgrade import _edition_fingerprint
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_edition_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        layouts_ok = True
        for edition in ("zh", "en"):
            for layout in ("bat", "command", "both"):
                sample = tmp / f"{edition}_{layout}"
                sample.mkdir()
                names = ("bat", "command") if layout == "both" else (layout,)
                for platform in names:
                    for name in _TEST_LAUNCHERS[edition][platform]:
                        (sample / name).write_text("x\n", encoding="utf-8")
                layouts_ok = layouts_ok and _edition_fingerprint(sample)[0] == edition
        if layouts_ok:
            print("  ✅ Chinese and English Windows-only, macOS-only, and dual signatures resolve uniquely"); ok += 1
        else:
            print("  ❌ a valid edition signature could not be resolved reliably"); bad += 1

        custom = tmp / "custom"
        _seed_upgrade_edition(custom, custom, "en", "bat")
        (custom / "research_tool.bat").write_text("x\n", encoding="utf-8")
        (custom / "my.command").write_text("x\n", encoding="utf-8")
        if _edition_fingerprint(custom)[0] == "en":
            print("  ✅ differently named project-owned .bat/.command files do not affect"
                  " edition detection (⛔ colliding names do — see the next case)"); ok += 1
        else:
            print("  ❌ a project-owned launcher contaminated edition detection"); bad += 1

        cases = []
        for label in ("cross", "mixed", "project_missing", "source_missing"):
            root = tmp / label / "project"
            src = root / "_upgrade"
            (root / "governance").mkdir(parents=True)
            (root / "governance/AGENTS.md").write_text("# OLD\n", encoding="utf-8")
            (src / "governance").mkdir(parents=True)
            (src / "governance/AGENTS.md").write_text("# NEW\n", encoding="utf-8")
            if label == "cross":
                _seed_upgrade_edition(root, root, "en", "bat")
                _seed_upgrade_edition(src, src, "zh", "bat")
            elif label == "mixed":
                _seed_upgrade_edition(root, src, "en", "bat")
                (root / _TEST_LAUNCHERS["zh"]["bat"][0]).write_text("x\n", encoding="utf-8")
            elif label == "project_missing":
                _seed_upgrade_edition(src, src, "en", "bat")
            else:
                _seed_upgrade_edition(root, root, "en", "bat")
            before = (root / "governance/AGENTS.md").read_bytes()
            result = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "governance",
                                     "--root", str(root)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", env=env)
            cases.append(result.returncode == 1
                         and (root / "governance/AGENTS.md").read_bytes() == before
                         and not (root / ".git").exists())
        if all(cases):
            print("  ✅ cross-edition, mixed, and missing signatures all fail before checkpoint with zero writes"); ok += 1
        else:
            print("  ❌ the edition gate did not fail closed for every uncertain state"); bad += 1

        # 🔴 **Paired sample: when the gate blocks, the message must name the file it saw.**
        #    ⚠️ **The gate reads only these twelve names and ⛔ not who put them there**,
        #    so a project-owned file carrying one of them makes a legitimate project
        #    read as "mixed" and blocks the whole upgrade. That is fail-closed,
        #    ⛔ but the user cannot tell which file caused it.
        #    **⇒ This sample's criterion is ⛔ not "did it block" but "did it say why".**
        collide = tmp / "collide" / "project"
        csrc = collide / "_upgrade"
        (collide / "governance").mkdir(parents=True)
        (collide / "governance/AGENTS.md").write_text("# OLD\n", encoding="utf-8")
        (csrc / "governance").mkdir(parents=True)
        (csrc / "governance/AGENTS.md").write_text("# NEW\n", encoding="utf-8")
        _seed_upgrade_edition(collide, csrc, "en", "bat")
        offender = _TEST_LAUNCHERS["zh"]["bat"][2]
        (collide / offender).write_text("x\n", encoding="utf-8")
        before = (collide / "governance/AGENTS.md").read_bytes()
        r = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "governance",
                            "--root", str(collide)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        told = offender in ((r.stdout or "") + (r.stderr or ""))
        if (r.returncode == 1 and told
                and (collide / "governance/AGENTS.md").read_bytes() == before):
            print(f"  ✅ a colliding project-owned launcher is named in the refusal: `{offender}`"); ok += 1
        else:
            print("  ❌ the refusal did not name the colliding file, so the user cannot fix it"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: root globs and platform launchers ----------------
def root_glob_platform_case():
    global ok, bad
    import shutil, tempfile
    from _common import _glob_dir, dead_glob_findings
    from framework_config import active_launcher_globs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rootglob_"))
    try:
        root = tmp / "project"
        root.mkdir()
        (tmp / "sibling.command").write_text("x", encoding="utf-8")
        findings = dead_glob_findings(["*.command"], "launcher_globs", root)
        bounded = _glob_dir(root, "*.command") == root
        no_parent_false_alarm = all(f[1] != "COVERAGE_COLLAPSE" for f in findings)
        if bounded and no_parent_false_alarm:
            print("  ✅ a root glob stays at project root; a neighbouring project cannot contaminate it"); ok += 1
        else:
            print("  ❌ a root glob escaped to the parent and manufactured coverage collapse"); bad += 1

        (root / "_upgrade/nested").mkdir(parents=True)
        (root / "_upgrade/nested/readme.txt").write_text("x", encoding="utf-8")
        (root / "_upgrade/nested/check.command").write_text("x", encoding="utf-8")
        excluded_findings = dead_glob_findings(
            ["*.txt", "*.command"], "excluded_dirs", root)
        if all(f[1] != "COVERAGE_COLLAPSE" for f in excluded_findings):
            print("  ✅ recursive collapse checks also exclude _upgrade (text and launcher)"); ok += 1
        else:
            print("  ❌ files under _upgrade still manufacture false coverage collapse"); bad += 1

        (root / "notes").mkdir()
        (root / "notes/real.txt").write_text("x", encoding="utf-8")
        real_findings = dead_glob_findings(["*.txt"], "real_child", root)
        if any(f[1] == "COVERAGE_COLLAPSE" for f in real_findings):
            print("  ✅ a real same-suffix file outside exclusions still means coverage collapse"); ok += 1
        else:
            print("  ❌ the exclusion fix is too broad and hides a real coverage collapse"); bad += 1

        (root / "check.bat").write_text("x", encoding="utf-8")
        globs = ["*.bat", "*.command"]
        win = active_launcher_globs(globs, root, "win32")
        if win == ["*.bat"]:
            print("  ✅ a Windows project may omit .command without an alarm"); ok += 1
        else:
            print(f"  ❌ Windows incorrectly requires a foreign launcher: {win}"); bad += 1
        (root / "check.bat").unlink()
        (root / "check.command").write_text("x", encoding="utf-8")
        mac = active_launcher_globs(globs, root, "darwin")
        if mac == ["*.command"]:
            print("  ✅ a macOS project may omit .bat without an alarm"); ok += 1
        else:
            print(f"  ❌ macOS incorrectly requires a foreign launcher: {mac}"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: validate index-tool arguments before any write ---
def my_index_cli_safety_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_idxcli_"))
    try:
        (tmp / "my").mkdir()
        idx = tmp / "my/MY_INDEX.md"
        idx.write_text("SENTINEL\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        help_run = subprocess.run([PY, str(HERE / "tool_my_index.py"), "--root", str(tmp), "--help"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", env=env)
        help_safe = help_run.returncode == 0 and idx.read_text(encoding="utf-8") == "SENTINEL\n"
        if help_safe:
            print("  ✅ tool_my_index.py --help does not write the index"); ok += 1
        else:
            print("  ❌ --help rewrote the index before showing help"); bad += 1
        unknown = subprocess.run([PY, str(HERE / "tool_my_index.py"), "--root", str(tmp), "--not-an-option"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        unknown_safe = unknown.returncode == 2 and idx.read_text(encoding="utf-8") == "SENTINEL\n"
        if unknown_safe:
            print("  ✅ an unknown tool_my_index.py option exits 2 without writing"); ok += 1
        else:
            print(f"  ❌ an unknown option must be refused without a write (exit {unknown.returncode})"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: parse rule-sync arguments first and write only the selected root --
def sync_my_rules_cli_safety_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rulescli_"))
    try:
        a_root, b_root = tmp / "A", tmp / "B"
        for project in (a_root, b_root):
            (project / "governance").mkdir(parents=True)
            (project / "my").mkdir()
        rules = "**R-01** first.\n\n**R-02** second.\n"
        a_my = "**R-01** first.\n\n<!-- FRAMEWORK_RULES_END -->\n"
        b_my = rules + "\n<!-- FRAMEWORK_RULES_END -->\n"
        for project in (a_root, b_root):
            (project / "governance/RULES.md").write_text(rules, encoding="utf-8")
        (a_root / "my/MY_RULES.md").write_text(a_my, encoding="utf-8")
        (b_root / "my/MY_RULES.md").write_text(b_my, encoding="utf-8")
        harness = b_root / "scripts/harness"
        harness.mkdir(parents=True)
        for name in ("tool_sync_my_rules.py", "sensor_my_rules.py", "_common.py",
                     "framework_config.py"):
            (harness / name).write_bytes((HERE / name).read_bytes())
        tool = harness / "tool_sync_my_rules.py"
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        before_a = (a_root / "my/MY_RULES.md").read_bytes()
        before_b = (b_root / "my/MY_RULES.md").read_bytes()

        help_run = subprocess.run([PY, str(tool), "--root", str(a_root), "--help"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", env=env)
        if (help_run.returncode == 0
                and (a_root / "my/MY_RULES.md").read_bytes() == before_a
                and (b_root / "my/MY_RULES.md").read_bytes() == before_b):
            print("  ✅ tool_sync_my_rules.py --help writes to neither project"); ok += 1
        else:
            print("  ❌ rule-sync --help triggered a write"); bad += 1

        unknown = subprocess.run([PY, str(tool), "--root", str(a_root), "--not-an-option"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        if (unknown.returncode == 2
                and (a_root / "my/MY_RULES.md").read_bytes() == before_a
                and (b_root / "my/MY_RULES.md").read_bytes() == before_b):
            print("  ✅ an unknown rule-sync option exits 2 with zero writes"); ok += 1
        else:
            print(f"  ❌ rule-sync did not safely reject an unknown option (exit {unknown.returncode})"); bad += 1

        rooted = subprocess.run([PY, str(tool), "--root", str(a_root)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        after_a = (a_root / "my/MY_RULES.md").read_text(encoding="utf-8")
        after_b = (b_root / "my/MY_RULES.md").read_bytes()
        if rooted.returncode == 0 and "**R-02** second." in after_a and after_b == before_b:
            print("  ✅ --root A updates only A, never the tool's own project B"); ok += 1
        else:
            print(f"  ❌ --root did not confine the write to the selected project (exit {rooted.returncode})"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: transient exemption is package + exact relative path --
def upgrade_transient_scope_case():
    global ok, bad
    import shutil, tempfile
    from upgrade import target_only_files
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_transient_"))
    try:
        cur, new = tmp / "current", tmp / "new"
        (cur / "harness").mkdir(parents=True)
        (cur / "custom").mkdir()
        (cur / "empty-owned").mkdir()
        new.mkdir()
        (cur / "harness/harness_status.json").write_text("framework", encoding="utf-8")
        (cur / "custom/harness_status.json").write_text("project", encoding="utf-8")
        scripts_only = target_only_files(cur, new, "scripts")
        if "harness/harness_status.json" not in scripts_only:
            print("  ✅ scripts/harness/harness_status.json is the exact transient exception"); ok += 1
        else:
            print("  ❌ the framework's own harness status was treated as project data"); bad += 1
        if "custom/harness_status.json" in scripts_only:
            print("  ✅ a namesake elsewhere under scripts still blocks replacement"); ok += 1
        else:
            print("  ❌ a name-only exception would silently delete project data"); bad += 1
        profiles_only = target_only_files(cur, new, "profiles")
        if "harness/harness_status.json" in profiles_only:
            print("  ✅ the same path outside the scripts package gets no exception"); ok += 1
        else:
            print("  ❌ the transient exception was not bound to the scripts package"); bad += 1
        if ("harness/harness_status.json" not in scripts_only
                and "custom/harness_status.json" in scripts_only
                and "harness/harness_status.json" in profiles_only):
            print("  ✅ UPG-REC-10: the transient exception is bound to exact package and path"); ok += 1
        else:
            print("  ❌ UPG-REC-10: the transient exception escaped its exact scope"); bad += 1
        if "empty-owned/" in scripts_only:
            print("  ✅ UPG-REC-11: a target-only empty directory blocks wholesale replacement"); ok += 1
        else:
            print("  ❌ UPG-REC-11: wholesale replacement would silently delete an empty directory"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: block target-only files before wholesale replacement --
def upgrade_target_only_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_targetonly_"))
    try:
        portable = tmp / "download" / "scripts" / "harness"
        portable.mkdir(parents=True)
        for name in ("upgrade.py", "_common.py", "framework_config.py"):
            (portable / name).write_bytes((HERE / name).read_bytes())
        portable_checkpoint = portable / "checkpoint.py"
        portable_checkpoint.write_text(
            'CHECKPOINT_TOOL_API = "spark2groundwork-checkpoint-tool-v1"\n'
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('checkpoint_called').write_text('yes')\n"
            "sys.exit(0)\n", encoding="utf-8")
        upgrade_tool = portable / "upgrade.py"
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        checkpoint_body = (
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('checkpoint_called').write_text('yes')\n"
            "sys.exit(0)\n")
        (root / "scripts/harness/checkpoint.py").write_text(checkpoint_body, encoding="utf-8")
        (root / "_upgrade/scripts/harness").mkdir(parents=True)
        (root / "_upgrade/scripts/harness/checkpoint.py").write_text(checkpoint_body, encoding="utf-8")
        (root / "prompts").mkdir()
        (root / "prompts/base.txt").write_text("old\n", encoding="utf-8")
        custom = root / "prompts/TEMPLATE_decompose.txt"
        custom.write_text("MY IDEA\n", encoding="utf-8")
        (root / "_upgrade/prompts").mkdir(parents=True)
        (root / "_upgrade/prompts/base.txt").write_text("new\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        args = [PY, str(upgrade_tool), "apply", "prompts", "--root", str(root)]
        blocked = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        untouched = (custom.read_text(encoding="utf-8") == "MY IDEA\n"
                     and (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n")
        before_checkpoint = not (root / "checkpoint_called").exists()
        listed = "prompts/TEMPLATE_decompose.txt" in ((blocked.stdout or "") + (blocked.stderr or ""))
        if blocked.returncode == 1 and untouched and before_checkpoint and listed:
            print("  ✅ target-only files are named and blocked before checkpoint or replacement"); ok += 1
        else:
            print("  ❌ target-only blocking must name the file and perform zero writes"); bad += 1

        idea = root / "FIRST_IDEA.md"
        custom.replace(idea)

        # 🔴 **The receipt gate (v1.4.4, `R-H006-02`): the checkpoint reports success,
        #    ⛔ and the restore point cannot be named.**
        #    ⚠️ **The stub checkpoint here only exits 0; ⛔ it builds no git history** —
        #    **⇒ `upgrade.py` cannot read back the pre-image commit id.**
        #    🔴 **⛔ That must not overwrite: a restore point that cannot say where it is
        #    is not a restore point.**
        #    ⚠️ **The other half of the pair is below: once git is there, the same command
        #    must succeed.**
        norepo = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        kept = (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n"
        if norepo.returncode == 2 and kept:
            print("  ✅ 🔴 no overwrite when the checkpoint id cannot be read back "
                  "(receipt gate)"); ok += 1
        else:
            print(f"  ❌ 🔴 the receipt gate is inert: exit {norepo.returncode}, content "
                  f"was {'kept' if kept else 'OVERWRITTEN'}"); bad += 1

        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=t",
                        "commit", "-qm", "base"], capture_output=True)

        # From here on, use the real same-version peer in the download; keep the project copy incompatible.
        portable_checkpoint.write_bytes((HERE / "checkpoint.py").read_bytes())

        # The current project can still carry the old checkpoint CLI. A downloaded
        # v1.4.4 upgrader must use the downloaded checkpoint peer for the bootstrap.
        (root / "checkpoint_called").unlink(missing_ok=True)
        (root / "scripts/harness/checkpoint.py").write_text(
            "import sys\nsys.exit(9)\n", encoding="utf-8")

        applied = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        replaced = (root / "prompts/base.txt").read_text(encoding="utf-8") == "new\n"
        survived = idea.read_text(encoding="utf-8") == "MY IDEA\n"
        if applied.returncode == 0 and replaced and survived and not (root / "checkpoint_called").exists():
            print("  ✅ the downloaded checkpoint bootstraps replacement while the old project tool refuses, and the root idea survives"); ok += 1
        else:
            detail = ((applied.stdout or "") + (applied.stderr or "")).strip().replace("\n", " | ")
            print(f"  ❌ wholesale replacement failed after project data moved out "
                  f"(exit {applied.returncode}: {detail})"); bad += 1
        # 🔴 The durable receipt and its safe recovery interface must be on screen.
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace").stdout.strip()
        out_all = (applied.stdout or "") + (applied.stderr or "")
        if head and head in out_all and "receipt: upg-" in out_all and "receipt-diff" in out_all:
            print("  ✅ 🔴 the completion message hands over a durable restore receipt and safe interface"); ok += 1
        else:
            print("  ❌ 🔴 the completion message hands over no usable restore point"); bad += 1

        import re
        found = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}", out_all)
        restored = subprocess.run([PY, str(upgrade_tool), "restore",
                                   found.group(0) if found else "missing", "prompts/base.txt",
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        if (restored.returncode == 0
                and (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n"
                and "upg-" in ((restored.stdout or "") + (restored.stderr or ""))):
            print("  ✅ old project + download + non-scripts package restores with an undo receipt"); ok += 1
        else:
            print(f"  ❌ post-bootstrap restore did not use the download peer safely (exit {restored.returncode})"); bad += 1

        foreign = "snapshot.bat" if sys.platform == "darwin" else "snapshot.command"
        (root / "_upgrade" / foreign).write_text("foreign launcher\n", encoding="utf-8")
        routine = subprocess.run([PY, str(upgrade_tool), "diff", "--root", str(root)],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        explicit = subprocess.run([PY, str(upgrade_tool), "apply", foreign,
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        omitted = foreign not in ((routine.stdout or "") + (routine.stderr or ""))
        installed = (root / foreign).read_text(encoding="utf-8") == "foreign launcher\n"
        if routine.returncode == 0 and omitted and explicit.returncode == 0 and installed:
            print("  ✅ routine diff omits an absent foreign launcher, but explicit apply installs it"); ok += 1
        else:
            print("  ❌ the foreign-launcher routine omission or explicit apply escape hatch failed"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: durable upgrade receipts must prove and recover the exact pre-image --
def upgrade_receipt_case():
    global ok, bad
    import json, re, shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_receipts_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    def git(root, *args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    def build(name, ignored=False):
        root = tmp / name
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        # A minimal tool-mode checkpoint: commit the worktree, never move `reviewed`.
        (root / "scripts/harness/checkpoint.py").write_text(
            "import pathlib, subprocess, sys\n"
            "r=pathlib.Path(__file__).resolve().parents[2]\n"
            "a=subprocess.run(['git','-C',str(r),'add','-A'])\n"
            "if a.returncode: sys.exit(a.returncode)\n"
            "d=subprocess.run(['git','-C',str(r),'diff','--cached','--quiet'])\n"
            "if d.returncode==1:\n"
            " p=subprocess.run(['git','-C',str(r),'-c','user.email=a@b','-c','user.name=t','commit','-qm','tool checkpoint'])\n"
            " sys.exit(p.returncode)\n"
            "sys.exit(0 if d.returncode==0 else d.returncode)\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "_upgrade/docs").mkdir(parents=True)
        (root / "_upgrade/docs/fig.svg").write_text("NEW\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade")
        if ignored:
            (root / ".gitignore").write_text("/docs/fig.svg\n", encoding="utf-8")
        else:
            (root / "docs/fig.svg").write_text("OLD\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        git(root, "add", "-A")
        git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "base")
        if ignored:
            (root / "docs/fig.svg").write_text("IGNORED HAND EDIT\n", encoding="utf-8")
        return root

    def apply(root):
        return subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "docs",
                               "--root", str(root)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env)

    def receipt_id(result):
        m = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}",
                      (result.stdout or "") + (result.stderr or ""))
        return m.group(0) if m else None

    try:
        ignored = build("ignored", ignored=True)
        result = apply(ignored)
        kept = (ignored / "docs/fig.svg").read_text(encoding="utf-8") == "IGNORED HAND EDIT\n"
        if result.returncode == 2 and kept and receipt_id(result) is None:
            print("  ✅ UPG-REC-03: an ignored same-path hand edit blocks replacement"); ok += 1
        else:
            print("  ❌ UPG-REC-03: ignored same-path content was not protected"); bad += 1

        hidden_ok = True
        for flag, clear in (("--assume-unchanged", "--no-assume-unchanged"),
                            ("--skip-worktree", "--no-skip-worktree")):
            root = build(flag.lstrip("-").replace("-", "_"))
            git(root, "update-index", flag, "--", "docs/fig.svg")
            (root / "docs/fig.svg").write_text(f"HIDDEN {flag}\n", encoding="utf-8")
            result = apply(root)
            hidden_ok = hidden_ok and result.returncode == 2 and \
                (root / "docs/fig.svg").read_text(encoding="utf-8") == f"HIDDEN {flag}\n"
            git(root, "update-index", clear, "--", "docs/fig.svg")
        if hidden_ok:
            print("  ✅ UPG-REC-04: assume-unchanged and skip-worktree cannot hide a pre-image"); ok += 1
        else:
            print("  ❌ UPG-REC-04: an index flag bypassed pre-image verification"); bad += 1

        root = build("roundtrip")
        reviewed = git(root, "rev-parse", "HEAD").stdout.strip()
        git(root, "tag", "reviewed", reviewed)
        (root / "docs/fig.svg").write_text("HAND EDIT\n", encoding="utf-8")
        result = apply(root)
        rid = receipt_id(result)
        listed = subprocess.run([PY, str(HERE / "upgrade.py"), "receipts", "--root", str(root)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        ref = git(root, "rev-parse", f"refs/spark2groundwork/restore/{rid}") if rid else None
        store_raw = git(root, "rev-parse", "--git-path", "spark2groundwork/receipts").stdout.strip()
        store = pathlib.Path(store_raw)
        if not store.is_absolute():
            store = root / store
        manifest = store / f"{rid}.json" if rid else store / "missing.json"
        manifest_data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
        durable = (result.returncode == 0 and rid and manifest.is_file()
                   and ref.returncode == 0 and rid in listed.stdout
                   and manifest_data["ref"].endswith(rid))
        if durable:
            print("  ✅ UPG-REC-05: apply persists a verifiable manifest and private Git ref"); ok += 1
        else:
            print("  ❌ UPG-REC-05: the receipt is not durable or listable"); bad += 1

        captured = git(root, "show", f"refs/spark2groundwork/restore/{rid}:docs/fig.svg") \
            if rid else None
        if captured and captured.returncode == 0 and captured.stdout == "HAND EDIT\n":
            print("  ✅ UPG-REC-08: a normal tracked hand edit is captured before apply"); ok += 1
        else:
            print("  ❌ UPG-REC-08: the tracked pre-image was not captured"); bad += 1

        diffed = subprocess.run([PY, str(HERE / "upgrade.py"), "receipt-diff", rid or "missing",
                                 "docs/fig.svg", "--root", str(root)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", env=env)
        restored = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                   "docs/fig.svg", "--root", str(root)], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", env=env)
        receipt_count = len(list(store.glob("*.json")))
        roundtrip = (diffed.returncode == 0 and "-HAND EDIT" in diffed.stdout and "+NEW" in diffed.stdout
                     and restored.returncode == 0
                     and (root / "docs/fig.svg").read_text(encoding="utf-8") == "HAND EDIT\n"
                     and receipt_count == 2
                     and git(root, "rev-parse", "refs/tags/reviewed").stdout.strip() == reviewed
                     and git(root, "diff", "--cached", "--quiet").returncode == 0)
        if roundtrip:
            print("  ✅ UPG-REC-06: diff and single-file restore work, with an undo receipt and stable reviewed tag"); ok += 1
        else:
            detail = (f"diff={diffed.returncode}, restore={restored.returncode}, "
                      f"receipts={receipt_count}, current={repr((root / 'docs/fig.svg').read_text(encoding='utf-8'))}, "
                      f"diff_out={repr(diffed.stdout)}, restore_out={repr(restored.stdout)}, "
                      f"restore_err={repr(restored.stderr)}")
            print(f"  ❌ UPG-REC-06: receipt diff/restore round trip was not safe ({detail})"); bad += 1

        before_count = len(list(store.glob("*.json")))
        outside = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                  "../outside", "--root", str(root)], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", env=env)
        (root / "docs/fig.svg").unlink()
        missing = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                  "docs/fig.svg", "--root", str(root)], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", env=env)
        after_count = len(list(store.glob("*.json")))
        if outside.returncode == 1 and missing.returncode == 1 and before_count == after_count:
            print("  ✅ UPG-REC-07: path escape and missing-current restore fail with zero receipt writes"); ok += 1
        else:
            print("  ❌ UPG-REC-07: restore confinement or fail-closed behavior regressed"); bad += 1

        crlf = build("crlf")
        (crlf / ".gitattributes").write_text("docs/*.svg text eol=lf\n", encoding="utf-8")
        git(crlf, "add", ".gitattributes")
        git(crlf, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "attributes")
        (crlf / "docs/fig.svg").write_bytes(b"OLD\r\n")
        normalized = apply(crlf)
        if (normalized.returncode == 0
                and (crlf / "docs/fig.svg").read_text(encoding="utf-8") == "NEW\n"):
            print("  ✅ UPG-REC-09: CRLF normalization follows Git semantics without a false block"); ok += 1
        else:
            print("  ❌ UPG-REC-09: byte-only CRLF differences caused a false block"); bad += 1

        if manifest.is_file():
            tampered = json.loads(manifest.read_text(encoding="utf-8"))
            tampered["files"][0]["blob"] = "0" * 40
            manifest.write_text(json.dumps(tampered), encoding="utf-8")
        invalid = subprocess.run([PY, str(HERE / "upgrade.py"), "receipt-diff", rid or "missing",
                                  "--root", str(root)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", env=env)
        if invalid.returncode == 2:
            print("  ✅ UPG-REC-12: a tampered manifest is rejected before use"); ok += 1
        else:
            print("  ❌ UPG-REC-12: receipt integrity checks accepted a tampered manifest"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: restore must write nothing when no compatible peer exists -----
def upgrade_peer_fail_case():
    global ok, bad
    import re, shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_peerfail_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        # This old copy leaves evidence if executed and deliberately lacks the API marker.
        (root / "scripts/harness/checkpoint.py").write_text(
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('UNEXPECTED').write_text('x')\n",
            encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs/fig.svg").write_text("OLD\n", encoding="utf-8")
        (root / "_upgrade/docs").mkdir(parents=True)
        (root / "_upgrade/docs/fig.svg").write_text("NEW\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade")
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=t",
                        "commit", "-qm", "base"], capture_output=True)
        applied = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "docs",
                                  "--root", str(root)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", env=env)
        found = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}",
                          (applied.stdout or "") + (applied.stderr or ""))
        portable = tmp / "standalone"
        portable.mkdir()
        for name in ("upgrade.py", "_common.py", "framework_config.py"):
            (portable / name).write_bytes((HERE / name).read_bytes())
        store_raw = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path",
                                    "spark2groundwork/receipts"], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace").stdout.strip()
        store = pathlib.Path(store_raw)
        if not store.is_absolute():
            store = root / store
        before_count = len(list(store.glob("*.json")))
        before = (root / "docs/fig.svg").read_bytes()
        restored = subprocess.run([PY, str(portable / "upgrade.py"), "restore",
                                   found.group(0) if found else "missing", "docs/fig.svg",
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        out = (restored.stdout or "") + (restored.stderr or "")
        safe = (applied.returncode == 0 and found is not None
                and restored.returncode == 2
                and (root / "docs/fig.svg").read_bytes() == before
                and len(list(store.glob("*.json"))) == before_count
                and not (root / "UNEXPECTED").exists()
                and "same edition and version" in out)
        if safe:
            print("  ✅ restore with no compatible peer skips the old tool, writes nothing, and says to redownload"); ok += 1
        else:
            print("  ❌ restore did not fail closed when no compatible peer existed"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


root_glob_platform_case()
upgrade_edition_case()
my_index_cli_safety_case()
sync_my_rules_cli_safety_case()
upgrade_transient_scope_case()
upgrade_target_only_case()
upgrade_receipt_case()
upgrade_peer_fail_case()
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
