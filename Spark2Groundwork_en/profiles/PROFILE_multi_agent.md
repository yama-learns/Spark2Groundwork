# Profile: several AIs with separate jobs

**For:** you use two or more AIs at once, and **at least two of them are from different
companies.**

⚠️ **If all your models come from one company, this profile buys you much less** —
**section 1 explains why.**

---

## 1. Three roles

| Role | Responsible for | Which model |
|---|---|---|
| **Governance** | Maintaining rules, logging incidents, maintaining the checks | Your main model |
| **Research** | The content itself: reading papers, analysis, testing hypotheses | Your main model |
| **Audit** | Finding holes. ⛔ **Produces nothing and fixes nothing** | 🔴 **Must be a different company's model** |

🔴 **If the auditor is the same model as the one being audited, that layer is doing nothing.**

**The reason is not that it would favour itself. The reason is that it cannot see.**
A model has its own blind spots — it will not notice what it left out,
in the same way that you do not notice the thing you did not think of.
**Switching companies switches the set of blind spots.**

⚠️ **This is why "two companies" matters more than "two models".**
Two models from the same company have blind spots that overlap heavily.

---

## 2. Three points of contact, ⛔ all of which go through you

| Contact point | Rule |
|---|---|
| **The two ledgers** | ⛔ **No AI writes to them directly.** An AI files a "please decide" request → you decide → the governance role writes it in |
| **State documents** | **One per line of work**, ⛔ never writing into each other's, never copying each other's content |
| **`handoffs/`** | All three roles may write here. ⚠️ **Filenames must carry a role prefix, or they will overwrite each other** |

**Why the ledgers must go through you:**
A ledger records **what you have confirmed**.
**If an AI writes straight into it, that column no longer means anyone confirmed anything.**

---

## 3. How each round goes

```
You press "snapshot"
   → give the research role its task           → it hands back a packet
   → give the governance role its task          → it hands back a packet
     (only if rules are changing this round)
   → you press "review changes" and see what each side did
   → you decide → the governance role writes the decision into the ledgers
   → you press "snapshot" again
```

### 3.1 Save at every handover, ⛔ not at the end of the day

⚠️ **If two lines of work happen between the same two checkpoints, the changes cannot be
attributed.** You will see a pile of edits ⛔ **and be unable to tell who made which.**

**Press "snapshot" every time you switch roles.** It is the cheapest, most effective single
habit in this setup.

### 3.2 The governance role hands over packets too

⚠️ **This gets missed easily, because what the governance role produces is "rules", which does
not feel like output.**

**But when a rule changes and nobody is told, the consequence is that the other roles find out
the next time they break it.**

⛔ **If a change this round affects anyone else's permissions, formats or tool behaviour, it
gets a handover packet with a named recipient.**

---

## 4. Who audits the governance role

🔴 **This is the easiest part of the whole structure to miss — because the person who would
think of the question is usually the governance role itself.**

**You do not need to audit every round. Audit when one of these four happens:**
a check was changed, the behaviour rules were changed, a write scope was changed,
or a new incident was logged.

**Auditing the governance role asks different questions than auditing research:**

| # | The question |
|---|---|
| **G-1** | **How many versions of this rule now exist?** Do the different files agree? |
| **G-2** | **Could this new rule and an existing rule be impossible to obey at the same time?** |
| **G-3** | Which layer did this change touch, **and which layer is now forced to change as well**? |
| **G-4** | **Does the new check have both kinds of sample — "must alarm" and "must not alarm"?** |
| **G-5** | This exception that was granted — **has its cost been written down?** |

⚠️ **G-2 deserves a sentence more, because it is the hardest to catch yourself.**

**A real example.** In a single round, two things happened:
a new rule said "do not write numbers that will change into the rule text", so the counts were
removed from the documents;
and an existing check had the criterion "no count stated in the document → fail".
🔴 **The moment the new rule was obeyed, the old check failed.**
**Both rules were written by the same role, ⛔ and the conflict only appeared at the moment
somebody tried to obey both.**

---

## 5. How the framework keeps getting better here

🔴 **This is where several roles pay for themselves.**

**In a solo setup you have to remember to write incidents down. Here you can make it one
role's job.**

### 5.1 The governance role maintains the log; ⛔ you close the cases

🔴 **Each role has its own start-up prompt. Paste the whole file into a new conversation:**

| Role | Paste this |
|---|---|
| Governance | `prompts/START_governance_AI.md` |
| Research | `prompts/START_research_AI.md` |
| Audit | `prompts/START_audit_AI.md` |

**Logging incidents is already written into the governance role's file** —
**⛔ you do not need to say it again yourself.**

⚠️ **Changing the status to "handled" is still yours alone.**
**Same reason as the ledgers: if a role can declare its own case closed, that column stops
meaning anything.**

### 5.2 A second use for the audit role: finding the pattern

**About every ten rounds, hand the whole of `my/MY_INCIDENTS.md` to the audit role and
ask:**

> "Which of these incidents are actually the same mechanism wearing different clothes?
> For each mechanism, tell me why the existing rules did not stop it."

🔴 **Give this to the audit role rather than the governance role.**
**The rules that failed to stop those incidents are the governance role's own** —
**and asking anyone to find the holes in their own rules is much harder than asking somebody
else.**

### 5.3 You decide on new rules; ⛔ the proposer does not approve their own

**Fix the sequence:**

```
Audit proposes → Governance assesses feasibility and cost → You decide → Governance writes it into my/MY_RULES.md
```

⛔ **Never let the proposer approve their own proposal.**
**This is not distrust. It is that the proposer has already been convinced by their own idea** —
**they cannot weigh its cost, because in their eyes the cost is worth paying.**

### 5.4 What this gets you

**A rule set that fits your topic more closely every month, where every rule has been through
three hands: someone proposed it, someone costed it, someone decided.**

⚠️ **It is slower than the solo setup, ⛔ and sturdier** —
**a solo rule has only ever been read by one person.**

---

## 6. Configuration

**Open `governance_config.json` in the project root** and state the write scopes:

```json
"write_scopes": {
  "governance": ["governance", "policy", "scripts", "my",
                 "file_index.md", "NEXT_SESSION_MEMO.md"],
  "research":   ["corpus_md", "RESEARCH_MEMO.md"],
  "audit":      ["scratch"],
  "_shared":    ["handoffs"]
}
```

⚠️ **Giving `audit` only a sandbox is deliberate: real reports go to `handoffs/` (`_shared`).**

🔴 **⚠️ ⛔ Do not edit `scripts/harness/framework_config.py`.**
**That is a framework file, replaced wholesale on upgrade — ⛔ settings changed there
disappear, and nothing tells you.**
**⚠️ `governance_config.json` is on the upgrade tool's never-replace list.**

⛔ **A misspelled key is not silently absorbed**: the sensor FAILs and names the closest valid key.

🔴 **`scratch/` does not come with the framework — ⛔ you create it yourself.**
**Just make a folder called `scratch` at the top level of your project.**
⚠️ **Leaving it out is deliberate: `scratch/` is defined as the place that is not under
version control, ⛔ and a sandbox that is under version control is no longer a sandbox.**

⚠️ **The audit role must have a sandbox (`scratch/`).**
**If you ask it to run adversarial tests but give it nowhere to make a mess,
⛔ you are asking it to either not test or overstep.**

⚠️ **Nothing in `scratch/` is under version control, ⛔ so nothing in it may be cited.**
**A citation into it reads exactly like a well-founded one, ⛔ and points at something that can
vanish at any moment.**
