# Profile: multiple AI roles

**For: two or more AIs with divided duties, using **at least two different vendors**.**

---

## 1. Three roles

| Role | Duties | Suggested model |
|---|---|---|
| **Governance** | Incident log, process maintenance, governance docs, sensors | Primary model |
| **Research** | Content iteration: reading sources, analysis, hypothesis testing | Primary model |
| **Audit** | Adversarial audit. **Produces nothing, fixes nothing** | ⚠️ **Must be a different vendor** |

⛔ **If auditor and audited are the same model, this layer does not exist.**
**The two models have different blind spots; that is the entire reason for pairing them.**

## 2. Three contact surfaces, **all passing through the human**

| Surface | Rule |
|---|---|
| **Ledgers** | ⛔ No AI writes here. Report via decision request → you adjudicate → governance role executes |
| **State documents** | One per line, **neither writes to nor copies from the other** |
| **`handoffs/`** | All three may write. ⚠️ **Filenames must carry a role prefix or they will overwrite each other** |

## 3. `framework_config.py` setting

```python
"write_scopes": {
    "governance": ["governance", "policy", "scripts", "file_index.md", "NEXT_SESSION_MEMO.md"],
    "research":   ["research", "corpus_md", "RESEARCH_MEMO.md"],
    "audit":      ["scratch"],          # sandbox; the report goes to handoffs/
    "_shared":    ["handoffs"],
}
```

⚠️ **Giving the audit role a sandbox is necessary.**
A predecessor project demanded adversarial audit without providing anywhere to run tests —
**which asks the auditor either not to test or to go out of scope.**

## 4. The **specific** risks of a multi-role setup

### 4.1 Snapshot at handover, not at end of session

⚠️ **If two lines work between the same two checkpoints, changes cannot be attributed** —
you will see a pile of diffs and not know who made which.

### 4.2 The governance role must also file handoff packets

⚠️ A predecessor project's governance role wrote only its own memo for a long time;
**the result was that other roles only learned a rule had changed the next time they violated it.**

⛔ **Any change affecting another party's permissions, specs, or tool behaviour requires a packet naming the recipient.**

### 4.3 Who audits the governance role

**This is the most commonly missed link, because the person proposing it is usually the governance role itself.**

**Triggers (not every round):** sensor code changed, T0 changed, write scope changed, new incident logged.

**Four governance-layer attacks, distinct from the research layer:**

| # | Question |
|---|---|
| G-1 | **How many versions does this rule have?** Are they consistent? |
| G-1b | **Would the new rule and some existing rule be mutually exclusive if both were obeyed?** Especially **rule layer vs tool layer** |
| G-2 | Which layer does this change touch, and **which layer will it force to change**? |
| G-3 | **Are both halves of the new check's paired fixtures present?** |
| G-4 | **Has the cost of this exclusion or exemption been written down?** |

⚠️ **Where G-1b comes from:** a project wrote "numbers that change do not go into clauses"
and removed a count from its documents in the same round, while an existing sensor's condition was
"no document states the count → FAIL". **Obeying the new rule made the old sensor fail immediately.**
**Both rules were written by the same person, and the conflict only surfaced when both were obeyed at once.**
