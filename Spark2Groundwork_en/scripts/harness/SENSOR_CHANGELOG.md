# Sensor Changelog

**⛔ Every sensor change must log its triggering case here** (constitution §7.1, gate three).

**Format:** number | date | one line. Must state: the triggering case, what was changed,
and where the paired fixtures live.

> 🔴 **This file contains two `#n` series sharing one namespace.**
> **Pre-history entries carry no date; maintenance entries always carry one.**
> ⛔ **Cite a maintenance entry with its date** (e.g. `#12 | 2026-08-20`);
> **cite a pre-history entry as "pre-history #n". ⛔ A bare `#1` is ambiguous.**
> ⚠️ **This file is append-only, ⛔ so nothing is renumbered** — what changed is how you cite it,
> not the record.
> ⚠️ **Pre-history entries are each edition's own history and ⛔ need not match**
> (this edition carries one extra entry about a constant specific to the English edition).

---

## Pre-history (**no dates**)

## #0 | Initial framework version

**This sensor suite was ported from two projects in real use; every one carries a real case:**

| Sensor | Triggering case |
|---|---|
| `sensor_claim_ledger.py` | Four figures in an assessment report had no source in the original, and the original's conclusion ran **in the opposite direction** |
| ├ anchor normalisation | An anchor was truncated to a 20-character fragment by the `fi` ligature in `identified`; at the time this was misdiagnosed as "a limitation of the extraction" |
| └ extraction hashing | Found when opening corpus write access: **if a party with write access can alter the extraction, the evidence chain becomes circular** |
| `sensor_conjecture_ledger.py` | Falsification fields sat empty for a long time while the conjecture was still cited as a premise |
| `sensor_self_certification.py` | 64 files claimed "all figures verified against the originals" while a fabricated sample size sat in the same batch |
| `sensor_governance_text.py` | 17 verbatim cross-file duplicates; 8 dangling section citations, **4 of which had existed since the project was created** |
| `sensor_scope_and_t0.py` | A checking program reported 16 violations **against the wrong repository**, with complete confidence |
| `sensor_prompt_self_contained.py` | A prompt's §1 quoted "do not write 'as above'", **and its lower half wrote "Same as R3-1"** |

⚠️ **This is the single exception to "no measured case, no sensor", and the reason is written here:**
**those cases happened in other projects, not yours.**
They are listed **to save you the detour, not to claim you are immune.**

⛔ **Every sensor you add still obeys "no measured case, no sensor".**

---

## #1 | Live solo-agent test of the framework itself (**11 defects, all found by the tested agent**)

**Method:** an independent agent ran the full flow inside a copy of the framework
(read the rules → decompose a cross-domain essay → fill in blanks → run sensors → file a handoff),
and answered four feedback questions.

### 🔴 Worst: the framework's own template taught a phrasing that switched off its own sensor

`TEMPLATE_decompose.txt` originally advised marking an unfillable falsification field
as "falsification pending".

**Measured: following that advice dropped `FALSIFICATION_EMPTY` from 2 to 1, with the exit code unchanged.**
Cause: the placeholder list matched exact strings only, so **"falsification pending" counted as filled.**

⚠️ **That is the "silent filtering" family, triggered by the framework's own template.**

### 🔴 Deeper: the incentives ran backwards

The tested agent's own words:

> Leaving "-" makes it look like I did less; writing "if X exceeds r > .8 then this is refuted"
> reads as entirely acceptable, and **nobody, human or sensor, can tell it is decorative**.
> It would even take that entry from WARN to silent.
> **The incentives run backwards: honesty gets a yellow light, invention does not.**

**Fix: the warning condition changed from "field is empty" to "not yet adjudicated by a human".**
Added a `Falsification adjudicated` field; **filling in text does not clear the warning —
only a human setting it to `adjudicated` does.** ⛔ AI must not set that field.
Check code renamed to `FALSIFICATION_UNADJUDICATED`.

### The other nine

| # | Defect | Handling |
|---|---|---|
| 1 | A heading said "three-level tags" while the table listed four | Renamed; no count in the clause (R-16) |
| 2 | "Output area" was undefined while §6 required writing only to it | Defined in constitution §6.1 |
| 3 | §4.2 required overwriting the state document; §6 implied otherwise | State document explicitly included in every role's output area |
| 4 | **No rule for "instruction conflicts with T0, what do I do now"** | Constitution §4.3, four cases |
| 5 | Ledger "scope" field undefined | Values defined |
| 6 | Handoff `<role>` had no enumerated values | Enumerated (an entry point for the "required fields induce fabrication" family) |
| 7 | A dangling section citation | Fixed (caught by a sensor) |
| 8 | A cross-file duplicate sentence | Changed to a citation (caught by a sensor) |
| 9 | No handling when the authoritative model field is absent | Three-step fallback added |

### ⚠️ Item 4 is the deepest structural gap

The tested agent was told to write into the ledger while **four documents said AI must not**.
It derived its own handling from the exemption clause, executed, and logged the exemption.

> **An agent deriving on its own that it may make an exception
> is exactly what this framework should worry about most.**

**The framework can tolerate an exception; it cannot tolerate nobody knowing one was made.**

### ✅ Two observations that the framework works

1. **The tested agent judged all seven WARNs individually and changed no document to turn the screen green.**
2. The failure-family table did work — its own words:
   **"It was the name 'silent filtering' that let me recognise what shape the template-and-sensor defect was."**

### ⛔ What this test could not verify (**coverage declaration**)

- **The tested agent was the same model family as the framework's author.**
  The cross-model adversarial layer was **entirely untested**.
- Single round. Cross-round drift (the "index as authority", "fixed one layer" and "document proliferation" families) **untested**.
- External-tool, multi-role, and Windows batch scenarios untested.

---

## #2 | English edition: constants that do not port across languages

**The duplicate check used a sentence-length window of 24–80 characters (tuned on Chinese).**
Ported unchanged to English, a ~100-character rule sentence **fell outside the window and the
duplicate check silently found nothing** — caught by the paired fixture, not by reading the code.

**Fix: window widened to 40–220 for the English edition, with the reason noted in the code.**

> **A rule that is "the same rule" in two languages can still need different constants.**

---

## Maintenance (**always dated**)

## #1 | 2026-08-19 | Extraction tools: identifiable backend + manifest self-check

**Triggering cases (three, from another running project and from this maintenance round):**

1. **Two extracts of the same 11 papers cross-tested: 62.5% strict anchor hit rate, 95.7%
   after stripping whitespace and punctuation** — 33.2 points were purely whitespace and
   hyphen differences. The old pypdf backend drops end-of-line spaces on some PDFs, producing
   glued words, and `anchor_norm.py` can collapse whitespace **but cannot insert whitespace
   that is not there.** → **Fix the extractor, not the comparator** (constitution §7.3 step 1; `R-20`).

2. **A comparable tool silently fell back to a different extraction path** when its primary
   backend failed, mixing two kinds of extract in one batch with no marker in the file.
   → Backend name goes into the header and the manifest; fallbacks record `degraded_from`.
   **Degrading is fine; degrading silently is not.**

3. **`out_dir.mkdir()` ran before the "are there any PDFs" check**, so one accidental
   invocation left an empty `corpus_md/` behind, and `sensor_claim_ledger.py` reported
   INCOMPLETE for it — **the whole harness went from 0 to 2, and `git status` could not see
   it** (git does not track empty directories). → Order swapped.

**What changed:**

| File | Change |
|---|---|
| `tool_pdf_to_md.py` | PyMuPDF primary + pypdf fallback; backend recorded; orphan check; `mkdir` ordering; **manifest gains `selfcheck_hit` / `selfcheck_n` / `anchors_spanning_pages`** |
| `tool_extract_compare.py` | **New.** Strict / loose / gap columns — the gap column separates "normalisation coverage" from "extraction quality" |

**Where are the paired fixtures:** ⚠️ **There are none yet.** Both are **tools, not sensors**;
they are not part of the `run_all_sensors.py` suite, so constitution §7.1 fixtures were not built.
⛔ **If `selfcheck_hit` is ever promoted to a sensor criterion, paired fixtures come first.**

**The self-check, measured (`[measured]`, re-runnable):**

The first version scored **93.3%** on a 9-page paper, and **both misses were sentences
crossing a `<!-- page: N -->` marker.**
⚠️ Re-checked per constitution §7.3 step 1: **the sampling was broken, not the extract.**
→ Changed to sample per page; page-spanning candidates are reported as a count
(`anchors_spanning_pages`) and excluded from the hit rate.
**After the fix the same paper scores 100% (30 sampled, 6 page-spanning candidates).**
→ The same finding also produced `ledgers/Claim_Ledger.md` §1.1 rule 5 (**anchors must not span pages**).

---

## #2 | 2026-08-19 | Self-test: the "must not false-alarm" half no longer checks only the exit code

**Triggering case (measured in another project, then confirmed to hold here):**

A `WARN`-level finding **does not change the exit code** (`emit` in `_common.py`: only
FAIL→1 and INCOMPLETE→2). So a "must not false-alarm" test asserting only `exit == 0`
**prints ✅ for any number of WARN-level false alarms.**

**Measured here before the fix (re-runnable):**

```
python3 scripts/harness/sensor_self_certification.py --root scripts/harness/selftest/selfcert_clean
python3 scripts/harness/sensor_governance_text.py   --root scripts/harness/selftest/gov_clean
```

→ The first emitted **2** WARNs, the second **3**, **and `run_selftest.py` printed ✅ for both.**

**What changed:**

1. `expect()` gains **`forbid`**: the finding codes that must **never** appear on that clean
   fixture. All five "must not false-alarm" fixtures now carry one, taken from their paired
   "must catch" test.
2. ⚠️ The criterion is deliberately **not** "no WARN at all" — a fixture directory does not
   contain every glob, so `SCAN_GLOB_MATCHES_NOTHING` is infrastructure noise.
   **Treating noise as a false alarm pushes the next person to add an exemption, and
   exemptions hollow the self-test into a blind spot.**
3. ⛔ **But tolerance must be visible:** tolerated WARN codes and counts are printed at the end.
   **Silent tolerance and no tolerance look the same on screen.**

⚠️ **The first version counted the intended detections as "tolerated", making the number
meaningless (18 reported, 13 real).** The `needle` code is now excluded;
**that mistake is kept in the code comments, not deleted.**

**Where are the paired fixtures:** the existing 12 are reused. ⚠️ **No new fixture this time** —
`forbid` adds a second assertion to existing fixtures rather than a new subject under test.
⛔ If anyone later loosens a `forbid`, they must state which code and why.

---

## #3 | 2026-08-19 | Conjecture sensor: editions aligned, and five defects the alignment exposed

**Triggering case:** the editions were **not equivalent**. `sensor_conjecture_ledger.py` was
13,839 bytes in Chinese and 7,065 in English, **and the English edition was missing three
whole checks**:

| Missing check | What it governs |
|---|---|
| `CITATION_NOT_IN_LEDGER` | Another document cites a conjecture ID that does not exist — **the main mechanical defence against the "conjecture drifts into premise" family** |
| `CONJECTURE_STATUS_INVALID` | State outside the six defined in ledger §0.1 |
| `EVIDENCE_MISSING_FOR_STATUS` | 🟢 / 🔴 with an empty Basis |

⚠️ Meanwhile the English ledger §0.4 says verbatim that "a sensor will **silently** treat it
as a citation of conjecture C-01" — **describing a behaviour that edition did not have.**

### 🔴 Five defects the port exposed (**all of them in the Chinese original**)

| # | Defect | Shape |
|---|---|---|
| 1 | `VALID_STATUS` held only 🔵🟡🟢🔴 — **four** — while ledger §0.1 defines **six** | **A correctly retired (⚫) or dormant (🟤) conjecture was FAILed** — the false alarm `R-19` forbids |
| 2 | The falsification check had **no exemption for ⚫ / 🟤** | ⚠️ **Masked by 1**: the old code `continue`d on an invalid state, so ⚫/🟤 never reached this check. **Fixing either one alone exposes the other** |
| 3 | A hard-coded `EXCLUDED_DIRS` in the file shadowed the imported `excluded` | Duplicated `framework_config` and **already out of sync** (missing `node_modules`, `.venv`), and contained **a directory name from another project**. Violates constitution §3.2 and `R-21` |
| 4 | Self-exclusion of the ledger compared `p.name != LEDGER_NAME`, but `LEDGER_NAME` is a **path** | Never equal to a bare filename → **the ledger was always in scan scope and `SCAN_GLOB_MATCHES_NOTHING` could never fire.** A guard that cannot trigger is the same shape as a dead exemption |
| 5 | An empty scan was reported as `FAIL` | "Could not scan" is **could not check**, so INCOMPLETE (`R-22`, constitution §7.4) |

### Decision 9 landed alongside: a deliberate blank is not a forgotten field

Ledger §0.3 rule 1 says verbatim that writing "-" is no worse than inventing something, and
the decompose template's rule 3 teaches "put '-' in the field and add a following line
`**Why I could not fill this:** ...`" — **and the old message printed "falsification
condition empty" for exactly that, word for word identical to a forgotten field.**

> ⚠️ **The consequence is hard to see: the next person reads "empty" and fills it in —
> which is the behaviour §0.3 rule 1 exists to prevent.**

→ Added `FALSIFICATION_DECLARED_UNFALSIFIABLE`.
⚠️ **The field name is taken from the template's existing wording** (`Why I could not fill this`).
⛔ The first version invented `Why it cannot be stated` in the English edition, **out of step
with the template; corrected. That is exactly what constitution §3.2's new sentence — "field
names are rules too" — governs.**

### Paired fixtures (**six pairs, one per edition, 12 fixture directories**)

| fixture | Must catch | Must not false-alarm |
|---|---|---|
| `conj_status_bad` | `CONJECTURE_STATUS_INVALID` | — |
| `conj_retired_dormant` | — | ⛔ none of `CONJECTURE_STATUS_INVALID` / `FALSIFICATION_UNADJUDICATED` / `EVIDENCE_MISSING_FOR_STATUS` |
| `conj_evidence_missing` | `EVIDENCE_MISSING_FOR_STATUS` | — |
| `conj_citation_ghost` | `CITATION_NOT_IN_LEDGER` | — |
| `conj_citation_ok` | — | ⛔ no `CITATION_NOT_IN_LEDGER` |
| `conj_declared_unfalsifiable` | `FALSIFICATION_DECLARED_UNFALSIFIABLE` | ⛔ no `FALSIFICATION_UNADJUDICATED` |

⚠️ **`conj_retired_dormant` is a regression test, not a feature test** — it guards the
defect 1 + 2 pair.

⚠️ **The four existing `conj_*` fixtures each gained a `NEXT_SESSION_MEMO.md`.**
Reason: once defect 4 was fixed, a fixture holding only the ledger made the citation scan
match nothing → INCOMPLETE. **A fixture with a single file is not a realistic project.**

⚠️ **The English edition's four existing fixtures had no emoji in the state field**
(`| Conjecture |`). The first attempt to add them hit the §0.1 table row instead of the
heading — **caught by running the fixtures, not by reading the diff.**

**Self-test: 18/18 in both editions, exit code 0.**

---

## #4 | 2026-08-19 | A miss in the self-certification sensor, and the `deny` key (decision 2)

### 4a. 🔴 The self-certification sensor returned PASS on a real audit report

**Triggering case (`[measured]`, specimen from another project in live use):**
a cross-model audit of a git wrapper concluded:

| The report's wording | `governance/Audit_Protocol.md` §3 |
|---|---|
| "**extremely high** robustness" | ⛔ bans "extremely" |
| "has **sealed off** most edge failures" | ⛔ bans "airtight"-class claims |
| "**nothing left to fix**" | ⛔ banned; §2.1 uses it verbatim as the ❌ example |
| "works **perfectly**" ×2, "**very robust**" | ⛔ banned |

**And the sensor returned PASS.**

The cause was **not APPRAISAL** (it held three of them) but **`SELF`, which did not cover the
self-reference an audit report actually uses** — "this round", "this audit", "the project".
The co-occurrence therefore never fired.

> ⛔ **Under-reporting is more dangerous than over-reporting: a false alarm gets
> investigated, a miss does not.**

### 4b. ⚠️ But widening `SELF` false-alarms on honest disclosure — so only the WARN branch widened

Measured: "**all** outstanding items from this round are listed in §3, two of which are not
yet **verified**" matches `SELF` + `SCOPE` + `OBJECT`, **and that is an honest disclosure,
not a certification.**
⛔ False-alarming on honest disclosure is precisely what `R-19` guards against —
**it teaches people not to write down what they did not finish.**

→ **Two scopes, ⛔ never merged:**

| Constant | Used by | Meaning |
|---|---|---|
| `SELF` (narrow, unchanged) | **FAIL** branch | "this document claims it verified itself" |
| `SELF_WIDE` (new) | **WARN** branch | "this document praises the thing it is about" |

Also fixed: `APPRAISAL` required `extremely (high|robust)` and **had no `perfect` at all**,
while §3 bans both outright.
⚠️ **The single home for that list is `Audit_Protocol.md` §3 — this regex may cover more,
⛔ never less.**

### 4c. Decision 2: the `deny` key

`framework_config.py` gains `"deny": ["ledgers"]`.
**Constitution §6, general rule 2 (⛔ ledgers and T0 are outside every AI's output area) now
has a mechanical counterpart for the first time.**

- ⚠️ **The two T0 files are deliberately not listed in `deny`** — their home is `t0_docs`
  and the sensor folds them in. ⛔ Restating them would create a second home (§3.2).
- ⚠️ **Only active when `write_scopes` is set.** The sensor reads `git status` and cannot tell
  a human's change from an AI's; enforcing it in a solo project would FAIL on the host
  editing their own ledger.
- ⚠️ **The `_human` exemption count is always printed.** A silent exemption and no exemption
  look identical on screen (the "silent filtering" family).

### 4d. Side fix: `load()` read the wrong project's config

`framework_config.load()` always read `ROOT/governance_config.json`, where `ROOT` derives from
**the sensor file's own location**. Pointing `--root` elsewhere **changed the scan scope but
not the config**, ⛔ silently. **Side effect: fixtures could not test config-dependent
behaviour at all.** Now `load(root)`, passed by `_common.cli()`.

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `selfcert_appraisal` (new) | `UNSUPPORTED_GLOBAL_APPRAISAL` | ⛔ no `UNVERIFIABLE_SELF_CERT` |
| `selfcert_clean` (gained an honest-disclosure line) | — | ⛔ neither code |
| **scope (four, real git repo in the system temp dir)** | `WRITE_TO_DENIED_PATH` ×2 | ⛔ no false alarm when `_human` covers it; none for an in-scope change |

⚠️ **`sensor_scope_and_t0.py` had no self-tests at all before this.**
It reads `git status`, and a nested `.git` makes it refuse to report — **so the test
environment has to live outside this repo**; one is built in the system temp dir and removed
afterwards. Per `R-27`, this section exercises the "write_scopes is set" branch.

⚠️ **Three of the four tests failed on the first attempt**: the base files were not committed,
so `governance/AGENTS.md` and `governance_config.json` counted as changes themselves.
**Caught by the self-test, not by reading the code.**

**Self-test: 23/23 in both editions.**

---

## #5 | 2026-08-19 | Decision 5: the prompt self-containment sensor split into two layers

### 5a. The old version applied the DR-only clause table to every prompt

**Observed (before the fix): all three templates the framework itself ships came out FAIL.**

`prompts/TEMPLATE_decompose.txt` is a **fully self-contained** decomposition prompt whose
opening line reads, verbatim, "⛔ do not search the literature this round" —
**a prompt that forbids literature search cannot and should not contain bilingual retrieval
clauses. It would still FAIL after assembly, forever.**

> 🔴 **And `prompts/README.md` had already written the excuse for that false alarm:**
> "because the template contains `<<<paste block B>>>`" —
> **that reason holds for `TEMPLATE_prior_art.txt` and not for the other two** (they have no
> block placeholder).
>
> **A sensor that alarms on correct text, plus an official note saying "this FAIL is correct".**
> **The second layer is worse than the first: it institutionalises ignoring the sensor.**

**→ Split into two layers:**

| Layer | Checks | Applies to |
|---|---|---|
| ① Self-containment | cross-prompt references, unassembled blocks, prompt pollution | **every prompt** |
| ② DR clause table (8 items) | LANG / VENUE-TYPE / NO-DOI / PASS A / B / title precision / NONE RETRIEVED / OUTPUT CONTRACT | **only `--profile deep-research`** |

⛔ Under `generic` the sensor always prints "DR clause table **not run** — not applicable
(⚠️ not applicable is not a pass)".

### 5b. Three kinds of `<<<…>>>` placeholder; only one is a defect

| Form | Example | Old | Now |
|---|---|---|---|
| Block placeholder | `<<<paste block B>>>` | FAIL | ❌ **FAIL** (`PROMPT_NOT_ASSEMBLED`) |
| **Content slot** | `<<<paste your full idea here>>>` | **FAIL (false alarm)** | ✅ **not a defect** |
| Fill slot | `<<<fill in:…>>>` | FAIL | ⚠️ WARN |

### 5c. 🔴 Quoting a prohibition is not violating it

**Observed:** `TEMPLATE_decompose.txt` contains the line
"⛔ do not write 'to be filled' or 'see below' in the falsification field",
**and the sensor read the embedded "see below" as a cross-file reference.**

> **String matching can tell whether a phrase is present; it cannot tell who is saying it.**
> **The predecessor projects hit this same thing once each on three different sensors.**

→ A prohibition marker (⛔ / must not / do not / forbidden) appearing **before** the phrase on
the same line marks it as quoted.
⛔ **Every exempted line number is printed** — a silent exemption and no exemption look
identical on screen (the "silent filtering" family).

### 5d. The two editions used to be two different sensors

Chinese: CROSSREF + POLLUTION + the 8-item DR clause table (all FAIL level).
English: CROSSREF (including placeholders) + three generic hints (WARN level), **no DR clause
table at all.**
→ Converged onto one design, taking the stronger half of each.

### 5e. The generic hints are calibrated against the framework's own templates

⛔ If an item alarms on a well-written prompt, the pattern is wrong (`R-19`).
⚠️ The Chinese enumeration pattern used to include a bare "list", **which matches prose**
(the adversarial template's "was not listed"), making a prompt with no enumeration requirement
look compliant — removed.
⚠️ The English side had no `answer each`, **which is exactly how the adversarial template is
written** — one hint firing in one edition and not the other **is drift, not a language
difference.** Added.

### 5f. Side fix: the banned-word list had drifted

`TEMPLATE_adversarial.txt` (Chinese) said "very **穩健**" while
`governance/Audit_Protocol.md` §3 says "very **強健**". **Aligned.**

⚠️ **There is a real tension here worth recording:**
`R-24` requires every prompt to be fully self-contained (so a template **must** carry its own
copy of the banned list), while constitution §3.2 requires every rule to have exactly one home.
**The two are mutually exclusive here, and the result of that exclusion is drift.**
⛔ **There is no mechanical defence yet.** This is a pending decision item.

### Paired fixtures (**seven, covering both profiles — constitution §7.1**)

| Fixture | generic | deep-research |
|---|---|---|
| `prompt_crossref` | ❌ `CROSS_PROMPT_REFERENCE` | — |
| `prompt_unassembled` | ❌ `PROMPT_NOT_ASSEMBLED` | — |
| `prompt_clean` | ✅ PASS, ⛔ no DR code | ❌ `DR_CLAUSE_MISSING` (**branch test**) |
| `prompt_quoted_prohibit` | ✅ PASS + exemption must be printed (**regression**) | — |
| `prompt_content_slot` | ✅ PASS (**regression**) | — |

**Both editions: 30/30 self-tests pass.**

### ⚠️ One true positive, left for the host to adjudicate

After the fix, `TEMPLATE_adversarial.txt` has **one remaining WARN in each edition: no
hallucination guardrail found.**
**That is not a false alarm** — the adversarial audit template genuinely carries no
"say so when unsure, do not invent" clause.
⛔ Whether to add one is a content decision; **not taken unilaterally this round.**

---

## #6 | 2026-08-19 | Decision 8 (five rounds late): citation exemption for proposal files; decision 19: hallucination guardrail for the adversarial template

### 6a. Decision 8: `CITATION_NOT_IN_LEDGER` exempts proposal files

**Triggering case: the framework's own process and its own sensor are mutually exclusive.**

The process is "AI proposes → a human adjudicates → a human writes the ledger"
(`governance/AGENTS.md` §5), so during the window between "proposal filed" and "decision made"
**a proposal file necessarily cites IDs that do not exist yet**, and
`CITATION_NOT_IN_LEDGER` necessarily reports FAIL. **Observed: 12 in a single round.**

→ This is exactly the question `profiles/PROFILE_multi_agent.md` §4.3 **G-1b** asks:
**"Can the new rule and some existing rule be violated by the mere act of obeying both?"**
⚠️ **And here the two sides are a process rule and a sensor.**

**Criterion (⛔ structural, not free text):** located under `handoffs/` **and** the filename
contains one of `proposal_markers`. The single home of those markers is `framework_config.py`.

⛔ **The exemption switches off this one check and nothing else. ⛔ Every exempted file is
printed** (`CITATION_CHECK_EXEMPTED`).

⚠️ **Why the criterion cannot be "write a sentence of justification":** a predecessor project's
exemption column asked only for a reason, **so one plausible-sounding sentence silenced the
sensor permanently on a real fabrication while the dashboard stayed green.**
**A free-text reason cannot be checked mechanically.**

### 6b. ⚠️ This item was "adjudicated but not done" for five rounds

**The host adjudicated [A] in work segment three; I did it in segment nine.**
Nothing anywhere showed that it was still outstanding — **because my own governance document
had no pending-decision queue**, which constitution §5.1 requires in so many words, and which
I had read in round one.

→ Created a pending-decision register with a "rounds waited" column, and split
**"adjudicated" from "landed" into two tables** — putting them in one table is precisely why
this item was dropped.

### 6c. Decision 19: hallucination guardrail added to `TEMPLATE_adversarial.txt`

After fix #5, each edition's adversarial template had one WARN left: **no hallucination
guardrail found.** **Not a false alarm** — the template genuinely had no "say so when unsure,
do not invent" clause. The host adjudicated that it be added. Both editions are now
**0 FAIL, 0 WARN.**

The core of what was added: **an auditor inventing a finding is worse than an auditor missing
one** — it sends people to fix a problem that does not exist, and it spends the trust the next
audit needs.

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `conj_citation_ghost` (existing) | `CITATION_NOT_IN_LEDGER` | **guards "the exemption must not be too wide"** |
| `conj_citation_proposal` (new) | `CITATION_CHECK_EXEMPTED` | ⛔ no `CITATION_NOT_IN_LEDGER` |

**Both editions: 31/31 self-tests pass.**

---

## #7 | 2026-08-19 | Decision 12 (model-attribution rewrite) and decision 14 (new reference-integrity sensor)

### 7a. Decision 12: `sensor_model_attribution.py` rewritten end to end

**The old version's problem was not the whitelist; it was the scan scope.**

The old version scanned "every `.md` in the project root". **But the root `.md` files are
templates the framework ships (`README` / `SETUP` / `file_index` …), not AI output — they are
not supposed to carry an author field.** So it needed two hard-coded whitelists (13 + 12
entries, all filenames from another project) to suppress alarms it had created itself, and
**it reported three WARNs on the first run against a clean, brand-new template tree.**

> **That whitelist existed to compensate for a wrong scan scope.**
> **Fix the scope and the whitelist is unnecessary — this version hard-codes zero filenames.**

| | Old | New |
|---|---|---|
| Scan scope | root `.md` + `handoffs/` (hard-coded) | `attribution_globs` (discovery-based; `handoffs/*.md` etc. by default) |
| Hard-coded filenames | **25** | **0** |
| Dangling references | **5 section + 4 file** | **0** |
| "Concrete model" criterion | a list of model names (goes stale) | **structural: does it carry a version digit** |
| Output on a clean template tree | 3 bogus WARNs | 3 **dead-glob** WARNs (a true statement) |

⚠️ **"Concrete model" deliberately avoids enumerating model names** — that is just another
whitelist. The criterion is instead: **a concrete model almost always carries a version digit**
(`opus-5`, `gemini-3.7-flash`, `o4-mini`), **while family names and platform names do not**
(`Claude`, `Gemini`, `Antigravity`). Platform names are handled by a separate **value-domain**
list (⛔ a value domain is not a scan scope, so `R-21` is not violated).

🔴 **`MODEL_UNREADABLE_DECLARED` is the most important item here:**
`policy/MODEL_IDENTITY.md` §3.6 rule 1 says, verbatim, that when the marker is not in visible
context **the only correct output** is `[Model: unreadable — …]`.
⛔ **Judging that FAIL would push the next model back to writing a platform name, and §3.6
rule 2 says that is worse than leaving it blank.**
**Degradation must point towards "I do not know", not towards "a vaguer name".** → WARN, with
a reminder to fill it in.

### 7b. Decision 14: new `sensor_reference_integrity.py`

**The existing `sensor_governance_text.py` only checks whether a section anchor resolves, and
only scans `.md`.** Two gaps had been open the whole time: `.py` file headers were never
scanned, and **whether a cited file exists was never checked at all.**

**Inventory before switching it on: 11 distinct dangling file references across both editions**, of which:

| Source | Count | Nature |
|---|---|---|
| old `sensor_model_attribution.py` | 2 | another project's paths |
| `policy/MODEL_IDENTITY.md` | 3 | other-project paths ×2 + **a file the framework promises but does not ship** |
| format-explanation placeholders | 4 | ⚠️ **not defects** |
| **created by me while rewriting 7a** | 2 | ⚠️ **see below** |

🔴 **Those last two deserve their own line: while rewriting the sensor's file header I quoted
the old whitelist's filenames as examples, and those filenames instantly became new dangling
references.**
**"Do not instantiate a defect while describing it" — the predecessor projects hit this same
mechanism three times; this is the fourth.**
⛔ **Handled as they handled it: reworded into description, no exemption added.**

**Two kinds of non-defect reference, handled differently:**

| Form | Criterion | Handling |
|---|---|---|
| format placeholder `` `<filename>.md` `` | **angle brackets** | ⛔ not checked |
| explicitly not shipped | **an explicit marker on the same line** | ✅ exempted, **but it must be printed** |

⛔ **The exemption criterion is "a marker on the same line", not an exemption list** — the
predecessor projects dodged the first two occurrences by rewording, and on the third the string
was substantive content that could not be reworded, **so they switched to an explicit marker and
required the marker itself to be printed.** This sensor follows that.

**After switching it on: both editions PASS against the real templates** (zh has 1 printed
explicit exemption; en has 0).

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `attrib_missing` / `attrib_vague` / `attrib_platform` | the matching code | — |
| `attrib_clean` | — | ⛔ neither code may appear |
| **`attrib_unreadable`** | `MODEL_UNREADABLE_DECLARED` | ⛔ **must not be judged a defect** |
| `ref_dangling` | `DANGLING_FILE_REF` | — |
| `ref_ok` / `ref_placeholder` | — | ⛔ no `DANGLING_FILE_REF` |
| `ref_not_shipped` | `REF_EXEMPTED_NOT_SHIPPED` | ⛔ no `DANGLING_FILE_REF` |

**Both editions: 40/40 self-tests pass; `run_all_sensors.py` is now 6 sensors, both editions PASS.**

⚠️ **`sensor_reference_integrity.py` takes about 5 seconds on a mounted filesystem** (it walks
the whole project once). It should be far faster locally, **but if the suite ever feels slow to
you, this is the first one to look at.**

---

## #8 | 2026-08-19 | Decision 21: the conjecture sensor now uses the shared `cli` / `emit`

**Triggering case:** `sensor_conjecture_ledger.py` **carried its own `argparse` block and its
own `emit()`**, running in parallel with the ones in `_common.py`. It was the only one of the
six sensors built that way.

**The consequence was not wrong output; it was a rule with two homes:**

| Thing | Home A | Home B |
|---|---|---|
| the `--root` / `--json` interface | `_common.cli()` | this file's own `argparse` |
| exit-code semantics (0 / 1 / 2) | `_common.emit()` (constitution §7.4) | this file's own `emit()` |
| JSON output shape | `_common.emit()` | this file's own `json.dumps` |

⚠️ **This is exactly what constitution §3.2 governs.** The two implementations agree today;
**that does not mean they will agree after the next person edits one of them** — and the time
they diverge, nothing will say so.

### ⛔ My prediction about this item was wrong; recorded here

When requesting the decision I justified it by writing that this file's `emit()` "takes an
**independent `incomplete` boolean**, and an independent boolean can disagree with the findings".
**That turned out to be false: the old code read
`incomplete = incomplete or any(f[0] == "INCOMPLETE" for f in findings)` — it derived the state
from the findings just like the shared one.**

> ⚠️ **A shape that strongly resembles a known failure family is not thereby a member of it.**
> I only read that line just before acting; **had the order been reversed, this log would now
> record a defect that never existed, and it would read perfectly plausibly.**

→ Corrected to the host before the decision was carried out. **The one real reason for this
item is the duplicated home.**

**What changed:**

- Removed this file's `emit()`, its `argparse` block, and `import argparse` / `import json`
  (both dead once the shared helpers are used).
- Now `root, _cfg, as_json, _name = cli("conjecture_ledger")` plus
  `emit(…, findings, stats, as_json, "conjecture_ledger")`.
- ⛔ **No independent `incomplete` argument any more** — INCOMPLETE is derived from the
  findings, by one route only.

**Where the paired fixtures are:** ⚠️ **None added this round, deliberately.**
This is a **behaviour-preserving refactor**; the six existing `conj_*` pairs are its regression
test — **if behaviour had changed, those six would have gone red on the spot.**
⛔ If anyone later changes the exit-code semantics in `_common.emit()`, come back and confirm
those six still hold.

**Carried out under decision 21's condition: "on its own, with no other change in the same batch."
Both editions: 43/43 self-tests pass.**

---

## #9 | 2026-08-19 | Decision 20: three states for an empty scan, and exit-code aggregation

### 9a. 🔴 Exit-code aggregation was swallowing INCOMPLETE

`run_all_sensors.py` used to let **a later result overwrite an earlier one**.
**Measured (reproducible): the exit codes `[2, 1]` aggregated to `1`.**

> **So "one sensor never managed to check at all" was hidden by a FAIL, and once that FAIL was
> fixed the whole suite went green — and nobody ever learned that the other sensor had not run
> a check.**

→ Changed to `worst = max(worst, r.returncode)`. ⚠️ Semantically this relies on `0 < 1 < 2`
**happening** to match severity order; noted on that line, **and if an exit code is ever added
that coincidence breaks.**

### 9b. Decision 20: an empty scan is no longer always just a WARN

Old behaviour: any glob matching zero files → `SCAN_GLOB_MATCHES_NOTHING` (WARN, **exit 0**).

⚠️ **The problem is that "matched zero" means two completely different things:**

| Situation | Meaning | Should the suite change colour |
|---|---|---|
| the directory does not exist yet | this project does not use that area | ⛔ no — a new project would go red on its first run |
| the directory was just created and is empty | same | ⛔ no |
| **the directory holds files of the same extension and the glob matched none** | **the pattern has drifted from reality — this line of defence is spinning freely** | ✅ **yes (INCOMPLETE)** |

> **"Nothing to compare against" and "compared and consistent" look identical on screen**
> (`R-22`, constitution §7.4).

**The criterion took three attempts; all three are kept here:**

| Version | Criterion | Why it was wrong |
|---|---|---|
| 1 | the directory exists → collapse | the framework's own empty `handoffs/` went INCOMPLETE immediately |
| 2 | the directory holds anything → collapse | `scripts/**/*.sh` was flagged in a pure-`.py` project |
| **3 (adopted)** | **files of the same extension exist under the directory and the glob matched none** | — |

⚠️ **Also fixed `_glob_dir()`:** the first version returned the project root for a glob with
**no wildcard** (e.g. `file_index.md`), so **every fixture missing that file counted as a
collapse — 7 self-test regressions on the spot.**
→ It now returns `None` when there is no wildcard (such a glob matching zero files means the
file is absent, not that coverage collapsed).

**Paired fixtures (three, one set per edition):**

| Fixture | Expected |
|---|---|
| directory absent | ⚠️ WARN, exit 0 |
| directory freshly created and empty | ⚠️ WARN, exit 0 |
| directory holds files but none match the glob | ❌ **INCOMPLETE (exit 2)** |

⚠️ **The middle one is the "must not false-alarm" half** — ⛔ without it, the next person will
loosen the criterion back to version 1.

---

## #10 | 2026-08-19 | Decision 17: duplicated long sentences — the real defect was the splitter and the threshold, not the two sentences

### 10a. ⚠️ The premise of the decision was wrong; that comes first

When requesting decision 17 I wrote that "the English edition has two cross-file duplicated long
sentences and the Chinese edition does not."
**That is false: both editions duplicate the same text; the Chinese edition's sensor could not
see it.**

| | Chinese | English |
|---|---|---|
| `MIN_DUP` / `MAX_DUP` | **24 / 80** | **40 / 220** |
| normalised length of that sentence | **21 characters** | **68 characters** |

**The Chinese copy missed its own edition's threshold by three characters**, so "the English
edition is dirtier" was an artefact of measurement.
⛔ **The fact that the two editions used different thresholds was registered nowhere.**

> 🔴 **A weaker sensor reads as a cleaner document.**

### 10b. A character-count threshold is systematically weaker for Chinese → information length

The same content takes roughly a third as many characters in Chinese.
→ `info_len()`: **one CJK character counts as three Latin ones**; both editions unified on
`MIN_DUP, MAX_DUP = 40, 220`.

### 10c. The splitter knew only `。` and newlines → English compared whole lines only

English sentences end in `.`, which was not a break, so **the English edition was in effect
doing whole-line comparison.** The sentence shared by `Audit_Protocol.md` and `HANDOFF.md` was
caught in Chinese and missed in English.

→ "A period followed by whitespace" was added as a break.
⚠️ **The first attempt still missed it**: in `**…unfinished.** "None"…` the period is followed
by `*`, not whitespace.
→ The criterion is now "period + optional closing markers (`**`, quotes, brackets) + whitespace".
`3.2` and `.md` stay intact (inline code spans are stripped first).

**After the fix the English edition caught that sentence immediately — it had always been there,
it just could not be measured.**

### 10d. A header banner is not a rule (⛔ this is not loosening a criterion because it alarmed)

`Claim_Ledger.md` and `Conjecture_Ledger.md` both carry the header line "T1 data class. AI must
not write to this file directly.", so it was reported as one rule with two homes.
**That line is file metadata, not a rule** — every data-class file has to state it.
**Demanding that it appear only once is demanding that it not work.**

⛔ **`R-20` forbids loosening a criterion because it alarmed; what changed here is what the
criterion is applied to**, and the reason is recorded in the source comment.
Still structural, not keyword-based: **a line that is one whole bold span and sits before the
first `## ` heading.**

### 10e. What decision 17 actually landed: `Claim_Ledger.md` §1.1 rule 4 becomes a citation

The content of R-27 / R-28 was written out **twice** — in `governance/RULES.md` and again in
`ledgers/Claim_Ledger.md` (including the `individ-\nual` example). ⚠️ **In both editions.**
→ The ledger now points at `governance/RULES.md` R-27 and R-28, **keeping only the consequence
specific to the ledger** (rewriting the extraction breaks the hash defence).

⛔ **Rewording one of the two copies was rejected** — predecessor incidents I-42 / I-43
explicitly refuse "dodge the duplicate by rewording it".

### 10f. One wrong rule citation fixed along the way

`run_selftest.py` said, in two places per edition, "Per `R-27`: every branch of a branching
sensor needs a self-test."
**`R-27` is the normalisation-order rule, not that requirement**; the home of that requirement
is constitution §7.1.
→ All four occurrences now cite `governance/WORKFLOW_CONSTITUTION.md` §7.1. **This is precisely
the shape `R-16` governs.**

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `gov_dup` (existing) | `DUPLICATE_RULE_TEXT` (whole line identical) | — |
| **`gov_dup_midline` (new)** | `DUPLICATE_RULE_TEXT` (**sentence ending mid-line**) | ⛔ deliberately contains no whole-line duplicate |
| `gov_clean` (**identical header banner added to both files**) | — | ⛔ `DUPLICATE_RULE_TEXT` must not appear |

⚠️ **Here is how that `gov_clean` line was shown to be worth anything:** `strip_banner()` was
temporarily replaced with the identity function and the sensor re-run — **`DUPLICATE_RULE_TEXT`
appeared at once in both editions**; putting it back removed it.
⛔ **A fixture that will always pass once an exemption exists tests nothing.**

**Both editions: 44/44 self-tests pass.**
**Current state: `sensor_governance_text.py` reports 2 WARNs in Chinese and 1 in English —
⚠️ all true positives, see below.**

### ⚠️ Two true positives, left for the host to adjudicate (**not handled unilaterally**)

| # | The duplication | Why I am not deciding it myself |
|---|---|---|
| a | `Audit_Protocol.md` / `HANDOFF.md`: "'None' is not full coverage; it is not having taken stock" (both editions) | **Both sides need it, and each has a different preceding sentence** (one about audit coverage, one about unfinished handoff items). Which side is the home is a content decision |
| b | `Incident_Log.md` / `RULES.md`: the self-certification case (**caught in Chinese only**) | The English edition duplicates it too, but one word differs (`among` vs `in`), so **literal comparison misses it** — ⚠️ exactly the blind spot this sensor declares about itself |

---

## #11 | 2026-08-19 | Decision 18: new `sensor_clause_sync.py` (clause-list synchronisation)

**Triggering case (logged in #5f, where no mechanical defence existed):**
`prompts/TEMPLATE_adversarial.txt` said "very **穩健**" while
`governance/Audit_Protocol.md` §3 says "very **強健**".

**One character, so that prompt's banned list guarded one word fewer, and both documents read
perfectly normally.**
⚠️ **A human found it by comparing character by character — while doing something else.**

### Why that drift is **structural**, not carelessness

| Rule | Requirement |
|---|---|
| `R-24` | every prompt is **fully self-contained** — ⛔ no "as above", no "see earlier" |
| constitution §3.2 | **every rule has exactly one home** |

> 🔴 **The two exclude each other here: self-containment forces you to copy; single-home
> forbids you to copy.**
> **The product is not somebody breaking a rule — it is drift, and drift shows no red light.**

⛔ **This sensor does not resolve that exclusion.** Which file is the home, and whether to copy,
remain human calls. It answers one mechanical question:
**"is the copy still identical to the home today?"**

### ⚠️ Where I departed from decision 18's wording: set equality, not identical order

Decision 18 said "compare … **verbatim identical**".
**Observed: both editions' banned lists have the same contents in a different order** (the
English home puts `airtight` fourth; the template puts it last).

> **Order carries no meaning in this list. FAILing on a meaningless difference is exactly the
> false alarm `R-19` warns about — and it would have happened on day one.**

→ **What was relaxed is the order, ⛔ not the characters.** Each item is still compared
character for character; "very 穩健" and "very 強健" are two different items and set equality
fails on the spot.
⚠️ **This is written into a fixture:** `sync_ok` (same set, different order) **must not
false-alarm** — ⛔ without it, the next person will "correct" the criterion back to identical
order, and that FAILs on both editions as they stand.

### ⛔ Zero hard-coded copy filenames

| | How |
|---|---|
| home | `synced_lists[].home` — **a pointer**, ⛔ not a scan scope, so `R-21` is not violated |
| copies | **discovered** via `marker`: any marked line inside the scan scope is a copy |
| scan scope | `sync_scan_globs` (⛔ **excludes `scripts/`** — the changelog and the source **describe** this list, and a description is not a copy) |

**Adding a new template needs no change here; the one you forget to update reports itself.**

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `sync_drift` | `SYNC_LIST_DRIFT` (one character) | — |
| **`sync_ok`** | — | ⛔ **a different order must not alarm** (none of `SYNC_LIST_DRIFT` / `SYNC_HOME_MISSING` / `SYNC_NO_COPY`) |
| `sync_home_missing` | `SYNC_HOME_MISSING` (**INCOMPLETE, ⛔ not PASS**) | — |

⚠️ **`SYNC_NO_COPY` is a WARN rather than silence:** a home with a list and no copy anywhere
means **this entry is currently watching nothing** — the same shape as a dead glob.

**Both editions: 47/47 self-tests pass; `run_all_sensors.py` is now 7 sensors, both PASS.**

---

## #12 | 2026-08-20 | A sentence that names its home is not a second home

**Triggering case (measured this round, ⚠️ caused by me):**
To remove a rule that appeared in three files, two of them were rewritten as
"**see constitution §3.4; ⛔ not restated here**".
**That citation was then word-for-word identical in two files, so the sensor reported it as a
duplicate in turn.**

> 🔴 **But it is the opposite: a sentence naming the home ⛔ cannot be a second home —
> it is the very mechanism that stops one from existing.**

⛔ **This is not "loosening the criterion because it false-alarmed" (`R-20`); it corrects what
the criterion is applied to** — the same correction as the header banner in #10d.

**Criterion (structural, ⛔ not keyword-based):** the sentence contains a `§` section number or
an `R-nn` rule id → it is a pointer and does not take part in the comparison.

⚠️ **Stated cost:** a genuinely duplicated rule that also names a section will be missed.
**This sensor chooses to miss that rather than alarm on every citation** (`R-19`: a sensor that
fires on correct text gets switched off).

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `gov_dup` / `gov_dup_midline` (existing) | `DUPLICATE_RULE_TEXT` (**neither contains `§`**) | — |
| `gov_clean` (**one identical pure citation added to both files**) | — | ⛔ no `DUPLICATE_RULE_TEXT` |

⚠️ **How that fixture was shown to be worth anything:** `POINTER` was replaced with a
never-matching pattern and the sensor re-run — **`DUPLICATE_RULE_TEXT` appeared at once**;
putting it back removed it.
⛔ **A fixture that always passes once an exemption exists tests nothing.**

⚠️ **The first draft of the fixture cited `§3.4`, while the fixture's own constitution has only
`§1`** — **so `SECTION_REF_UNRESOLVED` false-alarmed and the self-test stopped it.**
**The self-test caught it, not me.**

**Both editions: 47/47 self-tests pass; `run_all_sensors.py` exit 0 in both.**

---

## #13 | 2026-08-20 | Self-containment: this folder must work when copied out on its own

🔴 **Triggering case (measured this round, ⚠️ caused by me and found by me):**
the first version of the architecture figure lived in `docs/` at the **repository root**, and
each edition's README referenced it as `../docs/framework.svg`.

> **Inside the repository it looked perfectly fine.**
> ⛔ **But the way users actually work is to copy `Spark2Groundwork_<zh|en>/` wholesale into
> their own project — and once copied the figure is gone, while the README still cites it
> confidently.**

⚠️ **The shape of this class of dependency: it never errors in place; it breaks only in someone
else's hands.** **And "it works here" and "it works there" look identical on my screen.**

**What changed:** `sensor_reference_integrity.py` gained `REF_ESCAPES_EDITION` (FAIL) — any
`](../…)`, `src="../…"` or `href="../…"` is treated as climbing out of the folder.

⚠️ **The criterion is the path, ⛔ not intent.**
**`cd "$(dirname "$0")/../.."` inside `scripts/harness/*.sh` is unaffected** — that is a shell
working-directory computation, not a document reference; **the two have different shapes, so no
exemption list is needed to tell them apart.**

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| `ref_escapes` | `REF_ESCAPES_EDITION` | — |
| `ref_selfcontained` | — | ⛔ no `REF_ESCAPES_EDITION` / `DANGLING_FILE_REF` |

**Both editions: 49/49 self-tests pass; `run_all_sensors.py` exit 0 in both.**

⚠️ **Two related fixes in the same round (⛔ not sensor changes; recorded here for context):**
1. Each edition's README gained a licence notice — **`LICENSE` only existed at the repository
   root, so a copied-out edition had none**;
2. the root `.gitattributes` gained `*.command` — **I had added it to the two edition-level
   files in an earlier round and missed the root one.**

---

## #14 | 2026-08-20 | 🔴 The whole harness could not run on Traditional-Chinese Windows

**Triggering case: the host ran the first pre-release check on their own Windows machine.**

```
UnicodeEncodeError: 'cp950' codec can't encode character '✅'
```

### Why

**Python's default output encoding on Windows is the system ANSI code page** (`cp950` there),
and **every message this framework prints** contains `✅` / `⚠️` / `⛔`.
**So a sensor dies at the first symbol it prints.**

⚠️ **Until now the framework only worked on Windows because the `.bat` files started with
`chcp 65001`** — and when v1.2.0 turned those `.bat` files into thin shells,
**that line was not carried over.**
🔴 **And any user who runs `python scripts\harness\…` directly rather than pressing a button
hits it anyway.**
**⛔ Relying on the console code page was never a fix; it was a step that happened not to be
taken.**

### 🔴 How it failed matters more than that it failed

| What the screen said | What was true |
|---|---|
| **SUMMARY: FAIL (7 sensors run)** | **Two sensors never finished running** |
| every sensor printed its stats, but those two had **no `Result:` line** | they died mid-way |

**An uncaught Python exception always exits `1`, and 1 means "found a defect".**
⛔ **So "the sensor is broken" was presented as "the document has a problem" — exactly the
confusion `R-22` and constitution §7.4 forbid, occurring inside the runner itself.**

⚠️ **The old crash check, `if returncode not in (0,1,2)`, is structurally incapable of catching
a Python crash**, **because a Python crash always exits 1.**

### What changed

| # | Fix |
|---|---|
| 1 | **`_common._force_utf8()`** — reconfigures `stdout`/`stderr` to UTF-8 (`errors="replace"`, so ⛔ the worst case is a printed `?`, not a dead process) and calls `SetConsoleOutputCP(65001)` on Windows. **It runs on import of `_common`**, so every sensor is covered |
| 2 | The seven runners and tools, plus `sensor_prompt_self_contained.py` (which does not go through `_common.cli`), each call it explicitly |
| 3 | Every `subprocess.run(..., text=True)` now pins `encoding="utf-8"` **and passes `PYTHONIOENCODING=utf-8` to the child** — ⚠️ setting only one half turns the crash into a `UnicodeDecodeError` |
| 4 | **The crash criterion is now structural: non-zero exit + `Traceback (most recent call last)` on stderr = a crash → INCOMPLETE** |
| 5 | The `.bat` shells regained `chcp 65001` — ⚠️ **not to prevent the crash (1 and 2 do that), but so the console does not render mojibake** |

### Paired fixtures

| Fixture | Must catch | Must not false-alarm |
|---|---|---|
| **`_selftest_crasher.py` (new)** | a crash is judged INCOMPLETE, ⛔ not FAIL | — |
| the existing 49 | — | ⛔ must still all pass under `PYTHONIOENCODING=cp950` |

⛔ **The crash test deliberately uses a fake sensor that always crashes, ⛔ not a real one** —
**a real sensor gets fixed one day, and what this test checks is the runner's behaviour.**

### ⚠️ How to reproduce

```
PYTHONIOENCODING=cp950 python3 scripts/harness/run_all_sensors.py
PYTHONIOENCODING=cp950 python3 scripts/harness/run_selftest.py
```

**Before:** every sensor raised `UnicodeEncodeError`; the summary said FAIL.
**After:** both editions exit 0; self-tests **50/50**.

🔴 **This is the most expensive lesson in this framework so far:**
**the whole system was green in my environment for twenty-odd work sessions, and it had never
once started on the user's machine.**
**⛔ "It works here" and "it works there" look identical on my screen.**
