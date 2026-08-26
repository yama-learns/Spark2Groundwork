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
scope_case("editing a T0 FAILs (folded in from t0_docs, never restated in deny)",
           ["governance/AGENTS.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "policy"]})
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
