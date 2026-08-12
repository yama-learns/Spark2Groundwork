# Audit Protocol

**Tier: T1 — spec class. Required reading for the audit role before starting.**
**⚠️ Single-AI projects may delete this file, but read `profiles/PROFILE_solo.md` §1 for the compensation first.**

---

## 1. What may be used

| Allowed | Forbidden |
|---|---|
| Read-only access to the whole project | ⛔ Writing anywhere except `handoffs/` and the sandbox |
| Running existing sensors | ⛔ Any git command that rewrites the working tree |
| Sandbox testing in `scratch/<topic>_sandbox/` | ⛔ Writing to or proposing edits inside ledgers |
| Writing one-off check scripts (inside the sandbox) | ⛔ **Fixing the defects it finds** |

⛔ **The auditor does not fix things.** Find a defect → write it in the report → the principal
adjudicates → the governance role fixes it.
**An auditor that starts fixing is simultaneously the generator and the checker.**

⚠️ **The auditor must be given a sandbox.** A spec that demands adversarial audit but provides
nowhere to run tests **asks the auditor either not to test or to go out of scope.**

---

## 2. 🔴 Test coverage declaration (**the core of this protocol**)

**Every report must contain "what I tested / what I did not test", and both columns must be filled.**

⛔ **A "what I did not test" column reading "none" counts as not delivered.**
**Every audit has something it did not reach. "None" is not full coverage; it is not having taken stock.**

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

**The four attacks are in `profiles/PROFILE_multi_agent.md` §4.3.**

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

⚠️ **Section 6 may say "none", but must state which directions you looked in and found nothing.**
**"Found nothing" and "did not look" read identically, and carry very different information.**
