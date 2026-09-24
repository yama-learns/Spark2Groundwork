# Audit Protocol

**Tier: T1 — spec class. Required reading for the audit role before starting.**
**⚠️ Single-AI projects do not run adversarial audits, but automated sensors rely on this file for clauses and self-certification specs; ⛔ keep this file, do not delete (see `profiles/PROFILE_solo.md` §1).**

---

> 🔴 **This protocol governs the audit of research output, ⛔ not the review of governance
> maintenance.** That review is three questions; see
> `governance/WORKFLOW_CONSTITUTION.md` §10.2.
> ⚠️ **Applying this protocol to governance maintenance multiplies its cost — which is
> exactly what §10 exists to prevent.**

---

## 1. What may be used

| Allowed | Forbidden |
|---|---|
| Read-only access to the whole project | ⛔ Writing anywhere except `handoffs/` and the sandbox |
| Running existing sensors | ⛔ Any git command that rewrites the working tree |
| Sandbox testing in `scratch/<topic>_sandbox/` (defined in constitution §6.2) | ⛔ Writing to or proposing edits inside ledgers |
| Writing one-off check scripts (inside the sandbox) | ⛔ **Fixing the defects it finds** |

⛔ **The auditor does not fix things.** Find a defect → write it in the report → the principal
adjudicates → the governance role fixes it.
**An auditor that starts fixing is simultaneously the generator and the checker.**

⚠️ **The auditor must be given a sandbox.** A spec that demands adversarial audit but provides
nowhere to run tests **asks the auditor either not to test or to go out of scope.**

---

## 2. 🔴 Test coverage declaration (**the core of this protocol**)

**Every report must contain "what I tested / what I did not test", and both columns must be filled.**

⛔ **A "what I did not test" column reading "none" counts as not delivered**
(`governance/RULES.md` R-35 ①).
**Every audit has something it did not reach** — ⛔ this section does not restate R-35's reasoning.

### 2.1 The conclusion's scope must match the test matrix

| ❌ Do not write | ✅ Write instead |
|---|---|
| "No significant vulnerabilities remain" | "No defect found in the five scenarios I tested" |
| "Extremely robust" | "The guard correctly blocked under injected failure" |

⚠️ **Case:** one audit tested five scenarios solidly, injecting real faults,
**but did not test three of the fixes already claimed** — and concluded
"no significant vulnerabilities remain".
**That conclusion covered territory outside the test matrix, and the report never said that territory existed.**

### 2.2 Check each claimed fix, one by one

**Three states: tested-and-passed / tested-and-failed / not tested.**
**Why: this is the cheapest coverage audit available — the list already exists; you only have to walk it.**

---

## 3. Tone

| Register | Use |
|---|---|
| **Measured statement** | I injected X and observed Y |
| **Static observation** | I read the code; it says Z |
| **My inference** | Derived from the above, **not directly observed** |

⛔ **The three must not be mixed within one sentence.**

⛔ **Banned:** "extremely", "perfect", "very robust", "airtight", "no holes", "nothing to fix"
**Intensity adjectives are not evidential strength. An AI can deliver a wrong judgement in beautiful prose.**

### 3.1 ⚠️ "Minor finding" is a label that needs challenging

**Case:** an audit labelled a UTF-16 file "minor finding: this is PowerShell behaviour".
**The attribution was correct. That file's BOM bytes crashed two sensors outright.**

> **Any observation labelled "minor", "unrelated", or "environmental" and not pursued
> must carry one extra sentence: "what happens if another part of the system reads this?"**

⛔ **If you cannot answer, you may not label it minor. Labelling something minor is a judgement, not an omission.**

---

## 4. Governance-layer audit

**Triggers:** sensor code changed / T0 changed / write scope changed / new incident logged.

**The five questions for auditing the governance role (`G-1`–`G-5`) are in `profiles/PROFILE_multi_agent.md` §4.**

⛔ **The governance role must not assess whether it needs auditing.**

---

## 5. Report format

```
[Model: ...]
1. Audit target and trigger
2. Test coverage           ← §2, both columns
3. Findings, separated by the three registers
4. Check against claimed fixes ← three states
5. Files written
6. Items needing adjudication
```

⚠️ **Section 6 may say "none", but must state which directions you looked in and found
nothing** (`governance/RULES.md` R-35 ②).

---

## 6. 🔴 Cross-family is not independence (**an open question, ⛔ not a new rule**)

**Constitution §8 item 1 requires the auditor not to be the same model as the auditee,
on the grounds that "two model families have different blind spots."**
**⚠️ One source-verified data point suggests the problem may not be different blind spots
but a shared, directional preference.**

### 6.1 Verified source (`[source-verified]`)

**Source:** Jordán et al. (2026), *MAGIC: Multi-Agent Argumentation and Grammar Integrated Critiquer*, AAAI-26.

| # | Verbatim anchor | Page |
|---|---|---|
| 1 | `Finally, while the Judge LLM prefers the MAGIC feedback 69% of the time, the adjudicator only gave MAGIC prefer- ence 52% of the time, averaged across C1–C5, which could be due to the positive character of the prompt used for our study` | 7 |
| 2 | `the authors note that strong LLMs tend to also prefer LLM-generated responses (Zheng et al. 2023)` | 6 |
| 3 | `Gemma 3 27B without MAGIC wins marginally more often than losing with a 57% winrate against the ground- truth human-written GRE feedback` | 6 |

**Table 5 (p.7), Adjudicator–Judge agreement (Cohen's κ):**

| Criterion | Question | κ_AJA |
|---|---|---:|
| C1 | more relevant to the essay content | 0.211 |
| **C2** | better at highlighting **weaknesses** | **0.476** |
| **C3** | better at highlighting **strengths** | **0.583** |
| **C4** | more **specific and actionable** | **0.139** |
| **C5** | more **helpful for a student overall** | **0.236** |
| Overall | — | 0.382 |

### 6.2 🔴 The audit-relevant number is not 69% vs 52%; it is the C2/C3 vs C4/C5 gap

> **Judging "does this text point out a weakness" — LLM judge and human agree moderately (κ ≈ 0.48–0.58).**
> **Judging "is this text useful, specific, actionable" — agreement drops to κ ≈ 0.14–0.24.**

**Carried over to auditing:**

| Audit question | Closest criterion | What this data hints |
|---|---|---|
| "Does this document contain a defect of type X?" | near C2 / C3 | **An LLM auditor may be usable** |
| "Does this defect matter / should it be fixed?" | near C4 / C5 | ⚠️ **An LLM auditor's judgement may be near-uncorrelated with a human's** |

⚠️ **Note where this lands: exactly on the spot §3.1 already warned about.**
"Minor finding" is a **judgement**, and the table above suggests that is the class of
judgement an LLM makes least reliably.

### 6.3 ⛔ This section authorises no process change

- ⛔ **Do not** amend §1, §2, or constitution §8 on the strength of it.
- ⛔ **Do not** claim from it that cross-model auditing is worthless.
- ✅ **The one operative sentence: an all-green cross-model audit ⛔ must not be treated as
  equivalent to a human audit.**

### 6.4 ⚠️ What this data cannot carry (**read this, or the above will be over-cited**)

1. **It measures a preference between two pieces of feedback, not a defect-detection rate.**
   Those are not the same thing.
2. **The paper offers a different explanation itself:** the second half of anchor 1 attributes
   the 69/52 gap to "the positive character of the prompt" (citing Koutcheme et al. 2024),
   ⛔ **not to LLMs preferring LLM output.**
   ⚠️ But anchor 2 shows the authors **also** acknowledge that preference elsewhere
   (citing Zheng et al. 2023). **Both explanations stand; the paper adjudicates neither.**
3. **Sample:** 48 feedback pairs, 2 annotators plus 1 adjudicator, one domain (GRE essay
   feedback), one judge model (o4-mini). ⛔ **Do not generalise to "all LLM auditing."**
4. **Anchor 3 is the one worth remembering:** even the baseline model without MAGIC beat
   **human-expert-written** feedback 57% of the time in the LLM judge's view.
   **That is harder to explain away with prompt positivity than 69/52 is.**

### 6.5 When to revisit

**On the first case in this project where a cross-model audit came back all-green and a human
review then found a defect** — return to this section and log that case in
`governance/Incident_Log.md`. ⛔ Until then it must not be promoted to a rule.
