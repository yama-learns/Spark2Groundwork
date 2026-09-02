# Working Rules

**Tier: T1 — spec class.**
**Numbering: permanent `R-xx` IDs, append-only, never reused. Repealed rules change state; rows are not deleted or renumbered.**

> ⚠️ **Why permanent IDs rather than section numbers:**
> **A number that drifts makes every citation to it half-wrong at once, and nothing errors.**
> A predecessor project inserted a clause and turned §5.11 into §5.12,
> and had to annotate "old citations still valid".
> **A clause's identity comes from its ID, not its position.**

---

## A. Academic integrity

**Single home: `governance/AGENTS.md` §3** (T0). ⛔ The text is not restated here —
**T0 outranks this file; a second copy here would only create drift.**
⚠️ **The four rows below are pointers. ⛔ They must not be collapsed into `R-01–R-04`** —
**a range cannot carry the mapping (see below: 3 and 4 have no ID; 5 and 6 are R-03 / R-04).**

**R-01** Do not fabricate. → `AGENTS.md` §3 item **1**.
**R-02** "Not found" is not "does not exist". → `AGENTS.md` §3 item **2**.
**R-03** Do not delete a refuted record. → `AGENTS.md` §3 item **5**.
**R-04** Cite only descriptive findings. → `AGENTS.md` §3 item **6**.

⚠️ **`AGENTS.md` §3 items 3 and 4 (single sample → general conclusion; no significant
difference → the two are the same) ⛔ carry no `R-xx`.**
**That is the result of taking stock, ⛔ not an omission (`R-35`)** — they have lived in T0 only
since v1.0.0. **⛔ Do not add IDs just to make the list look even**: doing so would tie the
number of bottom lines to the `R-xx` series from then on.

## B. Verification and the limits of competence

**R-05** Every sentence carrying a number or an assertion must carry a verification-level tag (`AGENTS.md` §2.1).
**R-06** ⛔ `[checked]`-level material must not be used to judge a claim false, nor to build a new hypothesis.
**R-07** ⛔ No assertion from an external AI tool may be cited without verification against the original.
**R-08** Verdict vocabulary may only be used when quoting a ledger's recorded state, with the ID.
**R-09** Where the system provides an authoritative field (model, timestamp), read it verbatim. ⛔ Never infer it from context.
**R-34** 🔴 **The authority on what you can do is your tool list — ⛔ not one failure's error message.**
　　**Before declaring "I cannot do X", list which tools you checked and why each one cannot.**
　　⚠️ **What this blocks is not guessing wrong. It is turning one channel's limit into a
　　universal statement about yourself:** "this script's urllib is blocked by a proxy" is true;
　　"I have no network access" is false. **They are not the same sentence.**
　　⚠️ **Triggering cases (three, across two predecessor projects and this framework's own maintenance):**
　　① `rm` failed → asserted "this platform has no delete permission" → **an entire
　　　 cross-platform division of labour was built on a false premise**, while
　　　 **the authorising tool was in the tool list the whole time.** The user caught it.
　　② A sensor printed "this environment **may** have no network" → turned into the assertion
　　　 "the sandbox has no network" and written into a delivery note. The user asked
　　　 "did you check your own tools again?" — another channel reached the service directly.
　　③ Filesystem `unlink` was denied → declared "my tools cannot delete files" → **written into
　　　 three deliverables**, while a second, permission-gated channel went unenumerated.
　　　 The user caught it a third time.
　　⚠️ **The scope of an authoritative statement is itself something to check (`B-4`, 2026-09-01):**
　　"this tool cannot do X" is true; it does ⛔ not follow that "no tool can do X".
　　🔴 **Triggering case ④: an auditor's system prompt stated plainly that `device_bash`
　　　 cannot delete files, and that sentence was true; he therefore did not check further,
　　　 and read a bounded statement as a universal one about his own capability.**
　　⛔ **The first three are "did not check the tool list"; the fourth is "checked one
　　　 authoritative statement, and it covered only one channel"** —
　　　 ⚠️ **two different actions, so they are written down separately.**
　　⛔ **None of the three was a wrong check. All three were a missing check.**
　　All three were caught by a human — see `governance/Incident_Log.md` §3.

**R-35** 🔴 **"None" must be the result of taking stock, ⛔ never an omission.**
　　⚠️ **"Found nothing" and "did not look" read identically on the page, and carry very
　　different information.**
　　① **A "what I did not test / did not finish" column**: ⛔ "none" counts as not delivered.
　　　 **"None" is not full coverage; it is not having taken stock.**
　　② **Every other column that may legitimately be empty** (items needing adjudication, my
　　　 inferences…): "none" is allowed, **but state which directions you looked in and found
　　　 nothing.**
　　⛔ **This clause is the single home of all of the above.** `governance/Audit_Protocol.md`
　　§2 and §5, and `governance/HANDOFF.md` §3.1 and §3.2, each **cite** it; ⛔ none restates it
　　(constitution §3.2).
　　⚠️ **Why it is a rule rather than prose in four places:** the same principle was written out
　　**verbatim** in several documents, each with a different preceding sentence and a complete
　　context of its own — **that is not copy-paste, it is one higher-order principle instanced in
　　several settings. An instance should cite the principle, ⛔ not restate it.**


## C. Artefacts and self-certification

**R-10** ⛔ An artefact must not claim it has verified itself.
　　⚠️ **The reason is not that such claims are usually false. It is that the claim cannot be
　　independently reviewed in principle** — the document certifying and the document being
　　certified are the same file, so the reader is handed a circle.
　　⛔ **And it can be shown false: find one fabrication anywhere in the same batch.**
　　**This has actually happened; the verbatim evidence is in the self-certification family of
　　`governance/Incident_Log.md`.**
　　⚠️ **This clause deliberately carries no case number:** a downstream project's incident log
　　is its own, and **inserting a case ahead of that one shifts the numbering while the citation
　　still resolves — it just points at a different case.**
　　🔴 **Why that is worse than a dangling reference: constitution §3.4.** ⛔ Not restated here.
**R-11** ⛔ When the user has not asked about quality, do not offer a global appraisal.
**R-12** When claiming "done / passed / restored", **state which aspects were checked**.

## D. Data and file operations

**R-13** ⛔ Do not run git commands that rewrite the working tree.
**R-14** Extracted artefacts (produced programmatically from PDFs or scans) ⛔ must not be hand-edited; regenerate with the tool.
**R-15** Every extracted artefact must have its own hash registered.
　　⚠️ **Why: if a party with write access can alter the extraction, the evidence chain becomes
　　circular — and silently so.**
**R-16** Numbers that change (counts of sensors, entries, tests) ⛔ do not go into clauses; write a runnable check instead.
　　⚠️ **But if you do write a number, it must be correct.** What must actually be blocked is
　　"neither a number nor a way to check".

## E. Sensor governance

**R-17** The three gates for sensor changes (constitution §7.1) are all required.
**R-18** ⛔ Exclusion lists must be evaluated on paths **relative to the project root**.
　　⚠️ Both predecessor projects hit this once each: comparing absolute path parts excludes
　　every file under the fixture directory, **making self-tests all-green or all-red**.
　　**This is not a memory problem; the default way of writing exclusions is simply wrong.**
**R-19** **Precision over coverage.** A sensor that fires on correct text teaches people to ignore it.
**R-20** ⛔ The response to a false alarm is never to loosen the criterion; it is to fix the comparison and add a "must not false-alarm" fixture.
**R-21** Whitelists and hard-coded lists ⛔ must not define scan scope; use discovery-based scanning.
　　⚠️ Triggering case: a project's scan list carried a comment saying
　　"this is a hand-maintained whitelist; new documents will not appear automatically",
　　**and then failed exactly that way** — two required-reading documents were never checked.
　　**Writing down "this mechanism has a flaw" is not the same as fixing it.**
**R-22** A crash counts as INCOMPLETE. ⛔ Not FAIL, not PASS.
**R-33** ⛔ **"There was nothing to do" must never be the default branch when a preceding
　　operation failed.** **"I could not do it" and "there was nothing to do" must exit
　　with different codes.**
　　⚠️ **This applies to every script and tool, not only sensors** (it sits in this section
　　because it shares exit-code semantics with R-22).
　　⚠️ Triggering case: in a mount that denies unlink, `ai_checkpoint.sh` could not delete
　　`.git/index.lock`, the message was eaten by `2>/dev/null`, `git add` failed, the index
　　stayed empty, **so the script printed "no changes" and `exit 0` — no checkpoint was
　　created, and nobody would ever know.**
　　→ Full shape in `governance/Incident_Log.md` §2.2, "technically correct" failures, form three.
　　✅ **Correct form:** after a delete / move / write, **check that it actually succeeded**.
　　⛔ Never assume. **Only on success may control reach the "nothing to do" path.**

## F. External tools and sources

**R-23** External AI output is an **unverified lead**; its only legitimate use is pointing at a topic.
**R-24** Every external prompt must be **fully self-contained**. ⛔ No "as above", "see previous", "same as R1".
　　⚠️ Triggering case: a prompt's §1 quoted the rule "do not write 'as above'",
　　**and its lower half wrote "Same as R3-1"**.
　　Measured consequence: the referenced marker was used 0 times in that run,
　　while the version with the clause spelled out used it 12 times.
**R-25** Bibliographic identifiers ⛔ must not be generated by AI; obtain them from an authoritative bibliography.

## G. Full-text extraction and anchors

**R-26** Anchors must be verbatim. ⛔ Do not paraphrase, add punctuation, or normalise whitespace.
**R-27** At comparison time, the anchor and the extraction **must pass through the same normalisation function on both sides**.
　　⚠️ **The order cannot be swapped: de-hyphenation must precede whitespace collapse.**
　　Otherwise `individ-\nual` becomes `individ- ual` and then `individ-ual`, **and can never be rejoined**.
**R-28** ⛔ Normalisation happens only at comparison time; it is never written back to either side.

## H. Delegation and handoff

**R-29** Handoffs are always `.md` files in `handoffs/`.
**R-30** A handoff packet must separate **"what I independently verified / what I only restated / what is my inference"**.
**R-31** The recipient **spot-checks the most confident claims first**, not the least confident.
　　⚠️ **Why: across two projects, forty-odd incidents almost all occurred where the author was most certain.**
**R-32** ⛔ The auditor does not fix the defects it finds.

---

## Repeal / change register

| Date | Action | Note |
|---|---|---|
| — | **File created** | Distilled from two predecessor projects' rule sets. **Every clause corresponds to at least one measured case.** |
| 2026-08-20 | **R-35 added** | Decision 22. Triggering case: the sentence "'None' is not full coverage; it is not having taken stock" appeared verbatim in `Audit_Protocol.md` and `HANDOFF.md`, each with a complete context of its own. ⚠️ **Judged to be one higher-order principle instanced in several settings, so it was raised to a rule and all four sites now cite it** — ⛔ not reworded to dodge the sensor |
| 2026-08-19 | **R-34 added** | Three triggering cases: `rm` failure read as no delete permission; a sensor's "may have no network" read as a sandbox with no network; denied `unlink` read as no ability to delete. ⚠️ **The countermeasure existed in a predecessor project and was lost when the framework was distilled** |
| 2026-09-01 | **`R-34` gains scope-of-authority** | ⛔ Not a new rule. Project D's auditor supplied a form the existing wording cannot block, and it was his own: his system prompt said `device_bash` cannot delete files — true — and he read it as a universal statement. 🔴 **The existing `R-34` blocks "did not check the tool list"; ⛔ it does not block "checked one authoritative statement that covered only one channel"** |
| 2026-08-19 | **R-33 added** | Triggering case: the framework's own `ai_checkpoint.sh` reported a false success in a mount that denies unlink. Logged in `governance/Incident_Log.md` §2.2, "technically correct" failures, form three |

| 2026-08-26 | **`R-01`–`R-04` restored as four rows** | ⛔ Not a new rule. Rewriting T0 collapsed the four rows into the range `R-01`–`R-04`, and **`R-02` / `R-03` then matched nothing anywhere in the repository** — while this file's header says rows are never deleted. 🔴 **A range cannot carry the mapping: `R-03` → §3 item 5, `R-04` → item 6, not contiguous.** Now four pointer rows, with items 3 and 4 recorded as carrying no `R-xx` |

⚠️ **Rows in this table are never deleted.** Repealed rules change state, they are not removed —
**deleting the record makes the same rule get re-proposed a few rounds later,
with nobody knowing it has already been tested.**
