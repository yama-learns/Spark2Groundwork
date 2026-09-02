# Model Identity Protocol

**Tier: T1 — spec class.**

> **The enforceable form is `RULES.md` R-12. This file carries the mechanism difference
> between the two platform kinds, and the evidence behind it.**
> Moved here from a predecessor project's protocol of the same name and trimmed
> (date dropped from the filename, `R-16`).

---

## 1. Why this file exists

Incident **I-06** (a 3.1 Pro run executed intake under a 3.6 Flash identity; 26 papers came
back with every field blank and every sensor green) established that
**a misattributed model identity produces output that looks normal and is wrong**,
and that the sensors of the day could not catch it.

Four measured rounds on 2026-07-29 then exposed a second failure kind:
**an AI misreports its own identity without knowing it is doing so.**

| Round | Actual model | That model's self-report | Verdict |
|---|---|---|---|
| Main-text run | Fable 5 | (none) | — |
| MVE_v5.0c / R4-1 analysis | Opus 5 | (none) | — |
| Experiment ③ | **Haiku 4.5** | "the environment block says `Model: claude-opus-5`" | ❌ **wrong** |
| Experiment ④ | **Sonnet 5** | "the environment block says `Model: claude-sonnet-5`" | ✅ correct (and it volunteered a correction of the previous round) |

**The inference that matters:** the user's prior assumption that *the environment block is
unreliable* was **refuted by experiment ④** — the value Sonnet 5 read matched the user's actual
switch and differed from the previous round's value, which shows **the field updates per turn
and is accurate.** The real failure point is the **reading end**: Haiku 4.5 did not read
verbatim, it **predicted the answer from conversation context**
(the preceding text was full of "the user says they will switch to Opus 5", so it emitted opus-5).

> **This is a new member of the "index as authority" family, and its purest form:**
> not *consulted the index instead of the authority*, but **consulted nothing and
> completed the pattern from context.**

---

## 2. Two platform kinds (⛔ their rules do not port)

| | **State-snapshot platform** | **Change-event platform** |
|---|---|---|
| Authoritative source | a `Model:` field in an environment block | a `<USER_SETTINGS_CHANGE>`-style marker |
| Kind | **state snapshot** | **delta event** |
| How often present | **on every request** | only on the request where the user switched |
| When nothing switched | still shows the current value | **no marker**; you must look back through history |
| Main failure mode | **a lazy reading end** (predicting from context instead of reading verbatim) | **signal loss** (marker missed, or absent from the start of the session) |
| Robustness | higher (the signal is always there) | lower (depends on never missing an event) |

**⚠️ Therefore "look back through the context for the most recent recorded identity" —
correct on a change-event platform — is not merely unnecessary on a state-snapshot platform,
it is harmful:** that is exactly what Haiku 4.5 did wrong.
**On a state-snapshot platform, inferring identity from context is prohibited.**

**<<<FILL IN: which kind is the platform you work on, and what is its authoritative field>>>**

---

## 3. Rules

### 3.1 [State-snapshot platform] Declare identity every turn

**The first output of every user turn must contain one identity line.**

Format (**copy the `Model:` value verbatim: ⛔ do not rewrite it, complete it, or tidy it**):

```
[Model: <verbatim value>]
```

**Three prohibitions:**

1. ⛔ **Do not infer from conversation context.** The user's spoken declaration, the model named
   in a handoff packet, last turn's declared value, a description in a summary — **none of them count.**
2. ⛔ **Do not self-diagnose from answering style.** A model cannot introspect its own weights;
   style differences can be produced by the system prompt and the tool configuration alone.
3. ⛔ **Do not guess when you cannot read it.** Write
   `[Model: cannot read — please confirm in the interface]`.

### 3.2 Why every turn, and not "when a switch is detected"

The user's question was: **can an AI tell whether the current instruction came from the user?**

**Answer: structurally it can, and this rule deliberately does not depend on that.**

- **What is knowable:** I can observe whether the message immediately preceding this generation
  was a user message or a tool result. The former is the start of a turn.
- **What is not reliable:** scheduled tasks and automated flows inject messages in the user role
  too. ⛔ I cannot separate "a person typed this" from "a system sent it on their behalf".
- **But that does not matter, because:**
  1. The environment block **is present on every request**. Reading it needs no judgement about
     what kind of turn this is and **⛔ no tool call at all** — the cost is near zero.
  2. Scheduled and automated turns can just as easily run on a different model.
     **They should be checked anyway.**
  3. 🔴 **Any check that fires only after the AI first makes a judgement adds one more place
     for that judgement to be wrong.** An unconditional rule is more robust than a conditional one.

> **Design principle: ⛔ do not build a rule that rests on a premise I might get wrong.**
> This is the same reasoning as `R-34` — a capability boundary is read off the tool list,
> ⛔ not asserted from one error message.

### 3.3 Identity reconciliation gate on a handoff packet

If a packet or work order specifies "this task must be executed by X", the model picking it up
**must first compare that against its own declared value**:

- Match → proceed as normal
- **Mismatch → stop the substantive task immediately, raise an alert, and wait for adjudication:**
  > **[identity mismatch]** This task specifies `<X>`, but the environment block shows `<Y>`.
  > Please confirm whether the interface switch actually completed.

⚠️ **On a mismatch you must not decide for yourself that "I can do it anyway".**
**I-06 is precisely a case of *could* do it and did it badly.**

### 3.4 An artefact's author field must name the specific model

Every newly created `.md` artefact (main text, MVE, analysis report, governance document,
handoff packet) must carry a **specific model identifier** in its author field.
⛔ Not just "Claude" or "Gemini".

- ✅ `**Created:** Claude Opus 5, 2026-07-29`
- ❌ `**Created:** Claude, 2026-07-29`

**Why:** this is the only basis for attribution and traceability after the fact.
If the model-performance record in `governance/HANDOFF.md` cannot be tied to specific artefacts,
**the whole table degrades into impressions.**

> 🔴 **⚠️ Only half of this section has a mechanical defence (stated explicitly from v1.4.1).**
> **`sensor_model_attribution.py` scans `attribution_globs`, which in v1.4.1 is
> `handoffs/*.md` and nothing else.**
> 🔴 **So the author field of the "main text", the MVE and analysis reports
> ⛔ has nothing checking it.**
> ⚠️ **The two former globs `outputs/` and `reports/` matched 0 files from v1.0.0 onward —
> neither directory ever existed.**
> **⛔ The scope is completed once `research/` exists in v1.5.0.**
> **⚠️ Until then this section is a rule with ⛔ no mechanical counterpart for the main text —
> written down here rather than left blank.**

**Mechanical defence: `scripts/harness/sensor_model_attribution.py`.**

### 3.5 The git checkpoint tag carries the model

`auto: <time> [<model>-<topic>] — AI checkpoint, not reviewed by a human`

`<model>` must be a specific identifier (`opus5` / `fable5` / `sonnet5` / `haiku45`).
⛔ Not `claude`.

### 3.6 [Change-event platform] Reading identity, and context truncation

Treat the change marker as the single source of truth; with no marker, look back through the
context for the most recent record.
⚠️ **This look-back clause applies only to a change-event platform** (its signal is a delta;
there is no other way) — **⛔ it must not be ported to a state-snapshot platform.**

#### 3.6.1 Measured case (2026-07-31)

A predecessor project's git-audit handoff packet carried the author field `[Model: Antigravity]`.
The user established that the model was in fact **3.1 Pro**, and obtained that model's own account:
the workspace conversation had grown long, earlier context had been **truncated** by the system,
and **the change marker was no longer inside the visible window**. The output `Antigravity` was
a fall-back to the generic name in the system prompt. That system prompt states only
"You are Gemini, a large language model built by Google" and "designed by the Google Deepmind team" —
**⛔ it carries no version number.**

#### 3.6.2 What the case establishes: the asymmetry is worse than it was estimated to be

| | State-snapshot platform | Change-event platform |
|---|---|---|
| Signal kind | a `Model:` field — **state snapshot** | a change marker — **delta event** |
| Present on every request? | ✅ yes | ❌ no, only at the moment of the switch |
| After a long conversation is truncated | unaffected | **permanently lost, and ⛔ unrecoverable from the system prompt** |
| What the system prompt offers instead | — | only the family/vendor level, **⛔ no version number** |

**So identity reading on a change-event platform has a structural failure point
that ⛔ the AI cannot repair on its own.**

#### 3.6.3 Rules (three, all hard)

1. **When the marker is not inside the visible context, the only correct output is**
   `[Model: cannot read — the change marker is not in visible context]`.
   ⛔ **Do not** fall back to the generic name in the system prompt, the platform name,
   or the model family name.
2. 🔴 **A platform name is not a model.** Antigravity / Cowork / Claude Code / AI Studio are
   products; one platform runs different models. Writing the platform name is the same as
   writing nothing, and **worse than blank** — it reads as though there is an answer,
   so downstream stops asking. This is the same shape as the "artefact self-certification"
   family: **filling a field that should be empty with a string that looks acceptable.**
   Mechanical defence: `PLATFORM_NOT_MODEL` in `scripts/harness/sensor_model_attribution.py`.
3. **When you report "cannot read", ask the user to supply it.** The user's interface and
   billing are independent evidence the AI cannot see; identity **can** therefore be recovered —
   ⛔ but the one recovering it must be a person, not the AI's inference.

> ⚠️ **Nobody lied in this case.** With its information truncated, 3.1 Pro made a reasonable
> downgrade — the direction was just wrong.
> **It should have downgraded to "I do not know", ⛔ not to a vaguer name.**

### 3.7 🔴 When the authoritative field is not where the protocol says it is (**measured, 2026-08-12**)

**Measured case:** in one run the environment block **had no `Model:` field**, but the identifier
was written verbatim on the line immediately after that block in the system prompt.

⚠️ **Strictly applied, the correct output would be "cannot read" — and that would be a wrong
downgrade: the authoritative information existed, just not where the protocol said.**

**Handling (three cases, tried in order):**

1. The designated location has a value → **take it verbatim**
2. It does not, but **the same system prompt contains a verbatim model identifier** →
   take it, **and state explicitly: "authoritative field absent; read verbatim from `<actual location>`"**
3. Neither → **output "cannot read"**. ⛔ **Do not substitute a platform name**

⛔ **In case 2 that sentence must not be omitted.**
**"I read it" and "I read it from somewhere the protocol does not mention" are different things,
and ⛔ the reader cannot tell them apart from the output alone.**

---

## 4. Mechanical defences

**Rules do not stop a recurring error; mechanical checks do** (this project's position since I-05).

| Defence | What it does | Where |
|---|---|---|
| **M-1 identity trace table** | Every turn's declared value is written into an identity trace table (suggested filename `model_session_log.md`), so the user can cross-check it against the interface and the billing record | ⚠️ **not shipped with this framework; create your own** |
| **M-2 author-field sensor** | Scans root `.md` files for "author field names only Claude/Gemini with no model" and "no author field at all" | `scripts/harness/sensor_model_attribution.py` |
| **M-3 an extra item in the closing ritual** | At close of work, confirm the identity trace table has a row for this turn | `governance/WORKFLOW_CONSTITUTION.md` §4.2 |

**M-1 is the only mechanism that can check an AI's declaration after the fact** — because the
user holds two independent evidence sources the AI cannot see: the interface and the bill.
An AI's self-declaration is not by itself trustworthy (Haiku 4.5 demonstrated that);
**its value is that it gets written down and can therefore be refuted.**

---

## 5. What this protocol does not claim

- ⛔ **It does not claim** the environment field is accurate under all conditions. It passed
  experiment ④ (the value tracked the switch), but that is **n=1 positive evidence**.
  If a mismatch is found later, **the identity trace table (M-1)** is the data that locates it.
- ⛔ **It does not claim** an AI can detect its own model. All an AI can do is
  **transcribe a field the system supplied, verbatim** — that is transcription, not perception.
- ⛔ **It does not claim** a per-turn declaration prevents the user from forgetting to switch.
  What it does is **make a forgotten switch visible immediately**,
  instead of three hours later on the bill.
