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
⚠️ **(That section moved to `governance/CLAIM_LEDGER_SPEC.md` §1.1 in v1.4.1. ⛔ This line keeps its original wording because it records what was true then.)**

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

⚠️ **(§1.1 moved to `governance/CLAIM_LEDGER_SPEC.md` in v1.4.1. ⛔ The heading keeps its original wording.)**

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

## #15 | 2026-08-26 | 🔴 Short-form section citations were checked by nobody

### 1. Triggering cases (**three, ⛔ all found by hand**)

| Citation | Where | Shape |
|---|---|---|
| `constitution §5.11` | both editions' `sensor_model_attribution.py` header | 🔴 **a defect description that instantiated the defect it described** — ⚠️ two lines above, the same comment explains why the filenames were deliberately not written out |
| `constitution §8.1` | both editions' `Audit_Protocol.md` | the constitution's `## 8.` has ⛔ no `### 8.1`; the citer added a subsection number from memory |
| `constitution §5.8` | Chinese `MODEL_IDENTITY.md` | a T0 rewrite removed constitution §5, ⛔ and nobody went back to the file citing it |

🔴 **What the three share is not carelessness. It is that this written form was checked by nobody.**

### 2. Why nothing caught them (**two independent holes**)

| Hole | Detail |
|---|---|
| **Form** | `REF` only parses the long `` `<file>.md` §N `` form. ⛔ The framework itself writes the short form "constitution §N" in **58 places** |
| **Scope** | This sensor only scanned `governance_globs`. ⛔ **`scripts/harness/*.py` was entirely outside it** — and the `§5.11` case lived in a `.py` header |

⚠️ **`sensor_reference_integrity` exists precisely because `.py` headers were never scanned.**
🔴 **⛔ It fixed *file* references and not *section* references. The same hole was half-fixed,
and the half that was fixed made it look closed.**

### 3. What changed

1. **New config key `section_ref_aliases`**: `{anchor word: target file}`. ⛔ **Not hard-coded** —
   `R-21` forbids a whitelist as the definition of scan scope, and a downstream project's short
   name will not be this one's.
2. **The section-citation check now runs over `code_globs + launcher_globs + governance_globs`**
   (the same scope as `sensor_reference_integrity`).
3. **An anchor is configured but its target file is absent → `ALIAS_TARGET_MISSING` (INCOMPLETE)**,
   ⛔ not a silent skip (`R-33`).
4. **A "section citations checked" statistic was added** — ⛔ silence is not a pass.

### 4. 🔴 The first version of the criterion was too broad — and it caught that itself

**On the first run after the scope was widened, `HANDOFF.md` was reported as having two `## 3.`
headings.** One of them is a line inside the fenced block showing what the five required sections
look like — ⛔ **sample text is not a heading.**

⚠️ **The defect was already in the long-form check**; it never fired only because nothing inside
`governance_globs` happened to cite `HANDOFF.md §3`.
**Widening the scope ⛔ did not create it — it made it visible.**

**Fix: fenced blocks are stripped. ⛔ Not an exemption list (`R-20` / `R-21`)** — this corrects
what the criterion is applied to.
**Stated cost: a real heading placed inside a fenced block becomes invisible. ⛔ Nobody writes that.**

### 5. ⚠️ The sensors caught the maintainer twice, on the spot

**Writing the new comments, the long form was spelled with a real filename as an example**, so:
`[FAIL] DANGLING_FILE_REF: … references `<file>.md`, which is not in the project` — **four places.**
🔴 **The "instantiate the defect while describing it" family again — ⛔ inside the very paragraph
explaining that family.** All four were changed to the angle-bracket placeholder form.

### 6. Paired fixtures (four; ⛔ two of them are the "must not false-alarm" half)

| fixture | Expected |
|---|---|
| `secref_alias_bad/` | dangling short form → **WARN** |
| `secref_alias_ok/` | resolvable short form → ⛔ **must not false-alarm** |
| `secref_py/` | the citation lives in a `.py` header → **WARN** (proves the scope reaches code) |
| `secref_fence/` | a fake heading inside a fenced block → ⛔ **must not false-alarm** (the paired sample for this fix) |

**Self-tests 50 → 54. Both editions: `run_all_sensors.py` exit 0, `run_selftest.py` 54/54.**

### 7. ⛔ What this entry does not claim

- ⛔ **It does not claim other short names are checked.** Only one anchor ("constitution") is
  configured. **`R-35`: that is the result of taking stock — ⚠️ and I did not take stock of
  whether a third citation form exists in the framework.**
- ⛔ **It does not claim the citation points at the right content.** It answers only
  "that section exists and is unique".

---

---

## #16 | 2026-08-26 | An empty `corpus_md/` was reported as "could not check"

### 1. Triggering case

**The framework began shipping an empty `corpus_md/` folder** so that a new user can see where
extractions are meant to go.
🔴 **Every fresh project then printed INCOMPLETE on its very first `run_all_sensors.py`.**

⚠️ **⛔ A first run that cries wolf is exactly what teaches people to ignore the output.**

### 2. Why this is the criterion's fault, ⛔ not the folder's

**The old criterion knew two states:**

```
no directory                → not applicable, skip silently
directory but no manifest   → INCOMPLETE
```

**⛔ It had no third state: a directory that holds no extractions yet.**
**With nothing to protect, there is no such thing as "could not protect it".**

⚠️ **The same shape as an earlier defect**: `tool_pdf_to_md.py` created its output directory
before checking whether there were any PDFs to put in it — **both report "not applicable"
as "at risk".**

### 3. The fix

**The criterion now keys on whether extractions exist, ⛔ not on whether the directory does:**

| State | Disposition |
|---|---|
| No directory | Not applicable, skip silently |
| **Directory, no extractions** | **WARN `CORPUS_EMPTY`** (new) |
| Extractions, no manifest | INCOMPLETE (unchanged) |

⛔ **A structural correction, not an exemption list (`R-20` / `R-21`).**
⚠️ **`CORPUS_EMPTY` is a WARN rather than silence**: nothing of the user's has been checked yet,
**and that is worth saying — it just should not turn the whole run INCOMPLETE.**

### 4. Related: why the note file in there is a `.txt`

**Every `.md` in `corpus_md/` is treated as text extracted from a PDF.**
⛔ **So a `.md` note placed there would be reported as an untracked extraction.**
**The shipped note is therefore a `.txt`, ⛔ with the reason written inside it.**

### 5. Paired fixtures

| fixture | Expected |
|---|---|
| `corpus_empty/` | empty extraction folder → **WARN**, ⛔ **`CORPUS_MANIFEST_MISSING` must not appear** |
| `corpus_unmanifested/` | extractions but no manifest → **INCOMPLETE** (proves the old behaviour survived) |

**Self-tests 54 → 56.**

---

## #17 | 2026-08-27 | 🔴 An upgrade deleted a project's accumulated rules — **while the manual encouraged accumulating them**

**Triggering case (⛔ measured, not inferred from reading the code):**
a clean project was built locally, an `R-36` was added to `governance/RULES.md` and a
project family to `Incident_Log.md`, then `upgrade.py apply governance` was run:

| | before | after |
|---|---|---|
| `R-36` | 1 | 🔴 **0** |
| the project family | 1 | 🔴 **0** |

**Mechanism: `upgrade.py` does `shutil.rmtree` + `copytree` for a directory.**

🔴 **The serious part: the framework had already solved this once, and only halfway.**
`governance/Incident_Log.md` §1 says verbatim why project incidents moved to `MY_INCIDENTS.md`:
"a framework file has to be replaceable wholesale, ⛔ and overwriting a file that holds your
incident records deletes them."
**`RULES.md`, in the same folder, ⛔ never got that treatment.**

⚠️ **And `PROFILE_solo.md` §5.4 said "after a year your `governance/RULES.md` will not look
like anyone else's — that is the point", and the next paragraph listed what an upgrade will
not overwrite — ⛔ and `RULES.md` was not on that list.**
**Every word was true; together they led the reader to the opposite conclusion.**

**What was fixed:** added `my/MY_RULES.md` (`P-xx` numbering, the framework's rules copied
verbatim into §1), `sensor_my_rules.py`, `tool_sync_my_rules.py`; constitution §6.4
"a file may have exactly one owner".

**Paired samples:** six `my_rules_case()` entries in `run_selftest.py`.

⚠️ **The first finding this sensor produced was its own parser defect** — the insertion-point
comment at the end of §1 of `MY_RULES.md` joined the last rule's body. **The second is worth
more: the first override criterion was "there is text after the marker", so
`**R-19** [project override] <the original clause>` passed — ⛔ because that text is the clause
itself, not a reason. The criterion is now "the marker must be on a line of its own", with a
regression test.**

---

## #18 | 2026-08-27 | 🔴 `deny` had never once been in effect in a solo project — and solo is the default

**Triggering case:** the old `sensor_scope_and_t0.py` skipped block ② entirely when
`write_scopes` was empty, **⛔ `deny` included. And `PROFILE_solo.md` §6 tells a solo project
to leave it empty.**

🔴 **Consequence: constitution §6.3's "the mechanical counterpart is `deny`; clear it and you
have full authorisation" made no difference either way in a solo project** — **the sentence
described a mechanism that was not running.**

⚠️ **The second half of the same round: `t0_docs` was folded into `denied` in code, so no
configuration could switch T0 protection off, while the comment in `framework_config.py` said
"the two T0 files are deliberately absent here; a governance agent may maintain them".**
🔴 **Two comments by the same author with opposite intent: the absence of T0 from `deny` is a
gap, and a gap carries no intent.**

**What was fixed:**
(1) The two T0 files are listed verbatim in the `deny` default; the code ⛔ appends nothing.
(2) The permission check no longer depends on `write_scopes`; a solo project gets a WARN with
names (`DENIED_PATH_TOUCHED_UNATTRIBUTED`).
⚠️ **⛔ Not a FAIL: the principal editing their own ledger is normal (`R-19`); ⛔ and not
silence either (`R-22`).**
(3) An unrecognised key in `governance_config.json` is now a FAIL with a `difflib` suggestion.

**Paired samples:** four `scope_case()` entries (T0 in / not in deny; solo editing a ledger /
an ordinary file) plus three `config_key_case()` entries.

⚠️ **`config_key_case()`'s criterion was corrected by the self-test itself: the first version
judged by exit code, and the fixture has no git repo, so the two valid-key cases exit 2
(`SCOPE_UNCHECKABLE`) — ⛔ which is correct behaviour. The criterion is now "did the output
report an unknown key".**

**Self-tests 57 → 69.**

---

## #19 | 2026-08-27 | 🔴 A code path broken since v1.0.0 that had never once run

**Triggering case:** the principal ran `run_all_sensors.py` on their own machine
(Traditional-Chinese Windows) and `sensor_scope_and_t0.py` **crashed in both editions**:

```
AttributeError: 'NoneType' object has no attribute 'strip'
  top.stdout.strip()
```

**`subprocess.run(..., capture_output=True, text=True)` returned `returncode == 0`
⛔ with `stdout` set to `None`.**

🔴 **The defect had been there since v1.0.0. It surfaced for the first time in v1.4.1
⛔ because the old code skipped block ② entirely when `write_scopes` was empty — and
`PROFILE_solo.md` tells a solo project to leave it empty.**
**⇒ That code had never run on a real user's machine.**
⚠️ **`#18` (making `deny` effective in a solo project) ⛔ did not cause the crash;
it is what made it visible.**

⚠️ **The framework handled it correctly: `run_all_sensors.py` read the crash as
`SENSOR_CRASHED` → INCOMPLETE, and the summary was INCOMPLETE — ⛔ not PASS and ⛔ not FAIL.
`R-22` did its job.**

**Two fixes:**

**(1) When `stdout` is not a string, report INCOMPLETE and print the facts (type, stderr).**
⛔ **⚠️ This deliberately does ⛔ not claim to know the cause** — per `R-34`, the authority
on a limit is a measurement, ⛔ not a guess.
🔴 **It also blocks a worse failure: falling through turns `pathlib.Path("")` into the
current directory, so the sensor would report "the project sits inside another repository" —
a diagnosis that reads plausibly and is wrong.**

**(2) When the project is a subdirectory of a repo, ⛔ stop refusing to report; narrow the
report to that subtree instead.**
⚠️ **The old code always went INCOMPLETE. This framework's own repository has exactly that
shape (each edition is a subdirectory), and so does a user who drops the project into an
existing notes repo — ⛔ a light that is always on (`R-19`).**
⚠️ **`git status --porcelain` prints paths relative to the repository root, ⛔ not to the
directory named by `-C` — strip the prefix, ⛔ do not assume.**

**Paired samples:**

| Sample | Must |
|---|---|
| `git_blind_case()`: a fake `git` on PATH that exits 0 and prints nothing | INCOMPLETE, ⛔ no crash, ⛔ no "another repository" misdiagnosis |
| `subrepo_case()`: the project is a repo subdirectory, one change inside and one outside | **the denied change inside is seen, ⛔ the file outside is not** |

🔴 **The second half of `subrepo_case()` is the point: ⛔ doing only the first half is
"judging the wrong repo", which is exactly what the old refusal was protecting against.
⛔ When you soften a remedy, keep what it was actually protecting.**

**Self-tests 69 → 71.**

### 🔴 Follow-up (2026-08-27, after the principal ran the diagnostic): **the cause is established, ⛔ no longer "unknown"**

```
python -c "...capture_output=True, text=True..."
→ Exception in thread Thread-1 (_readerthread):
  UnicodeDecodeError: 'cp950' codec can't decode byte 0x94 in position 16
→ 0 None ''
```

**Python 3.14.2, Traditional-Chinese Windows. With `text=True` and ⛔ no `encoding`,
Python decodes git's UTF-8 output using the locale encoding (`cp950`).**
**`輔` in the path is `E8 BC 94` in UTF-8 — ⛔ byte 16 is `0x94`, which cp950 cannot decode.**

🔴 **⛔ The part worth remembering is not that it fails, but how:**
**the decode happens in `subprocess`'s reader thread. ⚠️ That thread dies, the exception
⛔ never reaches the main thread, and `communicate()` returns `None` — so the caller sees
"exit 0 and no output".**
**⛔ The standard library itself turned an error into a silent empty value.**

### ⚠️ The same fix, applied to only half the code

**`run()` in `checkpoint.py` and `review_changes.py` says
`encoding="utf-8", errors="replace"` verbatim — ⛔ and `sensor_scope_and_t0.py` did not.**
🔴 **The fix already existed in two programs in the same folder; it was never carried to the third.**

⚠️ **It is also the `R-34` shape: `_common._force_utf8()` fixes *what we print out*,
⛔ and it read as "encoding has been dealt with". ⛔ A true fix whose scope does not cover
the other channel.** **What it does ⛔ not cover is now written in its own docstring.**

### The paired sample that was added

**`subprocess_encoding_case()`: walks `scripts/harness/*.py` with `ast`; any
`subprocess.run` carrying `text=`/`universal_newlines=` and ⛔ no `encoding=` is a FAIL,
named as `file:line`.**

⚠️ **⛔ It is a static check and runs nothing. Why: the defect only occurs on a machine with
a non-UTF-8 locale, 🔴 and a criterion that cannot fire on my machine is not a criterion.**

**Measured: with `encoding` removed, the self-test reported
`❌ subprocess.run calls that would decode with the locale: sensor_scope_and_t0.py:83`.**

**Self-tests 71 → 72.**


---

## #20 | 2026-08-27 | 🔴 The framework displaced an index the user already had

**Triggering case (reported by the principal): a project adopted v1.3.0 and then stopped
maintaining its own file index — its `file_index.md` holds ⛔ not one research-related entry.**

**Mechanism: `file_index.md` began life in a predecessor project as the table for
"research plan versions and supporting documents". When it was refined into the framework its
contents became entirely the framework's own, ⛔ and the name did not change.**
🔴 **So a new user sees a file called "file index" and assumes it is theirs — and then either
registers their documents in it (lost at the next upgrade) or stops registering anything
(what actually happened).**

⚠️ **That project's own handoff packet carries the corroborating sentence: they deliberately
did ⛔ not register the tool they wrote in `file_index.md`, because "an upgrade overwrites it,
and registering there puts the pointer somewhere that disappears".**
**⇒ ⛔ The framework did not merely neglect the user's index; it displaced a mechanism that
already existed.**

**Added: `tool_my_index.py` (generator) and `sensor_my_index.py` (watcher).**

### Three design decisions

**(1) The criterion is "everything the framework does ⛔ not own", ⛔ never a list of what to
include.**
🔴 **A list of what to include is a whitelist (`R-21`): users keep inventing new folders.**
⚠️ **A predecessor project's generator had exactly that shape, and its author wrote the
sentence themselves: "a hand-written index misses files, ⛔ and a generator misses directories."**
**The single home for the framework's names is the replaceable list in `upgrade.py` — the tool
`import`s it ⛔ rather than keeping a second copy.**

**(2) The file list is generated; the descriptions are AI-maintained; the two live apart.**
⚠️ **The principal's practice: the descriptions in a research index have always been maintained
by the research AI. ⛔ And code cannot extract anything meaningful from `.docx` / `.pdf` / `.xlsx`.**
🔴 **Files with no description are ⛔ not hidden; they get their own section** —
**an index that looks complete while missing half the files is worse than no index.**

**(3) The sensor does ⛔ not reimplement generation; it calls `tool_my_index.render()` and
compares verbatim.**
⚠️ **If two generators differed anywhere, "is it stale" would say stale forever, ⛔ while the
real cause is that the two programs are not the same.**

### 🔴 The tool caught another defect on its very first run

**It lists what the framework does not own, and `docs/` (the two figures) and the six launcher
buttons appeared in that list.**
🔴 **⇒ They have always been the framework's, ⛔ and they were not on `upgrade.py`'s
replaceable list — meaning the seven figure-layout fixes made in v1.3.0 ⛔ reach no existing
project.** **`docs` and the six launchers are now on the list.**

⚠️ **`.gitignore` and `.gitattributes` are deliberately ⛔ left off** — they have mixed
ownership (the framework supplies defaults, the user adds to them), and per constitution §6.4
replacing them wholesale would delete the user's lines.
**⛔ The known cost is recorded in `upgrade.py`'s comments.**

### Paired samples (**six**)

| Sample | Must |
|---|---|
| The index has never been generated | **INCOMPLETE**, ⛔ not PASS |
| A freshly generated index | ⛔ must not false-alarm |
| 🔴 **The user creates a `deepresearch/` of their own** | **that file must appear in the index** (⛔ proving it is not a whitelist) |
| A file added after generation | **FAIL `MY_INDEX_STALE`** |
| A description pointing at a missing file | **FAIL `INDEX_NOTE_DANGLING`** |
| A broken notes file | **INCOMPLETE**, ⛔ never "there are no descriptions" |

⚠️ **The third sample's criterion was corrected by the self-test itself: the first version
checked "the sensor's output", ⛔ and the sensor prints counts, not the file list. It now
checks the generated index file.**
🔴 **⛔ I had aimed the criterion at the wrong object, ⚠️ and the self-test caught it.**

**Self-tests 72 → 78. Sensors 8 → 9.**

---

## #21 | 2026-08-28 | 🔴 A sensor was reporting "your operating system is different"

**Triggering case: the moment v1.4.1 was released. The principal ran step 2 and
`sensor_my_index.py` reported `MY_INDEX_STALE`. Running `tool_my_index.py` by hand turned it green.**

**⚠️ The principal's report is worth quoting: "I don't know whether this causes a problem,
so I'm telling you anyway."**
🔴 **That sentence is why this entry exists — a false alarm pushed him into an action he was
not sure about, in the middle of a release.**

### Cause

**The old line was `sorted(root.rglob("*"))` — ⛔ that sorts `Path` objects.**
**⚠️ `WindowsPath` comparison casefolds first; `PosixPath` ⛔ does not.**

| | Linux | Windows |
|---|---|---|
| `PROJECT.md` vs `corpus/` | `P`(0x50) < `c`(0x63) → **before** | casefolded, `project` > `corpus` → **after** |

🔴 **The index was generated on Linux and shipped with v1.4.1, so it was bound to report
stale on Windows.**
**⛔ What it reported was ⛔ not "the index is stale" but "your operating system is not the one
that generated it".**

⚠️ **This is the textbook shape of `R-19`: a criterion that fires on a correct state.**
**⛔ And its real consequence already happened — the principal worked around it and then was
unsure whether he had done something wrong.**

### What was fixed

**The sort key is now the relative posix string. ⛔ Never the `Path` object.**
**Python's `str` ordering is code-point ordering on both platforms — ⛔ no platform difference.**

### Paired sample

**`index_order_case()`: the fixture holds `Zed.md` and `apple/x.md`
(`Z` 0x5A < `a` 0x61, ⛔ while casefolding puts `apple` first), and asserts that `Zed.md`
appears before `apple/x.md` in the index.**

⚠️ **⛔ Be honest about its reach: it only lights up on a case-insensitive filesystem.**
**⛔ On Linux the old and new code agree, so it cannot fire there.**
🔴 **It is kept because the release procedure runs the self-test on Windows as step one —
⚠️ which is the only place this defect ever shows.**

⚠️ **⛔ This does not claim the same shape has been swept for elsewhere** —
**"calling `sorted()` on a type whose ordering is platform-dependent" ⛔ has not been inventoried.**

**Self-tests 78 → 79.**
## #22 | 2026-09-01 | A root glob escaped to the parent, and foreign-platform launchers were treated as required

**Triggering case:** Project D runs on Windows and legitimately has no `.command`, but
`_glob_dir()` resolved root `*.command` to the project's parent. A `.command` in a neighbouring
project then manufactured `COVERAGE_COLLAPSE`, reporting "could not check" for a valid
platform-specific installation.

**Change:** an empty glob prefix now resolves explicitly to project root.
`active_launcher_globs()` requires only the native launcher kind, while still scanning every
foreign launcher that is actually present. The reference-integrity and governance-text sensors
share that criterion.

**Paired fixtures:** `root_glob_platform_case()` in `run_selftest.py`: a neighbouring
`.command` must not contaminate a root glob; Windows without `.command` and macOS without `.bat`
must not false-alarm. Native execution of the macOS launcher still awaits a macOS review;
these fixtures test scan semantics only.

---

## #23 | 2026-09-01 | The collapse fallback forgot to exclude `_upgrade/`

**Triggering case:** Claude's v1.4.4 review found that `resolve_globs()` excluded `_upgrade/`,
but after a glob matched zero files, `dead_glob_findings()` performed a second, unfiltered
`rglob()` for the same suffix. A downloaded `.txt` or `.command` could therefore turn a valid
dead root glob into `COVERAGE_COLLAPSE`.

**Change:** the fallback recursive check now uses the same `excluded_dirs` criterion as the
first glob expansion.

**Paired fixtures:** `.txt` and `.command` files under `_upgrade/` must not manufacture
collapse; a real `.txt` under a non-excluded child must still produce `COVERAGE_COLLAPSE`.
The full suite rises from 86 to 95 tests; two directly cover this criterion, while the other
seven cover the upgrade and CLI corrections from the same review.

---

## #24 | 2026-09-01 | The seventh path sort, and a count that could not see it

**Trigger:** v1.4.1's `tool_my_index.py` built the index with `sorted(root.rglob("*"))`,
sorting `Path` objects — and `WindowsPath` comparison casefolds while `PosixPath` does not.
The principal hit `MY_INDEX_STALE` on his very first run, having done nothing wrong.
v1.4.2 fixed that one site.

**⚠️ What this entry records is not that fix but the count itself:** the conclusion at the
time was written as "six other sites, output order only". Re-counting this round gives
**seven** — `framework_config.py::resolve_globs()`'s `sorted(set(files))` was never
included, and it decides the scan order of every sensor.
🔴 **A count written into prose is itself a drifting number (`R-16`), and it drifted.**

**Fix:** all seven now pass `key=lambda p: p.as_posix()`. ⛔ They are still not defects
today — none of their output is stored and compared later. The reason for the change is
that "the same project prints a different order on two machines" is itself enough to make
any future comparison unreliable.

**Paired samples:** `path_sort_case()` in `run_selftest.py`. A **static** AST check of the
same shape as `subprocess_encoding_case()`: a `sorted(...)` whose first argument contains
`.glob()`/`.rglob()` and whose call has no `key=` is a violation. ⚠️ **Why static: the
difference only shows on Windows, and a criterion that cannot fire on this machine is not
a criterion.** The other half of the pair feeds the original v1.4.1 line straight to the
criterion and confirms it catches it — ⛔ a criterion that is permanently green protects
nothing.

⛔ **Known gap of this criterion:** it only recognises "glob then sort in place", ⛔ not
storing the paths in a variable and sorting later. Written down here rather than left blank.

Self-tests go from 95 to 97.

---

## #25 | 2026-09-01 | The tenth sensor: a half-finished upgrade produces no error

**Trigger:** Project D's `policy/` sat at v1.3.0 while `governance/`, `profiles/` and
`docs/` were already v1.4.2. **All nine of that project's sensors were green and every
self-test passed.** 🔴 **⛔ Not one of them was looking at "are these packages on the same
version", so the state was silent** — ⚠️ **it took an outside audit to find it, ⛔ and not
every project gets an audit.**

**Added:** `sensor_version_consistency.py` (the tenth).
`VERSION_MISMATCH` FAIL (packages report different versions) / `VERSION_UNREADABLE`
INCOMPLETE (package present, marker unreadable) / `PACKAGE_ABSENT` WARN (this project does
not have that package).

⚠️ **The three levels are deliberately separate:** "you are missing a package" and "two of
your packages disagree" are different things with different fixes; 🔴 **and "could not
read" must ⛔ never be folded into "consistent" — that is the one state this framework
cannot afford to dilute.**

⛔ **What it does not claim:** a version marker only answers "what does this folder call
itself". **The same Project D had the other half too: `prompts/_VERSION` read v1.4.2 while
`_COMMON_BLOCKS.md` was still v1.3.0 content. ⇒ This sensor catches "the labels disagree",
⛔ not "the labels agree and the contents differ"** — the required action for that is
`upgrade.py diff`. **Written down here rather than left blank.**

**Paired samples (five):** six packages on one version must not false-alarm / `policy` one
version behind must be caught (= Project D's actual state) / a missing package can only be
a WARN / an unreadable `_VERSION` can only be INCOMPLETE /
🔴 **`framework_config.version_packages` must be the same set of names as
`upgrade.FRAMEWORK_DIRS`**. ⚠️ **That last one is the watcher for the two copies: when they
drift you get a package the upgrader can replace but the sensor never compares — ⛔ which
is exactly what `docs/` was between v1.3.0 and v1.4.0.**

⛔ **The other half is deliberately kept out of the harness:** the repository-root
`CITATION.cff` and `CHANGELOG.md`, and the "two language editions" layout, do not exist in
a downstream project. **That half lives in `本地工作區/維護工具/check_release_versions.py`,
a release gate.** ⚠️ **Reason: a sensor that is permanently INCOMPLETE on the user's
machine teaches people to ignore INCOMPLETE (`R-19`).**

Sensors 9 → 10. Self-tests 97 → 102.

---

## #26 | 2026-09-01 | When the framework revises an existing rule, an existing project has no prescribed action

**Trigger:** v1.4.4 added a line to `R-34` per adjudication `B-4`: "the scope of an
authoritative statement is itself something to check". **⚠️ This is the first time this
framework has revised a rule that had already shipped.**

🔴 **And then this surfaced: `my/MY_RULES.md` §1 is a verbatim copy, `sensor_my_rules.py`
compares by rule number, ⛔ and `tool_sync_my_rules.py` only ever appended missing entries,
deliberately never overwriting an existing one.**
⇒ **That one line would hand every existing project a `RULE_TEXT_DRIFT` FAIL, ⛔ whose only
way out was asking a person to paste the new text in.**
⚠️ **"Ask a person to paste it" is exactly what that tool exists to avoid** — the
clause-sync sensor once caught `extremely` retyped as `extremely high`.

**⛔ The old reasoning was not wrong:** "a tool that overwrites automatically would quietly
erase a deliberate change."
🔴 **But the framework's own criterion already requires that a deliberate change be marked
`[project override]` with a reason, or it is a `RULE_TEXT_DRIFT` FAIL. ⇒ An unmarked entry
is a purely derived copy.**

**Fix:** `tool_sync_my_rules.py` gains `--adopt`: entries whose body differs ⛔ and that
carry no override marker are replaced with the framework wording, printing "old first line →
new first line" for each. ⛔ **Marked entries are always skipped and printed.**
⚠️ **`--adopt` is an explicit flag and ⛔ not the default: a deliberate change whose marker
was forgotten looks exactly like a plain stale copy from here. ⇒ The checkpoint is its
recovery path.**

**Refactor in the same round:** the override criterion moved into
`sensor_my_rules.is_override()`; sensor and tool now read the same function.
🔴 **⛔ If the two ever differ you get "the sensor calls it an override while the tool
overwrites it"** — ⚠️ **which is the axis-two shape this very sensor exists to watch,
happening to itself (constitution §3.2).**

**Paired samples (four):** unmarked + `--adopt` must adopt the framework wording / 🔴 **marked
+ `--adopt` must not change one character, and must print the skip** / without `--adopt`
nothing is written ⛔ and it does not go silent / `--adopt` is idempotent.

⚠️ **Worth recording about the process: on their first run, samples two and three both went
red — ⛔ and the tool was right. The fixture was missing a rule, so "something to append" and
"something drifted" were mixed together, and the `file did not change` assertion could not
tell which caused what.**
🔴 **The fix was to the fixture, ⛔ not to loosen the assertion.**

Self-tests 102 → 106.

---

## #27 | 2026-09-01 | What a folder becomes in an existing project after it retires

**`policy/` was folded into `governance/` in v1.4.4.**

🔴 **⛔ What is worth recording is not "four files moved" but where that name stands afterwards:**
**it came off `FRAMEWORK_DIRS`. ⇒ In an existing project, `policy/` now has**
**⛔ nothing that will replace it, ⛔ no sensor that looks at it, ⛔ and nothing that mentions it.**
⚠️ **Its contents stay frozen at the version it retired in, and it still looks like a framework folder.**

**⛔ The upgrader does not delete a user's files (constitution §6.3), ⚠️ but it must say so** —
🔴 **an orphan folder nobody knows about is exactly a stale framework document.**

**Added:** `RETIRED_DIRS` in `upgrade.py` (`dirname → (retired in, where the contents went)`).
`check`, `diff` and **every successful `apply`** list the orphans that still exist;
`apply policy` returns a message that says so, ⛔ not the generic "not a framework item".

⚠️ **Why `apply` prints it too:** 🔴 **the notice only exists in the new code, ⛔ and the user
runs `diff` with the old copy they already have** — **⇒ the earliest moment they can see it is
the instant `scripts` is replaced.** ⛔ **Printing it only on `check`/`diff` leaves anyone
upgrading in order silent for a whole round.**

**Paired samples (four):** a project that still has `policy/` must get it listed / 🔴 **a clean
new project ⛔ must get no retirement notice** (otherwise it is a permanent red light) / an empty
orphan is still listed (the criterion is "the folder exists", ⛔ not "it has anything in it") /
🔴 **`RETIRED_DIRS` and `FRAMEWORK_DIRS` must ⛔ never overlap** — **a name that is both
"replaceable" and "retired" makes the verdict depend on code order.**

**End-to-end check:** an existing project was built from the real `v1.4.2` tag, seeded with
`P-01`, a project incident, `my/tools/mine.py` and a filled `TEMPLATE_decompose.txt`, then
upgraded package by package. `prompts` was blocked by the target-only check as designed; after
the file was moved to `FIRST_IDEA.md` it succeeded; all four project-owned items survived;
`policy/` was named and ⛔ not deleted; the end state is 10 sensors PASS and 110/110 self-tests.

---

## #28 | 2026-09-02 | Only one of three protections actually existed

**An outside review (Codex, Windows) raised six findings against v1.4.4, three of them
release-blocking. ⛔ All three were in the same round's work.**

### 🔴 `F-03`: `--adopt`'s three layers were, in fact, one

**The header claimed "explicit flag + preview before writing + recoverable checkpoint". Measured:**

| Claim | Fact |
|---|---|
| "prints old → new **before** replacing" | ⛔ `write_text()` ran **before** both `print`s |
| "the checkpoint holds it" | ⛔ **an unconditional string**; the test project had no `.git` and it printed this anyway |
| the preview shows what changed | 🔴 **`R-34`'s old and new first lines are identical** — every change is on line two or later |

⚠️ **The third is the one worth recording: `R-34` is the first rule this framework has ever
revised after shipping, which makes it the first real use of `--adopt`.**
**⇒ At that exact moment the preview printed two identical lines. ⛔ Not merely unhelpful —
it told the user nothing had changed.**

**Fix (principal's ruling, 2026-09-02: "have `--adopt` create and verify a checkpoint itself;
if that fails, do not write"):**

🔴 **The criterion is ⛔ NOT "`checkpoint.py` exited 0"** — **measured, it also returns 0 when
there is nothing to commit.**
⚠️ **Nor a byte comparison against `git show HEAD:<path>`: the project may sit in a repo
subdirectory (different path base), and Windows `core.autocrlf` makes blob and working file
differ byte for byte — ⛔ that would call a healthy project unrecoverable.**
→ **Use git's own semantics instead: `rev-parse --git-dir` → `rev-parse --verify HEAD`
→ `ls-files --error-unmatch` (⛔ an untracked file is invisible to `git diff`)
→ `diff --quiet HEAD -- <rel>`.**
**⚠️ The last two together cover both "dirty tree (just committed)" and "clean tree (the
original was already in HEAD)".**

⚠️ **The gate covers overwriting writes only, ⛔ not pure appends** — **the ruling authorises
`--adopt` word for word; ⛔ extending it to appending missing entries would be adding to the
ruling (`CM-34`), and an append deletes nothing.**

**The preview is now a `difflib` line diff (adjudication `A4a: A`), capped at 8 lines per rule
with the line-count change printed.** 🔴 **If the criterion claims a drift while the line diff
is empty ⇒ non-zero exit, ⛔ no write** — **both cannot be true at once.**

### `F-04`: a string sort standing in for SemVer (adjudication `A4b: B`)

**Measured: `sorted({'v1.9.0','v1.10.0'})[-1]` → `v1.9.0`.**
⚠️ **The sensor still reports the mismatch correctly, ⛔ but told the user to move up to the
older version.** 🔴 **The deeper reason: this sensor cannot see `_upgrade/`, ⛔ so it has no way
to know the target version** — that is answered by the upgrade source (`R-34`).
**⇒ `newest` removed; the message now points at `upgrade.py diff`.**

### `F-07`: factoring out the shared criterion ⛔ did not remove the disagreement

**`is_override()` returns `(marker present, reason long enough)`, ⛔ and the tool read only `[0]`.**
⇒ A rule marked as an override with no reason was described by the tool as "marked",
🔴 **while `sensor_my_rules.py` was reporting `OVERRIDE_WITHOUT_REASON` FAIL against it.**
⚠️ **⛔ The behaviour is unchanged (a marker means hands off, which is right); what changed is
what the sentence says.**

### Paired samples

**`adopt_gate_case()`, ten rows**, replacing the previous `sync_adopt_case()`:
no Git / Git present / marked override with a reason / zero change must create no checkpoint /
without `--adopt` no write but no silence / the preview must print real diff lines and the line
count / 🔴 **a clean working tree must pass** / 🔴 **a project in a repo subdirectory** /
🔴 **an untracked file must be refused** / 🔴 **a marker with no reason must say the sensor
will FAIL**. **The last four were added here, ⛔ they were not in the original matrix.**

**`version_consistency_case()` gains two rows:** `v1.9.0` alongside `v1.10.0` must report the
mismatch, and the message must name ⛔ no target version.

Self-tests 110 → 120.

---

## #29 | 2026-09-02 | A program signed a person's name, and had been doing so since v1.4.1

🔴 **`v1.4.3` was never released.** Pre-release review found five defects in it, three of them
red; the principal ruled the entire `--adopt` write path back out and the rest ships as `v1.4.4`.

### 🔴 The worst one was ⛔ not newly introduced

**Since v1.4.1, `upgrade.py` has called `checkpoint.py --root <root>` with ⛔ no `--mode`.**
**`checkpoint.py` defaults to `human`, and human mode unconditionally runs `git tag -f reviewed`
and prints "human review point: I have looked at this".**

**⇒ The full chain, reproduced on the `v1.4.2` tag:**

```
① the user pressed "snapshot"                    reviewed = 15fe2c4
② an AI wrote into ledgers/Claim_Ledger.md and saved with --mode ai
   → review_changes showed that entry                       ✅ visible
③ the user upgraded the framework: upgrade.py apply
   → "human review point: I have looked at this"
   → review_changes: ⛔ the ledger entry was gone
```

⚠️ **The consequence is ⛔ not "a tag moved"; it is that "not yet reviewed" was emptied:**
🔴 **an entry an AI wrote into the claim ledger, which no person had reviewed, was marked
"I have looked at this" and dropped off the pending list because the user upgraded.**
**⛔ `reviewed` is the only mechanical carrier of this framework's claim that a person is the
only adjudicator.**

**Fix: `checkpoint.py` gains a third identity, `tool` (requiring `--tool-id` and `--operation`).**
🔴 **Neither `ai` nor `tool` may ⛔ move `reviewed`, and neither may print the human-review banner.**
`upgrade.py` now passes `--mode tool --tool-id upgrade --operation apply-<target>` explicitly.

⛔ **Why a tool must not use `ai` mode:** `ai` requires `--role` and a concrete `--model`,
**and a local tool is ⛔ none of `VALID_ROLES` and has no model** — ⚠️ **making it use `ai` means
making it invent a model, ⛔ the very thing `MODEL_IDENTITY.md` exists to forbid.**

⚠️ **Known cost: `--mode` still defaults to `human`.** Making it mandatory would immediately
break older projects' `.bat`/`.command`, ⇒ deferred to v1.5.0 alongside the launchers.
⚠️ **Second known cost: `checkpoint.py` runs `git add -A`, ⇒ a tool-made restore point commits
whatever half-finished edits the user has open.** ⛔ For a restore point that is correct (the
whole tree comes back), **but it changes the granularity of their history; ⚠️ at least the
message now says a tool did it.**

🔴 **A tag that was already moved does not move back on its own** — `SETUP.md` gains a section
on how to check it and how to reset it.

**Paired samples (`reviewed_tag_case`, 9):** for both `tool` and `ai`, "no reviewed before → none
after" and "an existing reviewed points to exactly the same commit", each plus "⛔ must not print
the human-review banner"; human mode must still move it (⛔ that distinction is deliberate and must
not be switched off with the rest); `tool` without its identity arguments must be refused;
🔴 **`CP-12` checks `upgrade.py`'s call string for `--mode tool` directly — ⛔ because the shipped
defect lives there, not in anything newly added.**

### `--adopt` ruled back out

**Three defects: it wrote the file before printing the "preview"; it claimed "the checkpoint
holds it" unconditionally (the test project had no `.git` at all); and it still wrote when the
checkpoint program had returned 1 and printed "nothing was written".**
⚠️ **The root of the third: "⛔ not only the exit code" had been implemented as "⛔ not the exit
code at all".**

**⇒ The principal ruled the whole write path out. ⛔ This tool now does two things: append
missing entries, and report drift line by line.**
🔴 **What was kept is the difference display** — **with no tool doing it for you, that difference
tells you which lines to paste by hand; ⚠️ it is more useful than it was before.**

**The `R-34` revision stays** (the principal: the project is small now, so fix the rule while it
is cheap). ⇒ **Existing projects will see one `RULE_TEXT_DRIFT`; the required action is a manual
paste, and `SETUP.md` spells out the four steps.**

Self-tests 120 → 128.

### The six findings that sent `H-006` back (Codex, independent review on Windows)

**⚠️ The core `tool`-mode fix holds (Codex re-ran the same end-to-end chain on Windows and
`reviewed` stayed put), ⛔ and the same round found six things, three of them release blockers.**

#### 🔴 `R-H006-03`　A human checkpoint reported success when the tag could not be created

**The exit code of `git tag -f reviewed` had never been checked.**
**Codex's fault injection: with a `reviewed/child` tag already present, Git's ref namespace can
no longer hold `reviewed`, and `git tag -f` returns 128 — ⛔ while this program printed
"reviewed baseline moved to the latest checkpoint" and exited 0.**
🔴 **⇒ The user presses "I have looked at this", the screen says done, ⛔ and the tag does not
exist at all.**

**Fix:** check the exit code, **then read `reviewed` back and compare it against `HEAD`**; if any
step fails, exit 2 and say plainly "the commit was made, ⛔ and the tag did not move".
⚠️ **The post-condition is ⛔ not "the commit succeeded"; it is "`reviewed` points at the
current HEAD".**
**Paired sample `CP-14` (4 checks): non-zero exit / ⛔ no "baseline moved" banner / it must say
the tag did not move / the commit itself is still there.**

#### 🔴 `R-H006-02`　The upgrade saved a restore point the official recovery path cannot see

**`upgrade.py`'s completion message told the user to recover overwritten hand edits with
review-changes; ⛔ but `review_changes.py`'s baseline is fixed at `reviewed`, and `tool` mode
deliberately never moves `reviewed`.**
**Codex's counterexample: the same file, `git diff reviewed` 0 lines, `git diff HEAD` 193 lines.**
🔴 **⇒ The pre-image really was still there, ⛔ and the official interface could not see it. This
regression was introduced by this round's own fix.**

**Fix (minimal, truth first):** before overwriting, read the checkpoint's commit id back and print
it as a **receipt**, with `git diff <receipt> --` and `git checkout <receipt> --`; and say plainly
that review-changes cannot see it, and why.
🔴 **⛔ No read, no overwrite** — **a restore point that cannot say where it is is not a restore
point.** The id is also written to `git-checkpoint.log`.
⚠️ **The cost: it hands git commands to a user this framework assumes will not use git.**
**⇒ Whether to build a dedicated receipt architecture (a persistent ref / `--base` / a `restore`
command) is a red-level mechanism choice; it is registered for adjudication ⛔ and the maintainer
does not settle it alone.**

**Paired samples:** `CP-15` (3 checks on the message and the ordering of the gate) plus 2 new
behavioural checks in `upgrade_target_only_case` — **with no git, wholesale replacement must exit
2 and overwrite nothing; once git is there the same command must succeed, and a real commit id
and recovery command must appear on screen.**

#### 🔴 `R-H006-04`　The diagnosis for existing projects missed the most common case

**It only taught the user to check whether `reviewed` pointed at `snapshot …`.**
⚠️ **⛔ But when the working tree is clean at upgrade time — the common case — the old upgrader
moved the tag onto an existing `auto:` commit.**
🔴 **Worse: `auto:` is both a result of the defect and a result of the normal flow** (pressing
"snapshot" after the AI finishes lands the tag there legitimately) — **⛔ the two look identical,
⇒ the message prefix cannot be the criterion.**

**Fix: `SETUP.md` now has three steps.** ① look at the commit kind (all four cases listed, and it
says outright that `auto:` is ⛔ not evidence); ② read the `mode=human` timestamps in
`git-checkpoint.log` against what the user remembers, **and state that Git ⛔ keeps no reflog for
a tag like this, so nobody hunts for something that does not exist**; ③ when neither step can
tell, ⛔ **do not guess and do not reset** — drop back to a commit you are certain about and read
forward. **⛔ Not with the review-changes button — that button's baseline is the very thing under
suspicion.**

#### `R-H006-05`　The flag was withdrawn; the instructions were not

**`--adopt` had been removed from argparse, ⛔ and the completion message in both `upgrade.py`
editions and the docstring in both `sensor_my_rules.py` editions still told the user to add it.**
⚠️ **The paired sample at the time, `SYNC-07`, proved "the program refuses it" — ⛔ which is a
different statement from "nobody is told to use it".**

**Fix:** all three sites cleared. **New static scan `SYNC-08`:** it reads `SETUP.md`,
`README.md`, `INITIALIZE_PROMPT.md` and every `.py` under harness, and FAILs on any withdrawn
flag that appears in a paragraph without a `[withdrawn]` marker. ⛔ **No word whitelist**
("used to", "briefly", ...) — **a criterion like that is bypassed by rephrasing.**
⚠️ **The scan has its own counter-sample: an unmarked fake instruction must be caught, ⛔ or
"scanned, all clear" and "the scan is empty" look the same.**

#### `R-H006-06`　The version claim, and bilingual quality

**`tool_sync_my_rules.py` said the `--adopt` version "would have been v1.4.4" — ⛔ wrong, it was
`v1.4.3`.** ⚠️ **Root: a global v1.4.3 → v1.4.4 replace overwrote the special-case sentence I had
written minutes earlier.**

**The English `reviewed_tag_case` in `run_selftest.py` was a machine copy of the Chinese one** —
🔴 **⛔ the third English test I have shipped that way. ⚠️ Tests passing ⛔ is not the English
interface being finished.** The fix is always to rewrite the English, ⛔ never to loosen an
assertion.

#### `R-H006-01`　Colliding adjudication ids (maintainer process, ⛔ no file in this repo)

**The principal typed `A4a` and the maintainer had filed it as `A-4-a`, ⇒ an independent reviewer
searched every record and concluded "the ruling cannot be traced", ⛔ when the ruling was in that
same file.** ⚠️ **One id, two referents — ⛔ and a permanent record cannot be matched up from
memory.** **The fix is on the maintainer side: adjudication ids are now permanently unique and
append-only, ⛔ no longer borrowed from section numbers that get rewritten.**

Self-tests 128 → 139.

## #30 | 2026-09-02 | A commit id was called a receipt without proving it contained the file

**Triggering case (Codex, Windows):** an existing same-path framework file was ignored by Git
and then hand-edited. The checkpoint exited 0 and `HEAD` existed, but its tree did not contain
that file. `upgrade.py apply docs` replaced it anyway and claimed the whole project had been
saved. Measured result: `UPGRADE_EXIT=0`, `RECEIPT_HAS_HAND_EDIT_PATH=False`,
`MANUAL_MARKER_SURVIVES=False`.

🔴 **Root cause:** the program proved only that a checkpoint commit existed. Ignore rules,
`assume-unchanged`, and `skip-worktree` can make that commit differ from the working file about
to be deleted. **A commit id is not a restore receipt until the pre-image is proved present.**

**Fix, authorised by principal ruling `D-20260902-06`:** v1.4.4 now has a complete
upgrade-specific receipt path.

- Before replacement, every existing non-transient file at a path the new package will
  overwrite must be tracked, have a normal blob in the checkpoint tree and index, and hash to
  that blob through Git's own attribute/EOL filters. Any missing or mismatching path is named;
  exit 2; zero replacement.
- A receipt manifest records the operation, target, checkpoint, prior `reviewed`, every saved
  path/blob/mode, and exact transient omissions. Its authoritative copy is embedded in an
  annotated Git object under `refs/spark2groundwork/restore/<receipt>`; a readable JSON mirror
  lives at the path returned by `git rev-parse --git-path spark2groundwork/receipts`.
  The ref pins both checkpoint and manifest; altering the JSON mirror is detected.
- `upgrade.py receipts`, `receipt-diff <receipt|latest> [path]`, and
  `restore <receipt|latest> <path>` expose recovery without raw Git commands. Restore is one
  regular file at a time, makes and verifies its own undo receipt first, writes only the
  worktree, and never moves `reviewed`.
- When the downloaded v1.4.4 upgrader targets an older project, `apply` uses the checkpoint
  program from that same download. Pairing the new receipt contract with an old checkpoint CLI
  would otherwise fail before `scripts/` could bootstrap itself.
- Receipts are not deleted automatically in v1.4.4. Cross-tool receipt reuse and cleanup policy
  remain v1.5.0 work. The guarantee is Git restore semantics, ⛔ not original bytes.

**Paired samples `UPG-REC-03`–`UPG-REC-12`:** ignored content, both index-hiding flags,
durable ref/manifest listing, tracked hand edits, diff/restore plus undo receipt, stable
`reviewed`, path escape, missing-current refusal, CRLF normalisation, exact transient scope,
target-only empty directories, manifest tampering, and the downloaded-checkpoint bootstrap.
**Self-tests 139 → 149.**

### `A-20260902-11` / rulings 48 and 54–57 (Claude, 2026-09-02)

#### 🔴 Line endings and hashes: three correct components that together guarantee a false FAIL

| Component | Correct on its own? |
|---|---|
| `tool_pdf_to_md.py` writes extracts with `write_text(..., encoding="utf-8")` | ⚠️ **Emits CRLF on Windows**, and `md_sha256` records the hash of those bytes |
| `.gitattributes` carries `*.md text eol=lf` | ✅ Correct |
| `sensor_claim_ledger.py` re-hashes every round and FAILs on a mismatch | ✅ Correct |

🔴 **⇒ On the next clean checkout (a clone onto a second machine / `git checkout` / the recovery
steps in `SETUP.md` §9) the working tree becomes LF, every hash mismatches, and
`CORPUS_MD_MODIFIED` fires on every file — ⛔ with not one character actually changed.**
⚠️ **The failure direction is a false positive, exactly what `R-19` says teaches people to
ignore a sensor.**
⛔ **This defect is live in v1.4.1 and v1.4.2 right now** — **⚠️ it has not fired only because
Project D's extracts were produced on Linux and written straight in.**

**Fix:** both editions of `tool_pdf_to_md.py` now pass `newline="\n"` when writing the extract
and the manifest. ⚠️ **A project that has already run the extractor must run it once more**
(manifest and files then become LF together, ⇒ self-consistent).

**Paired samples (three, static):** the criterion is a deliberate **over-approximation** —
**if a module computes hashes at all (`import hashlib`), every `write_text` in it must pass
`newline=`.** (1) scan the whole harness and print the denominator; (2) **the criterion must
catch a planted violation** (⛔ or it merely prints green forever); (3) 🔴 **a module that does
⛔ not hash must ⛔ not be flagged** — ⚠️ **otherwise the next person is forced to add `newline=`
to dozens of fixture writes, and a parameter added only to silence a warning turns the
criterion itself into noise.**

⛔ **Known gap, written down rather than left blank: if the module that writes and the module
that hashes are two different files, this check misses it.** ⚠️ **No such split exists in the
framework today, ⛔ and that is the current state, not a guarantee.**

#### Ruling 48 (B-3): print a protection that was always there ⛔ and invisible

**`sensor_claim_ledger.py` re-hashes every extract on every run, ⛔ and its stats line was an
empty `{}`.**
🔴 **⇒ Two different people, seven days apart, reached the same conclusion: the v1.3.0 auditor
could not find "which sensor compares the manifest", and on 2026-09-02 Project D's user wrote
the same sentence again. ⛔ It had been there the whole time.**

**Fix:** the stats line now carries "hashes compared file by file: N".
⚠️ **It prints 0 when the corpus is empty rather than omitting the line** — `R-35`: an absence
must be the result of counting.

#### Rulings 54–57: failure families ⑨ and ⑩, and two new variants of ①

| | Content |
|---|---|
| **①(d)** | **Measuring a proxy and then treating it as the fact** — ⚠️ **the proxy is usually correct in itself; ⛔ it is simply answering a different question**, ⇒ it neither errors nor looks suspicious |
| **①(e)** | **Reading a statement that is true within a scope as if it were universal** (⚠️ the same root as the clause added to `R-34` in this release) |
| **⑨** | **The batch edit succeeded, ⛔ and what it did was not what I wanted.** 🔴 **⛔ Reading the diff does not catch this** — a diff says "this block was added", ⛔ never "this block should not have been" |
| **⑩** | **A constant tuned for one environment, copied verbatim into another.** 🔴 **Both sides are textually identical ⇒ every "are the two editions consistent?" check reports consistent — "consistent" is its disguise** |

⚠️ **⑨ and ⑩ both carry `[framework's own]`: they happened while maintaining this framework,
⛔ they are not somebody else's incidents.**

Self-tests 149 → 152.

#### Ruling `D-20260902-C25`: family ⑪ and four concrete cases

**⑪ Two writers share one identifier space, ⛔ and to each of them the allocation looks
successful.**
🔴 **⛔ Unlike family ②, this is not one fact copied into several records — two distinct new
things claim the same unique name.**
⚠️ **Measured three times in one day. ⛔ And "re-read before allocating" does not stop it —
all three were preceded by a re-read.** **⇒ The remedy is to split the space by allocator.**

🔴 **It holds for downstream research projects too: `M-xx` in `Claim_Ledger.md` and `C-xx` in
`Conjecture_Ledger.md` are identifier spaces appended to by several agents in parallel** —
⚠️ **two agents allocating `M-36` in the same round would go entirely unnoticed today.**

**Four concrete cases added to §2.2** (all specimens of existing families): an identifier rule
illustrated with an example indistinguishable from a real identifier (⑧); the sentence
illustrating drifting numbers drifting itself (②⑶); one field of a tool's output used to answer
a different question (①⑷); "it was blocked" read as "there is a check" (①⑷).

**§3's "AI (generator)" row gains:** treating a criterion set for its own recommendations as an
obligation on the principal.

---

### `D-20260902-X12`/`-X13`: restore peer and edition gate (Codex author)

- Apply and restore share one compatible-peer resolver: first the `checkpoint.py` beside the
  running `upgrade.py`, then a project copy. Candidates are checked by reading an exact tool-API
  marker, never by execution. If neither matches, the operation writes nothing and asks for the
  complete package in the same edition and version.
- The promise is narrowed to a project-local durable receipt: the private ref pins objects in
  this Git repository, but an ordinary clone or working-file backup does not carry it automatically.
- Before any checkpoint, receipt, or replacement, apply compares edition fingerprints. Each
  language's three existing launchers may form a Windows-only, macOS-only, or dual-platform
  signature. Cross-edition, mixed, and incomplete signatures are rejected. A formal edition
  field is deferred to v1.5.0.
- 🔴 **A refusal now names the launchers it actually saw. Triggering case (pre-release review,
  2026-09-03):** the decision reads only those twelve framework names and ⛔ not who put them
  there, so **a legitimate Chinese project that owns a file called `snapshot.bat` is read as
  "mixed" and the whole upgrade is refused** (measured: `(None, 'mixed')`). ⛔ The old message
  said only that the edition could not be proved and asked for a fresh download — ⚠️ but the
  download was never the problem, **so the user re-downloads forever and the cause never
  appears.** The message now lists what each side showed, with the edition of each name.
  ⚠️ **⛔ Not one character of the decision changed:** the new inventory helper runs only on the
  failure path, 🔴 **so how a refusal explains itself is separate from what it decides.**
  ⚠️ The old sentence "unrelated project `.bat`/`.command` files are ignored" was an unscoped
  statement about a scoped mechanism (`R-34`'s new clause); all three copies — this note, the
  self-test message, and the release notes — now state the real scope.

**Six self-tests added:** six valid signatures, **differently named** unrelated launchers, four
uncertain states with zero writes, post-bootstrap restore with an undo receipt,
missing-compatible-peer refusal without running the old program, and **a colliding name being
named in the refusal**, and **a file inside the exclude list that does exist ⛔ must not be
called missing**. **Self-tests 152 → 159.**

- 🔴 **The index tool called a file inside the exclude list "does not exist".**
  **Triggering case (Project D, 2026-09-02):** `archive/` sits in `my_index_exclude`, so a
  retired file that really exists printed under `INDEX_NOTE_DANGLING` as "moved or renamed".
  🔴 **⛔ Acting on that message (deleting the note) does not fail ⇒ ⛔ nobody ever finds out
  it lied.** ⚠️ The old line `dangling = sorted(k for k in notes if k not in set(files))` only
  asked whether the scan had seen it and ⛔ never looked at the disk. It now calls `exists()`
  before saying something is missing, and the two cases carry different codes: really gone →
  `INDEX_NOTE_DANGLING` (FAIL); **present but excluded → `INDEX_NOTE_EXCLUDED` (WARN).**
  ⚠️ **⛔ `archive/` was not moved out of the exclude list** — widening a scan to fix a wrong
  message puts the cost in the wrong place, as the reporter also argued.
- **One sentence in constitution §6.1 contradicted general rule 2 in the same section and §6.3.**
  It read "⛔ **In every situation**, `ledgers/` are in no AI's output area", while nine lines
  below it said "that is a default, ⛔ not a prohibition — see §6.3", and §6.3 said the user may
  authorise anything, with `deny` as its mechanical counterpart. 🔴 **All three in one T0
  document.** Now stated as a default governed by `deny`, with the triggering case recorded.
  ⚠️ **⛔ The other half is unresolved: a project's ruling on a framework clause still has
  nowhere to live that an upgrade will not overwrite ⇒ v1.5.0.**

---
