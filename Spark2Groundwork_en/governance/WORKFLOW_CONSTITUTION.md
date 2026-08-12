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
| ⑤ Authenticity | Does this reference exist | external lookup (optional) | Computational, needs network |
| ⑥ Support | Does the passage bear this claim | — | **Human / cross-model audit** |
| ⑦ Generalisation | Can you go from that sample to here | — | **Human / cross-model audit** |

⚠️ **⑥ and ⑦ are deliberately not mechanised.** They are judgement, not a backlog item.
**An attempt to mechanise them yields a sensor that fires on correct text,
and that teaches people to ignore the whole system.**

---

## 3. Document tiers (**by update frequency, not by topic**)

| Class | Frequency | Examples |
|---|---|---|
| **State** | Overwritten each round | `NEXT_SESSION_MEMO.md` |
| **Spec** | Rarely | The two T0 files, `RULES.md`, `policy/*` |
| **Data** | Event-driven, append-only | Ledgers, `Incident_Log.md`, `handoffs/` |
| **Index** | As files come and go | `file_index.md` |

### 3.1 ⛔ State belongs only in state-class documents

⚠️ **Source: a predecessor project's dispatch document kept its to-do list in its own §5.
Within three hours it contained two entries marked "✅ done" that were still sitting there.**

> **A document with state mixed in inherits the update frequency of its fastest-changing part.**
> **And the reader cannot tell which paragraph is stale — each one reads fine on its own.**

### 3.2 Every rule has exactly one home

**Any rule, criterion, or table is defined in exactly one place project-wide;
everywhere else cites it rather than restating it.**

⚠️ **Measured: one project had 17 sentences appearing verbatim in more than one file.**
**Duplication itself is harmless; divergence is fatal — and divergence is the
inevitable end state of duplication, not an accident.**

**Each rule's home is registered in `file_index.md` §0.**

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
| Other files | `` `filename.md` `` §N |

⛔ **Do not use ambiguous short forms** (e.g. writing "the constitution §N" when the project has two constitutions).
⛔ **When citing another project's section numbers, name that project** —
⚠️ a predecessor project inherited a failure-family table from another project
**together with that project's section numbers; four dangling references went unnoticed for a long time.**
**Inheriting a rule together with its citations is itself a form of "index as authority".**

---

## 4. Rituals (**hard gates, not skippable**)

### 4.1 Session start

1. **Declare your model** (`policy/MODEL_IDENTITY.md`)
2. Read the state document (`NEXT_SESSION_MEMO.md`)
3. Read both T0 files
4. First-time participants also read `Incident_Log.md`
5. **Restate your own write scope** (§6)
6. Run `run_all_sensors.py` and **confirm the exit code**

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

**A framework with only "decision requests" has a mechanism for proposing rule changes —
it has none for "what do I do right now".**

⚠️ **Measured:** a tested agent received an instruction to write into the ledger,
while four documents said AI must not write to the ledger.
**It derived its own handling from the exemption clause and executed.**

> **An agent deriving on its own that it may make an exception
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
2. ⛔ **Ledgers are in no AI role's write scope.**
3. **Every exception must have its cost written down.**
   ⚠️ One exemption is fine, but **an exemption should be visible rather than quiet**.

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

⚠️ **A crash counts as INCOMPLETE, not FAIL.**
Conflating them makes "the sensor is broken" look like "the document has a problem" —
**and that sends someone to fix a document that was fine.**

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
