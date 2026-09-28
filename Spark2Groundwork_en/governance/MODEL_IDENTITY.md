# Model Identity Protocol

**Tier: T1 — spec class.**

> **The enforceable form is `RULES.md` R-09. This file defines current source and continuity rules
> and retains the original experimental context.**
> Moved here from a predecessor project's protocol of the same name and trimmed
> (date dropped from the filename, `R-16`).

Section 1 retains the original incidents and contemporaneous inferences. They are not rerun here or guarantees about all current hosts. Sections 2–5 govern current behavior: no mandatory per-turn declarations or rejection of sourced user confirmation.

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

## 2. Available sources, not platform names

A host may expose a state field, a change event or neither. Inspect what is actually readable rather than assuming that a platform supplies a field on every turn. Record a visible current value faithfully; absence of a field does not invalidate an earlier user-provided source. One positive case cannot guarantee every host or version.

## 3. Rules

### 3.1 Separate the model from its source

Transcribe a readable environment value verbatim. Otherwise, the user's current statement or interface screenshot can provide sourced confirmation. Retain a known family or collaboration name while leaving the full version unknown. Never invent a version or infer the current identity from style, attachments or an old handoff. Record the name, model, source, conversation scope and last confirmation event; record roles separately. A user or UI report is not backend verification.

### 3.2 Continuity within a conversation

Retain a confirmation unless a switch or new conflict appears. Several turns without a visible model field do not revoke it or require repeated questions or headers. A summary can preserve the source and conversation scope. Return to unknown if even that source record is unavailable. A new conversation or instance does not automatically inherit the old model confirmation. A model change does not erase authorship or allow independent review of one's own earlier work.

### 3.3 Eligibility and conflicts

When user or UI information genuinely differs from a readable environment value, present both sources; do not claim agreement or arbitrarily certify one as backend truth. Clarify before an action only when a specified model affects eligibility or authorization for it. Ordinary research and discussion can continue. Complete uncertainty likewise does not block ordinary work or require repeated questions.

### 3.4 Minimal compatible handoff format

Keep attribution in collaboration or handoff records; not every research document needs a model header. The scan remains limited to `attribution_globs` (default `handoffs/*.md`). There is no promise of a new research directory or expanded scanning.

Put each of the three fields on its own line within the first 15 lines, outside example code fences:

```text
[Model: Sol]
[Model source: user]
[Model status: reported]
```

| source / status | Model value and meaning |
|---|---|
| environment / read | A faithfully read model or partial name; no inferred full version |
| user / reported | A model or partial name explicitly given by the user |
| ui / reported | The name visible in a user-provided interface image |
| unknown / unknown | `unknown`; no usable confirmation |
| conflict / conflict | `unknown`; list the disagreeing sources in accompanying prose |

Use the source/status values above; model names have no allowlist. A platform name is not a model. Different values for the same field, incomplete field pairs or incompatible states are rejected. Truthfully declared unknown or conflicting identity produces a notice, not a document failure or a mandatory halt to ordinary work. Add the conversation scope and last confirmation event in prose (for example, "the user just supplied a screenshot in this conversation; full version unknown"); do not guess a timestamp.

Legacy `[Model: claude-opus-5]` tags and existing author fields remain readable. A digit is only a legacy compatibility criterion, not authentication; the missing source is reported. Legacy "cannot read" declarations remain readable without requiring another question. A versionless name without a source needs its actual source recorded; adding a digit to arbitrary text is not verification. The sensor checks record consistency, not whether a user actually said something or which backend is running.

### 3.5 Git checkpoints

A checkpoint name may use a known name or unknown; retain the source in collaboration records without inventing a version. This grants no commit, tag or release permission; existing authorization and tool contracts still apply.

The `--mode ai --model` argument accepts the known name (including `claude`, `gemini`, `gpt`, `Sol`) or `unknown`. It rejects platform names, blank/placeholder values, control characters, `[`/`]`/`|` delimiters and punctuation-only values. This checks the label structure, not whether a backend uses that model. Keep the actual source/status pair in the existing handoff record (§3.4); no extra checkpoint source flag is needed. AI checkpoints never move the human `reviewed` tag.

Historical missing-source notices are counted once in the human sensor output; they are not new errors and need no per-file backfill. `sensor_model_attribution.py --json` retains every path and finding. Every invocation scans the full configured scope; missing/contradictory new fields and unknown/conflict notices remain visible.

### 3.6 Switch events and truncation

A switch triggers renewed confirmation. Update the current record while retaining earlier authorship. A temporarily absent field is not evidence of a switch. Do not conceal loss of source information with a platform name.

#### 3.6.1 Retained historical case

The following case was already recorded in the earlier protocol. It is not a new run or a guarantee about every platform.

A predecessor project's git-audit handoff packet carried the author field `[Model: Antigravity]`.
The user established that the model was in fact **3.1 Pro**, and obtained that model's own account:
the workspace conversation had grown long, earlier context had been **truncated** by the system,
and **the change marker was no longer inside the visible window**. The output `Antigravity` was
a fall-back to the generic name in the system prompt. That system prompt states only
"You are Gemini, a large language model built by Google" and "designed by the Google Deepmind team" —
**⛔ it carries no version number.**

#### 3.6.2 Limits of the case

A change event can disappear after truncation. Continuity relies on a still-visible source record applicable to this conversation. This case cannot establish that every platform always has or always lacks a signal.

#### 3.6.3 Required boundaries

Record unknown when unknown; a platform is not a model. User confirmation may restore a known name and its source should persist. Ask only when eligibility requires it or a genuine conflict needs resolution, not on every turn.

### 3.7 A field changes location

A verbatim value elsewhere in readable system content may be recorded with its actual location. If unavailable, follow 3.1: accept sourced user confirmation or record unknown. Do not claim to have read a nonexistent field.

## 4. Limits of the mechanical check

`scripts/harness/sensor_model_attribution.py` checks headers within the configured scope. It does not inspect the backend, store conversations or verify screenshots. Keep a confirmation summary in an existing handoff where useful; no new identity trace table is required for every turn.

## 5. What this protocol does not claim

It cannot guarantee that a model never forgets, authenticate identity from a header, or ensure changed instructions have loaded into existing conversations. Preserve custom rules, preview the update and reload as described in the edition README.
