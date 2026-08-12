# Handoff Packet Specification

**Tier: T1 — spec class.**

---

## 1. Why handoffs must be files

**No persistent orchestrator, no shared memory, AIs do not talk to each other.**
**Files are the only channel that survives across roles, platforms, and sessions.**

⛔ **Any scheme replacing it with conversation, memory, or verbal relay is, in this topology, no handoff at all.**

## 2. Filename

```
handoffs/<role>_<YYYY-MM-DD>_<two-digit seq>_<topic>.md
```

**`<role>` values (⛔ do not invent):**

| Situation | Value |
|---|---|
| Single AI | `agent` |
| Multiple roles | `governance` / `research` / `audit` |

⚠️ **This table was added from the framework's own live test** — the tested agent had no
value available and invented a category name.
**That is the entry point of failure family ③ "required fields induce fabrication",
except what gets fabricated is a category rather than a number.**

⚠️ The filename rule itself once lived in a document whose first line said "agents need not read this" —
**the only filename rule, placed in the one document readers were told to skip.**

## 3. Five required sections (**missing one ＝ not delivered**)

```
[Model: ...]            ← read verbatim; ⛔ never a platform name

## 1. What I claimed this round
## 2. What I independently verified / what I only restated / what is my inference
## 3. What I did not finish, and its exact boundary
## 4. Which files I wrote
## 5. What I believe needs adjudication
```

### 3.1 How to write section 2 (**the most important one**)

| Column | Content |
|---|---|
| **What I independently verified** | **With a command or steps you can re-run** |
| **What I only restated** | And **why it could only be restated** |
| **My inference** | ⚠️ Marked explicitly, **never mixed into the same sentence as the other two** |

⛔ **If section 5 says "none", state which directions you looked in and found nothing.**
**"Found nothing" and "did not look" read identically on the page, and carry very different information.**

### 3.2 Section 3 must not say "everything complete"

**Every round has something unfinished.** "None" is not full coverage; it is not having taken stock.

## 4. Recipient's obligations

| Step | Action |
|---|---|
| 1 | Confirm all five sections present |
| 2 | **Spot-check "what I independently verified" — starting with the most confident claims** |
| 3 | Register candidate claims in the ledger, run the sensors |
| 4 | Overwrite the state document |

⚠️ **Step 2's ordering is not a typo.**
**Across two predecessor projects, forty-odd incidents almost all occurred where the author was most certain.**

## 5. Archiving

**When every decision request in a packet has been adjudicated and the outcome has landed,
move the packet to `archive/handoffs/`.**

⛔ **The criterion is "the adjudication has landed", not "time has passed".**
Archiving by age sweeps away packets that were never handled, **and that loss is silent.**
