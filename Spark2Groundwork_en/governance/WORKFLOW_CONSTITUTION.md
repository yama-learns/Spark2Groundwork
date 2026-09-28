# Workflow Constitution (T0)

**Tier: T0.** Subordinate to `AGENTS.md`, above everything else.

> ⛔ **This file must contain no state.** ⛔ **It restates no other document's rules; it defines process only.**

---

## 1. Topological facts (**the premise of every rule**)

| Fact | Consequence |
|---|---|
| **No persistent orchestrator** | Information across sessions can only travel via files |
| **No shared memory** | "We discussed this last time" does not exist in the next session |
| **AIs do not talk to each other** | Every exchange must land as a file, and pass through the principal |
| **The principal is the single adjudication point** | The queue will grow; it must be made visible (§5.1) |

⛔ **Any design premised on "we said so in conversation" or "the AI remembers"
is, in this topology, not a design at all.**

---

## 2. Evidence chain and sensor placement

| Link | Question | Watcher | Type |
|---|---|---|---|
| ① Locate | Which passage to cite | — | **Human** |
| ② **Exists** | Is that passage in the source | `sensor_claim_ledger.py` | **Computational, zero cost** |
| ③ Fields | Are required fields filled | `sensor_conjecture_ledger.py` | Computational |
| ④ Consistency | Do documents agree | `sensor_governance_text.py` | Computational |
| ⑤ Authenticity | Does this reference exist | **Authoritative bibliography file** (`governance/SOURCES.md` §3) | **Human** / ✅ approved tool |
| ⑥ Support | Does the passage bear this claim | — | **Human / cross-model audit** |
| ⑦ Generalisation | Can you go from that sample to here | — | **Human / cross-model audit** |

⚠️ **⑥ and ⑦ are deliberately not mechanised.** They are judgement, not a backlog item.
**An attempt to mechanise them yields a sensor that fires on correct text,
and that teaches people to ignore the whole system.**

⚠️ **⑤ is different from ⑥ and ⑦: it is not unmechanisable, there is simply no trustworthy
machine source for it by default.** The conditions under which a tool may take over this link
are defined in `governance/SOURCES.md` §5 — ⛔ not restated here.

---

## 3. Document tiers (**by update frequency, not by topic**)

| Class | Frequency | Examples |
|---|---|---|
| **State** | Overwritten each round | `NEXT_SESSION_MEMO.md` |
| **Spec** | Rarely | The two T0 files, `RULES.md`, `governance/*` |
| **Data** | Event-driven, append-only | Ledgers, `Incident_Log.md`, `handoffs/` |
| **Index** | As files come and go | `file_index.md` |

### 3.1 ⛔ State belongs only in state-class documents

**A document with state mixed in inherits the update frequency of its fastest-changing part,
and the reader cannot tell which paragraph is stale — each one reads fine on its own.**

### 3.2 Every rule has exactly one home

**Any rule, criterion, or table is defined in exactly one place project-wide;
everywhere else cites it rather than restating it.**

🔴 **Paths, directory names, filename patterns and field names are rules too,
and they get exactly one home as well.**

⚠️ **Duplication itself is harmless; divergence is fatal — and divergence is the inevitable
end state of duplication, not an accident.**
⛔ **An agent that follows one of three mutually contradictory specs has not misjudged;
the three specs are what is wrong.**

**The single home for paths is `scripts/harness/framework_config.py`; each rule's home is
registered in `file_index.md` §0.**

### 3.3 Document proliferation defence

**Before adding any governance document, answer three questions:**

1. Could this be a section in an existing document?
2. If not, is it because the topic differs, or because the **update frequency** differs?
3. What is this document's authority scope? **Where it overlaps existing documents, who owns the overlap?**

⚠️ **Measured: a project's governance documents were cut from 46 to 22, then rebounded to 42.**
**Trimming is not a one-off action; rebound is the default behaviour.**

### 3.4 Citation format

| Case | Form |
|---|---|
| This file | §N |
| Other files | `` `<filename>.md` `` §N |

⛔ **Do not use ambiguous short forms** (e.g. writing "the constitution §N" when the project has two constitutions).
⛔ **Cite a failure family by name, never by number** — **the number is the table's ordinal;
the name is the identifier.**
🔴 **A citation that silently retargets is more dangerous than one that dangles, because it
stays green** — and a sensor can only catch the latter.
⛔ **When citing another project's section numbers, name that project** —
**Inheriting a rule together with its citations is itself a form of "index as authority".**

---

## 4. Rituals (**hard gates, not skippable**)

### 4.1 Session start

1. **Confirm your model and its source once** (no repeat without a switch or new conflict in the same conversation; `governance/MODEL_IDENTITY.md`)
2. Read the state document (`NEXT_SESSION_MEMO.md`)
3. Read both T0 files
4. First-time participants also read `Incident_Log.md`
5. **Restate your own write scope** (§6)
6. Run `run_all_sensors.py`, **confirm the exit code, and handle it per the table below**

#### 4.1.1 🔴 What to do when the exit code is not 0

> ⚠️ **A ritual step with a check and no disposition is a step that does nothing.**

| Exit code | Disposition |
|---|---|
| **0** | Start as normal |
| **1 (FAIL), unrelated to this session's task** | ✅ Start, **but log it at the top of this session's output**: how many FAILs, why you judged them unrelated, who clears them |
| **1 (FAIL), related to this session's task** | ⛔ **Fix first. Do not start.** |
| **2 (INCOMPLETE)** | ⛔ **Stop and report.** "Could not check" ⛔ must not default to "unrelated" |

⛔ **When you cannot tell which row applies, take the last one** (same as the last row of §4.3).

### 4.2 Session end

1. Run `run_all_sensors.py`
2. Overwrite the state document
3. **Produce a handoff packet** (`governance/HANDOFF.md`)
4. Raise decision requests (§5)

⚠️ **Any change affecting another party's permissions, specs, or tool behaviour requires a
handoff packet naming the recipient** — **including the governance/maintenance role itself.**
A predecessor project's governance role wrote only its own memo for a long time;
**the result was that other roles only discovered a rule had changed the next time they violated it.**

### 4.3 🔴 When an instruction conflicts with T0 (**the most commonly missing rule**)

This section does not block user changes to role defaults under §6.3. Proceed with explicitly authorized ordinary writes instead of refusing because of the factory role split.

**"Decision requests" propose rule changes; they do not answer "what do I do right now".**

> ⚠️ **An agent deriving on its own that it may make an exception
> is exactly what this framework should worry about most.**

**→ Explicit handling, four cases, judged in order:**

| Case | Handling |
|---|---|
| Conflicts with a T0 **hard prohibition** (⛔ clause) | ⛔ **Stop and report. Do not execute.** |
| Conflicts with a T0 **procedural rule**, and **not executing blocks the task** | ✅ Execute, **but log the exemption at the top of the output**: which rule, why, at what cost |
| Conflicts with T0, but **a non-conflicting alternative exists** | ✅ **Always take the alternative**, and report that you did |
| Cannot tell which case applies | ⛔ **Stop and report.** ⚠️ "Cannot tell" does not default to executable |

⛔ **Never execute silently.** All three executable cases require you to say so.
**This framework can tolerate an exception; it cannot tolerate nobody knowing an exception was made.**

---

## 5. Decision request format

```
> **[Decision request N] <one-line title>**
> **Proposed change:** what specifically changes
> **Motivation:** why now
> **Verification status:** what I verified, what I did not, what residual risk remains
> **Options:** [A …] (recommended) / [B …] / [C do nothing]
```

⛔ **The "verification status" field must not be empty, and must not say "fully verified".**

### 5.1 The pending queue must be visible

The pending list in the state document **must carry a "rounds waited" column**.

⚠️ **Why:** the principal is the single adjudication point. When the queue grows faster than it drains,
**the failure mode is "adjudication quality drops", not "adjudication stops" — and that shows no red light.**
**The number of rounds waited is itself the signal.**

---

## 6. Write scopes

### 6.1 Default role permissions

Roles divide work; they are not directory barriers to everyday tasks. A user-assigned task includes the reading, directory creation, writing and editing of ordinary work products needed to complete it. Do not ask again for every file. This table applies to solo and multi-role work. A solo AI may combine jobs, but self-checks are not independent review.

| Role | Allowed by default | Actions needing a specific instruction |
|---|---|---|
| Research | Reading, translations, notes, analysis, code and manuscript drafts; `my/research/`, user-designated research folders, `corpus_md/`, research memos and ledger working records; adding acquired papers to `corpus/` | Deleting or overwriting original papers/data; changing user-decided goals or ethical limits; modifying framework governance or shared tools |
| Governance | `governance/` including both T0 files, `profiles/`, `prompts/`, `scripts/`, indexes, settings and rules/incidents in `my/`; recording actual user decisions and organizing ledgers | Changing explicit user permissions, research goals or ethical limits; deleting/revising research under the guise of housekeeping; external publication |
| Audit | Reading task-relevant files; creating `my/audit/`, reports, tests, reproduction copies, memos and handoffs; creating its own sandbox | Changes to reviewed artifacts must be within an assigned repair task; the auditor becomes a repair author for those changes and cannot call their review independent |
| All roles | Their working folders, `scratch/`, `handoffs/`, `NEXT_SESSION_MEMO.md`; maintaining factual descriptions/status in `PROJECT.md` | Coordinate or merge before sharing a file; never overwrite another worker's unmerged work |

Ledgers may contain candidate claims, sources, notes, open questions and check results. Record "user confirmed/reviewed/accepted" only from an actual user instruction, never by inference. The falsification-condition adjudication remains the user's decision; an AI may transcribe explicit words with their source, but cannot decide on the user's behalf. Changing roles does not reset review independence.

Reuse existing research tools where suitable; create needed task tools in `my/research/tools/` or a task folder without stopping research for lack of a bundled tool. Never silently weaken framework checks to obtain a pass. Drafting is not formal adoption; source and research-integrity requirements remain.

After adding, renaming or moving project-owned files, run `python scripts/harness/tool_my_index.py` before closing to refresh `my/MY_INDEX.md`; otherwise the sensor reports `MY_INDEX_STALE`. This is index maintenance, not a permission refusal.

These are permissive v1.5 defaults. Detailed role design belongs to later v2 work. Paths are suggestions, not a requirement to move existing user data.


### 6.2 Operational directories (**they are not output areas**)

| Directory | What it is | Version-controlled | Scanned by sensors |
|---|---|---|---|
| `scratch/` | **Sandbox.** Things built to test a judgement: a small repo for reproduction, a throwaway script, a disposable specimen. Conventional path `scratch/<topic>_sandbox/` | ⛔ no | ⛔ no |
| `archive/` | Retired versions kept **deliberately undeleted** | ✅ yes | ⛔ no |
| `_to_delete/` | In an **environment where deletion is denied**, the holding place for things judged deletable | ⛔ no | ⛔ no |

🔴 **The defining property of `scratch/`: nothing in it ⛔ may be cited.**
**A sandbox exists to reach a conclusion, not to produce something others will cite.**
⚠️ **It is not version-controlled, so by the time the next person opens your citation the file
is gone** — **and a citation pointing at a file that does not exist reads exactly like a
well-founded one.**
→ **Move what you want to keep out of `scratch/` into your output area first, then cite it.**

⚠️ **`_to_delete/` is a product of an environment limit (some filesystems deny `unlink`),
⛔ not a wastebasket.**
⛔ **After moving something there you must tell a human, who does the real deletion** —
**a `_to_delete/` nobody knows about is identical to not having deleted anything.**

⚠️ ⛔ **`excluded_dirs` lists them to save scanning cost, not to grant permission.**
**"Not scanned" and "not writable" are different things** — see the comment on that key in
`scripts/harness/framework_config.py`.


#### Folders the user creates

🔴 **A user may create any folder in the project, ⛔ without registering it with the framework.**

**Two mechanisms guarantee those folders are safe, and both are mechanical:**

1. **The upgrade tool recognises only the items named on its replaceable list** (`FRAMEWORK_DIRS` and `FRAMEWORK_FILES` in `upgrade.py`) and
   ⛔ **refuses every other target.**
   ⚠️ **Paired sample: `upgrade_case()` in `run_selftest.py`.**
2. **A sensor's scan scope is defined by globs**, ⛔ not by "scan everything".

⚠️ **This clause exists because of a place that is easy to read backwards:**
**what protects the user's material is the list of replaceable items, ⛔ not a list of
protected ones.**
🔴 **The latter exists only to produce a clearer error message** —
**⛔ treated as the primary defence, it makes any folder not on it look unprotected.**

### 6.3 User instructions and configuration

Users may change these defaults; explicit task instructions take precedence over the factory division of work. Preserve existing user restrictions. Ordinary work needs no separate directory permission; clarify only a genuinely ambiguous scope, destructive original-data change, change to a settled decision, external disclosure or publication.

New projects use `deny: []` and `write_scopes: {}` in `governance_config.json`. Empty deny means no blanket path ban; it does not authorize arbitrary tasks, decisions on behalf of the user or publication. With nonempty write_scopes, the current sensor checks the union of all roles' paths, not actual authorship or per-role enforcement. It is an after-the-fact check, not an operating-system permission boundary.

With empty write_scopes, a deny hit produces DENIED_PATH_TOUCHED_UNATTRIBUTED as a warning, not a failure by itself. With nonempty scopes, deny hits outside the existing _human exception produce WRITE_TO_DENIED_PATH/FAIL. Other checks may still fail or be incomplete. This is an after-the-fact check, not OS enforcement; user restrictions still bind the AI.

Upgrades never overwrite existing project settings. If a user chooses the new defaults, read their settings first, show and apply the smallest necessary changes, and retain custom restrictions. An explicit task authorization also permits aligning the settings needed for that task; do not require users to edit JSON or repeat the same approval. Clarify a conflicting custom restriction only where necessary; never silently clear it.

Protect data by action: routine additions and editing may proceed; deleting or irreversibly overwriting original data, erasing history, external private-data disclosure and publication need corresponding authorization. Saving is not human review; writable ledgers do not confer acceptance authority. Report actual changes without creating a separate exception record for every ordinary write.


### 6.4 🔴 A file may have exactly one owner (v1.4.1)

**An upgrade only recognises the framework's own handful of names (§6.2). ⛔ One thing follows:**

🔴 **A file that mixes "the framework's content" with "your content" will lose one of them at
the next upgrade — ⛔ and which one is lost depends only on which list that folder is on.**

| Where the file is | Consequence of two owners | The framework's own instance |
|---|---|---|
| **On the replaceable list** | 🔴 **What you accumulated is deleted** | `governance/RULES.md` was where projects accumulated their own rules |
| **On the never-replace list** | 🔴 **The framework's update never arrives** | The two ledgers in `ledgers/` carried sixty lines of framework specification |

⚠️ **⛔ Two directions of one illness. Before v1.4.0 this framework had one of each.**

**⇒ The criterion: does the project add more of the same kind of item to this file, one by one?**

| Answer | Treatment | Instance |
|---|---|---|
| **Yes** | **Framework ⊆ a copy under `my/`, plus a comparison sensor** | `RULES.md` ↔ `my/MY_RULES.md` |
| **No, but framework definitions and project data are mixed** | **Definitions move to the framework side; the data side keeps data plus a one-line pointer** | the two ledgers ↔ `governance/*_LEDGER_SPEC.md`; `Incident_Log.md` ↔ `my/MY_INCIDENTS.md` |
| **Pure framework content** | **Replaced wholesale** | `file_index.md`, `governance/*`, `profiles/*`, `prompts/*`; the user-filled first idea now lives at the root, outside `prompts/` |

⚠️ **⛔ The criterion exists to stop a good mechanism being applied where it is not needed:
per-item copies of a ledger would put sixty lines of spec inside the user's data file,
⛔ and nobody would ever read that copy.**

🔴 **⚠️ One exception: the authorisation settings (`governance_config.json`) do ⛔ not follow row two.**
**A specification update should reach you; ⛔ what you have authorised is your decision, and the
framework must not overwrite it (§6.3).**

---

## 7. Sensor governance

### 7.1 Three gates for any sensor change (all required)

① Paired seeded-defect fixtures (**"must catch" ＋ "must not false-alarm"**)
② `run_selftest.py` fully passing
③ The triggering case logged in `scripts/harness/SENSOR_CHANGELOG.md`

### 7.2 Scope of "no case, no change"

| Target | Rule |
|---|---|
| **Sensors** | ⛔ **No measured case, do not build.** False alarms teach people to ignore sensors |
| **Document rules** | ✅ May be established pre-emptively on architectural risk, **but must be tagged `[predicted]` with a review trigger** |

⚠️ **Their failure costs are asymmetric, so the criteria should not be the same:**
**a false-alarming sensor gets switched off; an untriggered document rule is merely untriggered.**

### 7.3 Handling a checking tool's false alarm

⚠️ **When a checking tool declares the artefact defective, first assume the tool is broken.**

| Step | Action |
|---|---|
| 1 | **Re-check with a second, independent tool** |
| 2 | Check whether normalisation on **both sides is fully symmetric**. One-sided normalisation manufactures false positives |
| 3 | Check the **order** of normalisation: strip structure first, collapse whitespace last |
| 4 | Only after all three may you declare the artefact defective |

⛔ **Loosening the criterion is not an acceptable response to a false alarm** — it switches off true positives too.
The response is always to fix the comparison logic **and add a "must not false-alarm" fixture**.

### 7.4 Three exit codes

| Code | Meaning |
|---|---|
| 0 | PASS |
| 1 | FAIL — **a definite defect** |
| 2 | **INCOMPLETE — could not check. ⛔ This is not a pass** |

⚠️ **A crash counts as INCOMPLETE, not FAIL** — otherwise "the sensor is broken" looks like
"the document has a problem", **and that sends someone to fix a document that was fine.**

### 7.5 Cross-layer checklist for governance changes

**Before every governance change, ask layer by layer:
which layer does this touch? Which layer will it force to change?**

| Layer | Here |
|---|---|
| **E** Execution | Sandbox boundaries, scratch space |
| **T** Tooling | `scripts/` |
| **C** Context | Document tiers, state files, ledgers |
| **L** Lifecycle | Rituals, handoffs, decision requests |
| **O** Observability | Git checkpoints, logs, re-runnable commands |
| **V** Verification | Sensors, paired self-tests |
| **G** Governance | Write scopes, ethical gates, vocabulary rules |

⚠️ **Measured: neither cross-layer cascade was foreseen — both were caught by sensors after the fact.**
Widening corpus write access forced a hash check; granting an audit sandbox
immediately collided with T0 uniqueness.

---

## 8. Cross-model adversarial audit

**Spec in `governance/Audit_Protocol.md`. This section fixes only four non-negotiables:**

1. Independent reviewers must not have authored or repaired the material they review. Changing models, vendors, roles or conversations does not reset authorship. Diverse models may add perspectives but do not establish independence.
2. The report must carry **"what I tested / what I did not test"**, and **the latter must not be empty**
3. The conclusion's scope **must not exceed the test matrix**
4. Do not modify reviewed artifacts without an assigned repair task. Carry out user-assigned repairs, preserve the original candidate and findings, and disclose repair authorship; do not claim independent review of those changes (Constitution §6).

---

## 9. What this constitution does not claim

- ⛔ It **does not guarantee the research is correct**
- ⛔ It **does not guarantee that all-green sensors mean no problem** — green covers only what is mechanised
- ⛔ It **cannot replace the principal's judgement**; it only gives that judgement something to stand on

## 10. 🔴 The cost ceiling on governance (**this section governs the framework itself**)

> **Governance is a cost of research, ⛔ not its purpose.**
> ⚠️ **The moment governance work starts crowding out the time and compute that research
> needs, governance has already failed** — **even if every governance document is individually
> correct.**

### 10.1 The user is the only auditor

⛔ **A governance agent must not be required to run an adversarial audit on its own
maintenance** — **it multiplies the overhead, and that compute was meant for the research.**

⛔ **`governance/Audit_Protocol.md` governs the audit of research output, not the review of
governance maintenance.**

### 10.2 The review is three questions (⛔ no more)

| # | Question |
|---|---|
| ① | For what changed this round, **can I see why it was changed?** |
| ② | Did it touch **anything I cannot restore** (ledgers, corpus, handoffs, `PROJECT.md`, `FIRST_IDEA.md`)? |
| ③ | **Are the sensors still green?** |

🔴 **⛔ The reviewer must not be asked to judge whether a change is *correct*.**
**That requires the same context the governance agent has, and requiring the user to hold that
context is exactly where the crowding-out comes from.**

⚠️ **All three are deliberately answerable in a few minutes.**
**A review process that takes half an hour is, in practice, a review that does not happen.**

### 10.3 The governance agent reports its cost every round

**State in the handoff packet: how many files were touched, how many rounds of conversation.**
⛔ **This is not for appraisal; it is to turn crowding-out into a visible number** —
**a cost nobody measures is a cost nobody notices growing.**

### 10.4 How this divides from §7

§7 governs **the quality of changing a sensor** (its three gates stand);
**this section governs whether the effort should be spent at all.**

---
