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
| `my/MY_INCIDENTS.md` | **What went wrong in your project.** Section 5 explains why this is the important one |
| `NEXT_SESSION_MEMO.md` | Where things stood at the end of a round; used to open the next one |
| `scripts/harness/` | The automatic checks |
| `governance/Audit_Protocol.md` | Defines audit terms, self-certification specs, and sensor clauses. While solo mode does not run a two-model adversarial audit, automated sensors require its clauses and definitions; ⛔ keep it, do not delete |
| All supplied files in `profiles/` | Other profiles remain referenced by `SETUP.md`, governance documents, and checks; keeping them does not activate those collaboration modes |
| Root launchers (including `check_project.bat` / `.command`) | Entries for project checks, snapshots, reviewing changes, saving progress, syncing rules, and checking updates |

⛔ **Do not delete the other profile files to signal that you chose solo.**
`governance/Audit_Protocol.md`, `governance/EXTERNAL_TOOLS.md`, and the checks still refer to them;
removing them makes the reference check fail. Choosing solo changes how you collaborate this round;
it does not activate the roles described by the other profiles.

---

## 2. What you lose without a second model

**It costs you a second pair of eyes.**

⚠️ This is worth taking seriously: **several of the most important defences in this framework
were not thought of by their author. Another model saw something the author could not see.**
One model working from start to finish will stay blind to whatever it is blind to.
(Solo mode keeps `Audit_Protocol.md` for automated sensors, but automated checks cannot replace substantive challenge.)

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
**ask it there and then to write the case into `my/MY_INCIDENTS.md`.**

**One sentence is enough:**

> "Log what just happened in `my/MY_INCIDENTS.md`. Say what the task was,
> why you did it that way, and how to avoid it next time."

⚠️ **Changing the status column to "handled" is your decision, ⛔ never the AI's.**
**The reason is simple: if the AI can declare its own mistakes closed, that column stops
meaning anything.**

### 5.2 After a few entries, look for the pattern, ⛔ not the individual case

**One mistake on its own does not help, because the next one will not look the same.**
**What is worth having is the shape that repeats.**

**About every ten rounds, or every three logged cases, ask the AI to do this:**

> "Read `my/MY_INCIDENTS.md` and find the patterns that repeat.
> For each one, tell me: is this something an existing rule failed to stop,
> or is there no rule covering it at all?"

**Then you decide whether to add a rule.**
⛔ **The AI may propose; writing it into `my/MY_RULES.md` is your call** —
**because that rule will bind both of you afterwards.**

🔴 **⚠️ Into `my/MY_RULES.md`, ⛔ not `governance/RULES.md`.**
**`governance/` is a framework folder and is replaced wholesale on upgrade —
⛔ anything you write there disappears.**
**Number your own rules `P-01`, `P-02`, … ⛔ never continue the sequence as `R-36`**
(the next framework version may use that number itself).

### 5.3 What is worth turning into a rule

| Worth it | ⛔ Not worth it |
|---|---|
| The same kind of mistake has now happened twice | It happened once, for a one-off reason |
| The mistake is hard to spot (it looks correct) | Anyone would notice it immediately |
| You can write down a concrete thing to check | The best you can write is "be more careful" |

🔴 **The last row is the test.**
**A rule that cannot be turned into a concrete action reads like a reminder and stops nothing.**

### 5.4 What this gets you

**After a year, your `my/MY_RULES.md` will not look like anyone else's.**
**That is not drift; that is the point** —
**your copy slowly becomes a set of defences against the mistakes that your topic, your AI and
your working habits actually produce.**

⚠️ **An upgrade never overwrites any of this: `my/`, `ledgers/`, `corpus/`, `corpus_md/`,
`handoffs/`, `PROJECT.md`, or any folder you created yourself.**
🔴 **The upgrade tool recognises a handful of names of its own and refuses everything else.**

> ⚠️ **v1.4.1 corrected something here, and it is worth saying out loud.**
> **Before v1.4.0 this section told you to accumulate rules in `governance/RULES.md`,
> and the next paragraph said "upgrading never overwrites your material" and listed the
> things that were safe — 🔴 ⛔ and `RULES.md` was not on that list. Every word was true,
> and together they led the reader to the opposite conclusion.**
> **⛔ Rules now live in `my/`, and the copy of the framework's rules is watched by
> `sensor_my_rules.py`.**

---

## 6. Configuration

**Open `governance_config.json` in the project root.** ⚠️ **⛔ Not the `.py` file under `scripts/`** —
🔴 **`scripts/` is replaced wholesale on upgrade, and settings changed there disappear.**

**A solo setup needs no changes at all.** The default already reads:

```json
"write_scopes": {}
```

⚠️ **Empty ⛔ does not switch a check off.** **It tells the checks that this project has no
division of roles, so they issue ⛔ no out-of-scope verdict — because they read `git status`
and ⛔ cannot tell your edit from the AI's.**

🔴 **Changes inside the no-write area are still listed** (from v1.4.1):

```
[WARN] 1 change this round falls inside the AI's default no-write area:
       ledgers/Claim_Ledger.md — if you made it yourself this is normal;
       if not, read this list
```

⛔ **⚠️ That is ⛔ not a red light and ⛔ not silence.** **It is a list for you to claim.**
