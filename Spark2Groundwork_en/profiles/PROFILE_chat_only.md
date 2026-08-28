# Profile: a chat window only

**For:** you are using an AI through a web page or a phone app. It cannot read your folder,
and everything moves by copy and paste.

⚠️ **This still works, ⛔ but you take over a few jobs the programs would have done.**
**This profile tells you which ones are not optional.**

---

## 1. Cut it right down: keep three things

| Keep | Why |
|---|---|
| `ledgers/Claim_Ledger.md` | **Lowest cost, highest return.** Maintaining it by hand is entirely workable |
| `ledgers/Conjecture_Ledger.md` | Same |
| `governance/AGENTS.md` | Paste the whole thing at the start of every new conversation |

**Everything else can go, including the automatic checks** —
⛔ **because you will not run them, and a check that never runs is not a check.**

⚠️ **But if you have Python on your computer, strongly consider keeping
`scripts/harness/sensor_claim_ledger.py`.**
**It is the one tool that answers "is this sentence really in the source", and that is exactly
where a chat interface goes wrong most often.**

**If you keep it, keep `corpus/` and `corpus_md/` too** — that is where the source text it
compares against lives.

---

## 2. How each round goes

```
① Open a new conversation and paste the whole of governance/AGENTS.md
② Paste the current state of your ledgers (all of it, or the relevant entries)
③ When you set the task, say it explicitly:
   "For every sentence with a number in it, give me the exact wording from the
    source and the page number."
④ After the AI replies, YOU write the new claims into the ledger
⑤ Every five to ten rounds, paste the ledger to a DIFFERENT company's model and ask:
   "Which of these quotations is most likely to have been invented?"
```

⚠️ **The wording in step ③ matters.**
**Ask for "a source" and you will get a bibliography.
What you need is the exact wording, because that is the only thing you can check.**

---

## 3. The biggest risk here: you cannot tell what changed

**Without version control, ⛔ you have nothing to compare against.**

### The cheapest replacement

**After every meaningful step forward, save a dated copy of the whole ledger:**

```
Claim_Ledger_2026-01-15.md
Claim_Ledger_2026-01-22.md
```

⛔ **Do not overwrite.**
**What you need is not the latest version. It is two versions you can put side by side.**

---

## 4. Checking by hand: one action is enough

**When the AI gives you a number, do this one thing:**

> **Open the source PDF and use Ctrl+F (Cmd+F on a Mac) to search for the exact wording
> it gave you.**

⚠️ **If you cannot find it, ⛔ do not ask the AI "did I get that wrong?"**
**Start from the assumption that the sentence does not exist.**

**This is not paranoia.** The first incident recorded in an earlier project had exactly this
shape: four figures, none of which appeared anywhere in the source,
**and the source's actual conclusion pointed the opposite way.**

---

## 5. Build your own bibliography authority

**This step matters more here than in any other setup**, because no program is checking
anything for you.

1. Manage your references in **Zotero** or **EndNote**
2. Export the whole bibliography and paste it into `corpus/BIBLIOGRAPHY.docx`
3. **From then on, every citation follows that file, ⛔ not what the AI says**

⚠️ **Why:**
**an AI will get DOIs, page numbers and years wrong, and a wrong one reads exactly like a
right one.** "Are these good papers?" is a question it can answer; "is this DOI correct?" is
not — **⛔ and both answers arrive with the same confidence.**

---

## 6. How the framework keeps getting better here

⚠️ **You lost the automatic checks. ⛔ You did not lose the habit of writing down what went
wrong** — and in this setup that is the best-value thing you can do.

### 6.1 Keep a plain-text incident log

**Keep `my/MY_INCIDENTS.md`** (or just start a text file of your own).

**Whenever the AI makes a mistake worth remembering, ask it there and then to write a short
entry covering four things:**

| What to write | Why |
|---|---|
| What you had asked for | **The same kind of task produces the same kind of mistake** |
| What it did | The fact |
| How you noticed | ⚠️ **The most useful column** — it tells you which of your checks actually work |
| How to avoid it next time | Must turn into a concrete action, ⛔ not "be more careful" |

### 6.2 Fold it into your opening paste

🔴 **This is the advantage that only the chat setup has: you re-paste your opening every round,
so a rule change takes effect immediately.**

**Every three to five logged incidents, do this:**

> Paste the log to the AI and say:
> "From these, give me three to five rules I should add to the text I paste at the start
> of every conversation."

**Then add them to your opening paste.**
⛔ **You choose which ones go in** — **because they will bind both of you from then on.**

### 6.3 What this gets you

**After a while, the text you paste gets longer, ⛔ and considerably sharper.**
**It slowly turns into a set of defences against the mistakes that your topic and your AI
actually produce** — ⚠️ **and it is yours, so it still works when you move to a different
chat interface.**
