# Profile: you and one AI

**For:** just you and one AI assistant, where that AI can read your project folder
(Claude Cowork, ChatGPT Work mode, Antigravity, and so on).

**This is the most common setup, and the one the framework assumes by default.**

---

## 1. What to keep in this setup

| Keep | Why |
|---|---|
| `PROJECT.md` | The one file you write yourself |
| `governance/AGENTS.md`, `governance/WORKFLOW_CONSTITUTION.md` | How the AI is required to behave. ⛔ Delete these and there is no framework |
| `governance/RULES.md`, `governance/Incident_Log.md` | The working rules, and the failure patterns behind them |
| Both files in `ledgers/` | Your ideas, and the source behind each sentence |
| `corpus/`, `corpus_md/` | Your source papers and their plain-text copies |
| `incidents/MY_INCIDENTS.md` | **What went wrong in your project.** Section 5 explains why this is the important one |
| `NEXT_SESSION_MEMO.md` | Where things stood at the end of a round; used to open the next one |
| `scripts/harness/` | The automatic checks |
| The three buttons at the top level | snapshot / review changes / check update |

| Safe to delete | Why |
|---|---|
| `governance/Audit_Protocol.md` | It is for a second model picking holes in the work, and you do not have one |
| The other three files in `profiles/` | You have chosen this one |

⛔ **Do not keep everything just because it looks more complete.**
**A governance document nobody maintains is worse than not having it — it makes you think
somebody is watching.**

---

## 2. What deleting the audit document costs you

**It costs you a second pair of eyes.**

⚠️ This is worth taking seriously: **several of the most important defences in this framework
were not thought of by their author. Another model saw something the author could not see.**
One model working from start to finish will stay blind to whatever it is blind to.

**The cheapest possible replacement is one sentence:**

> Paste this round's output to a **different company's** AI and ask only:
> "Which sentence in here is the author most confident about and I should be most suspicious of?"

**You do not need a full audit procedure. You need one pair of eyes that is not the same model.**

---

## 3. How each round goes

```
snapshot → give the task → the AI works → review changes → you decide → update the ledgers → snapshot again
```

**Neither snapshot can be skipped.**
The first exists so you can see afterwards what this round touched.
The second means "I have read it" — **and the next "what changed" is counted from there.**

---

## 4. The risk specific to this setup: you and the AI form a closed loop

⚠️ **The candidate papers, the counter-examples, the theoretical links you see may all have
been filtered by the AI.**
🔴 **So you will not see what the AI did not think of, and you will not know that you did not
see it.**

**This is not a hypothetical. It follows from the structure** — with one source of information,
that source's blind spot is your blind spot.

### What to do about it: every few rounds, search without the AI

1. **You** run one search in a proper database, **with a 60-minute limit**
2. Produce a plain list. ⛔ **Do not hand it to the AI to tidy up**
3. Compare it against what you have, in three columns:
   **found by both / found only by the AI / found only by you**

🔴 **The third column is the point.**
**If it is empty**, the AI's search was not missing anything obvious.
**If it is not empty**, your space of hypotheses has been filtered all along —
**and until you ran that search, nobody knew it.**

---

## 5. How the framework keeps getting better here

🔴 **This is the most important section in this profile.**

**A framework does not get more useful because its version number went up. It gets more useful
because it recorded what actually went wrong in your project.**
In a solo setup nobody else will do this — **so make it part of the routine rather than
something you have to remember.**

### 5.1 Record it when it happens, ⛔ not "when there is time"

**Whenever you catch the AI doing something worth remembering** — a citation that does not
match, a field filled in carelessly, a confident-sounding judgement it never actually checked —
**ask it there and then to write the case into `incidents/MY_INCIDENTS.md`.**

**One sentence is enough:**

> "Log what just happened in `incidents/MY_INCIDENTS.md`. Say what the task was,
> why you did it that way, and how to avoid it next time."

⚠️ **Changing the status column to "handled" is your decision, ⛔ never the AI's.**
**The reason is simple: if the AI can declare its own mistakes closed, that column stops
meaning anything.**

### 5.2 After a few entries, look for the pattern, ⛔ not the individual case

**One mistake on its own does not help, because the next one will not look the same.**
**What is worth having is the shape that repeats.**

**About every ten rounds, or every three logged cases, ask the AI to do this:**

> "Read `incidents/MY_INCIDENTS.md` and find the patterns that repeat.
> For each one, tell me: is this something an existing rule failed to stop,
> or is there no rule covering it at all?"

**Then you decide whether to add a rule.**
⛔ **The AI may propose; writing it into `governance/RULES.md` is your call** —
**because that rule will bind both of you afterwards.**

### 5.3 What is worth turning into a rule

| Worth it | ⛔ Not worth it |
|---|---|
| The same kind of mistake has now happened twice | It happened once, for a one-off reason |
| The mistake is hard to spot (it looks correct) | Anyone would notice it immediately |
| You can write down a concrete thing to check | The best you can write is "be more careful" |

🔴 **The last row is the test.**
**A rule that cannot be turned into a concrete action reads like a reminder and stops nothing.**

### 5.4 What this gets you

**After a year, your `governance/RULES.md` will not look like anyone else's.**
**That is not drift; that is the point** —
**your copy slowly becomes a set of defences against the mistakes that your topic, your AI and
your working habits actually produce.**

⚠️ **This is also why upgrading never overwrites your material.**
🔴 **The upgrade tool recognises nine names of its own and refuses everything else** —
**your incident log, your ledgers, your papers, `PROJECT.md`, and any folder you created
yourself are all outside its reach.**

---

## 6. Configuration

Open `scripts/harness/framework_config.py` and make sure this is empty:

```python
"write_scopes": {}          # empty for a solo setup. The checks will say "not applicable"
```

**Leaving it empty does not switch a check off. It tells the checks that this project has no
division of roles.**
⛔ **They will honestly print "not applicable" rather than printing "passed".**
