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
| ⑤ Authenticity | Does this reference exist | **Authoritative bibliography file** (`policy/SOURCES.md` §3) | **Human** / ✅ approved tool |
| ⑥ Support | Does the passage bear this claim | — | **Human / cross-model audit** |
| ⑦ Generalisation | Can you go from that sample to here | — | **Human / cross-model audit** |

⚠️ **⑥ and ⑦ are deliberately not mechanised.** They are judgement, not a backlog item.
**An attempt to mechanise them yields a sensor that fires on correct text,
and that teaches people to ignore the whole system.**

⚠️ **⑤ is different from ⑥ and ⑦: it is not unmechanisable, there is simply no trustworthy
machine source for it by default.** The conditions under which a tool may take over this link
are defined in `policy/SOURCES.md` §5 — ⛔ not restated here.

---

## 3. Document tiers (**by update frequency, not by topic**)

| Class | Frequency | Examples |
|---|---|---|
| **State** | Overwritten each round | `NEXT_SESSION_MEMO.md` |
| **Spec** | Rarely | The two T0 files, `RULES.md`, `policy/*` |
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

1. **Declare your model** (`policy/MODEL_IDENTITY.md`)
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
3. **Produce a handoff packet** (`policy/HANDOFF.md`)
4. Raise decision requests (§5)

⚠️ **Any change affecting another party's permissions, specs, or tool behaviour requires a
handoff packet naming the recipient** — **including the governance/maintenance role itself.**
A predecessor project's governance role wrote only its own memo for a long time;
**the result was that other roles only discovered a rule had changed the next time they violated it.**

### 4.3 🔴 When an instruction conflicts with T0 (**the most commonly missing rule**)

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

## 6. Write scope

**Set per your chosen profile, registered in `file_index.md`.**

### 6.1 What "output area" means

**Output area ＝ the directory where this role's work for the round should land.**

| Situation | Output area |
|---|---|
| Single AI | Project root, **minus** ledgers, T0, and `scripts/` |
| Multiple roles | Whatever `write_scopes` lists in `framework_config.py` |

⛔ **In every situation, the following are in no AI's output area:**
`ledgers/`, `governance/AGENTS.md`, `governance/WORKFLOW_CONSTITUTION.md`

✅ **`NEXT_SESSION_MEMO.md` is part of every role's output area** —
the end-of-session ritual requires overwriting it (§4.2); leave it out and **§4 and §6 contradict each other**.
⚠️ Found by the framework's own live test: the tested agent, faced with that contradiction,
chose not to overwrite it. **The file was left containing three spaces.**

**Three general rules:**

1. **A role writes only to its own output area ＋ `handoffs/`.**
2. **Ledgers are by default in no AI role's write scope** — ⚠️ **that is a default, ⛔ not a
   prohibition. See §6.3.**
3. **Every exception must have its cost written down.**
   ⚠️ One exemption is fine, but **an exemption should be visible rather than quiet**.


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


### 6.3 🔴 Authorisation is the user's decision, ⛔ not the framework's

**A user may authorise the AI to write anything in their project, ledgers included.**
⛔ **This framework has no standing to forbid that** — **each project is the responsibility of
its principal, and this framework takes no responsibility for any project's final product.**

⚠️ **Reason: a prohibition the user cannot lift gets routed around entirely the moment they
genuinely need it lifted, and routing around leaves no record. ⛔ A gate that can be switched
off in a config is safer than a gate that gets bypassed.**

**Mechanical counterpart:** `deny` in `governance_config.json`.
**Empty it and authorisation is complete.**

#### One thing worth knowing when you decide (⛔ information, not persuasion)

| | After it breaks |
|---|---|
| **Framework documents** (`governance/` `policy/` `profiles/` `prompts/` `scripts/` …) | ✅ **Re-download from GitHub and overwrite** |
| **`ledgers/` `corpus/` `corpus_md/` `handoffs/` `incidents/` `PROJECT.md`** | 🔴 **Nothing anywhere can restore them** |

**The default `deny` blocks only the second kind, ⛔ never the first** — so a governance agent
can fully maintain the governance documents, **which is the precondition for a user being able
to keep this framework alive on their own.**

#### ⚠️ Two things full authorisation does not change

1. **The AI still declares "which files I wrote" in `handoffs/`** (`policy/HANDOFF.md` §3.3).
   **Authorisation changes what may be written, ⛔ not whether it must be reported.**
2. The **falsification-adjudicated column** in `ledgers/Conjecture_Ledger.md` is still ⛔
   human-only. 🔴 **That column is the only record that a human adjudicated — if the AI can
   fill it, adjudication is just a string.**

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

1. The auditor **must not be the same model as the audited**
2. The report must carry **"what I tested / what I did not test"**, and **the latter must not be empty**
3. The conclusion's scope **must not exceed the test matrix**
4. ⛔ **The auditor does not fix things**

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
| ② | Did it touch **anything I cannot restore** (ledgers, corpus, handoffs, `PROJECT.md`)? |
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
