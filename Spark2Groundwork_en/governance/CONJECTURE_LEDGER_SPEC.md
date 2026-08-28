# Conjecture Ledger Spec

**Tier: T1 — specification class. ⚠️ This file is replaced wholesale by a framework upgrade.**

> 🔴 **This file defines conjecture states and thresholds; `ledgers/Conjecture_Ledger.md` holds the conjectures.**
> **⚠️ Why they are separate: constitution §6.4 (⛔ not restated here).**

---

## 0. How to use it

### 0.1 Six states

| State | Meaning | May it serve as a premise |
|---|---|---|
| 🔵 **Conjecture** | Unverified; falsifiability not yet established | ❌ No |
| 🟡 **Falsifiable** | Falsification condition and rival hypothesis both filled and sound | ❌ Not as a premise, but usable as a research hypothesis |
| 🟢 **Literature-supported** | A source supports it, and that source actually says so | ✅ Yes, with source and location |
| 🔴 **Refuted** | Current evidence runs against it | ❌ No. **Keep the record; do not delete** |
| ⚫ **Unfalsifiable (retired)** | After attempts to split it, still yields no observable falsification condition | ❌ No. **Keep the record; do not delete** |
| 🟤 **Dormant** | Uncited for several rounds and outside the current scope | ❌ Not as a premise. **Record fully preserved** |

### 0.1a 🟤 Dormant ≠ ⚫ Retired

| | Retired ⚫ | Dormant 🟤 |
|---|---|---|
| What it asserts | Unfalsifiable in principle | **Asserts nothing** |
| Registration cost | Four items (§0.1b) | One line: dormancy date ＋ **wake condition** |
| Reversible | Requires a new ID | Change the state |

⛔ **Dormancy requires a wake condition, not just a date.** Dormancy without one is silent deletion.
⛔ **Sensors never downgrade automatically.** Automatic downgrade turns "nobody mentioned it"
into "it does not matter" — **and those are different things.**

⚠️ **Why dormancy is needed:** during ideation, conjectures are generated far faster than they
are retired — **that is the nature of the stage, not a discipline problem.**
If the only exit is an expensive retirement, **"do nothing" costs zero, so it becomes the default.**

### 0.1b Threshold for ⚫ retirement

"Unfalsifiable" comes in two forms; **only one should be retired**:

| Form | Description | Handling |
|---|---|---|
| **(a) Unfalsifiable in principle** | However you split it, no result would make it false | ⚫ **Retire** |
| **(b) Current wording unfalsifiable** | The claim has content, it is just written too broadly | 🔵 **Keep**, list as pending split |

⚠️ **Retirement requires at least one recorded splitting attempt first.**
**Allowing "cannot fill the field → just delete" rewards not trying —
filling a field is easier than splitting a claim, and deleting is easier than either.**

### 0.2 Required fields per conjecture

```
### C-NN | <state> | <scope>

**Statement:**        One sentence, readable standalone, context-independent
**Origin:**           Where this conjecture came from
**Falsification:**    Which observable result would refute it. If you cannot say, write "—"
**Falsification adjudicated:** `pending` / `adjudicated` — ⛔ only a human may set `adjudicated`
**Why I could not fill this:** **Optional.** When Falsification is "-", say here why
                      ⚠️ **Same wording as `prompts/TEMPLATE_decompose.txt` rule 3.**
                      ⛔ Field names are rules too, and a rule has one home
                      (`governance/WORKFLOW_CONSTITUTION.md` §3.2)
                      ⚠️ Filling it makes the sensor report
                      `FALSIFICATION_DECLARED_UNFALSIFIABLE` rather than "condition empty"
                      — **because those are two different states**
**Strongest rival:**  Name it specifically. ⛔ Not "some scholars disagree"
**Rival's differing prediction:** What the rival predicts, and where the two diverge
**Basis:**            🟢 name source and location; 🔴 name the refuting evidence
**Log:**              Creation date and state-change trail
```

**"Scope" values (⛔ do not invent):** `main line` / `candidate pool`
(single-line projects: always `main line`).

### 0.3 Six hard rules

1. Falsification conditions must be **observable**.
   🔴 **Writing "—" is not worse than making something up. This is by design.**
   ⚠️ **Why (measured):** if the sensor only fires on an empty field,
   **honest blankness gets a warning while a plausible-sounding fake condition does not** —
   **and nobody, human or sensor, can tell the fake from the real one. The incentives run backwards.**
   → **The warning condition is "not yet adjudicated by a human", not "field is empty".**
   **Filling in text does not clear the warning; only a human marking it `adjudicated` does.**
   ⛔ **AI must not set `Falsification adjudicated` to `adjudicated` on its own.**
2. Rival hypotheses must be specific enough to yield a **different observable result**.
   **A decorative rival is worse than none.**
3. 🔴 and ⚫ entries **must not be deleted** — **deleting the record makes the same claim
   get re-proposed a few rounds later with nobody knowing it was already tested.**
4. State changes require **independently checkable** grounds.
5. ⛔ **AI must not write to this ledger**; report via decision request.
6. A statement is **frozen once registered**; to change it, register a new ID noting supersession.

### 0.4 ID namespaces (⛔ do not mix)

| Prefix | Use |
|---|---|
| `C-NN` | **Conjectures** (two digits) |
| `M-NN` | **Claims** (Claim Ledger) |
| `W-n` | Work items |
| `R-n` | Pending decisions |

⚠️ **Work items must always carry the prefix.** Written as `C-1`, a sensor will
**silently** treat it as a citation of conjecture C-01 and let it through.

---
