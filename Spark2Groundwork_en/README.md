# Spark2Groundwork

**Turn a spark of an idea into a research proposal that holds up.**

---

## There are only three things you have to do

| What | Where |
|---|---|
| **Fill in one file** | `PROJECT.md` in this folder. ⛔ Every other document is looked after by the AI |
| **Press three buttons** | snapshot / review changes / check update (`.bat` on Windows, `.command` on Mac) |
| **Decide** | The AI proposes; you decide whether to accept. **This part cannot be handed off** |

⚠️ **When a new version of the framework comes out you can swap it in wholesale, ⛔ and your
own material — your ideas, your quotations, the papers you added — is never touched.**

---

## 0. What this is

**A set of files you copy into your project folder.**
They give the AI a set of working rules, and they give you a way of checking what it did.

It starts from one assumption: **the AI will be wrong, and it will be wrong in the places
where it sounds most certain.** Every working rule in here corresponds to something that
actually happened.

| The question it helps you answer | What answers it |
|---|---|
| **Which page of the original paper does this statement rest on?** | The Claim Ledger, plus a check that compares your quote against the source |
| **What would it take to prove this idea wrong?** | The falsification field in the Conjecture Ledger |
| **What did the AI just change, and have I looked at it?** | Git checkpoints, plus the "review changes" button |

---

## 1. What it does not claim (**please read this first**)

⛔ **This framework does not promise your research is correct.**
It promises something narrower and more useful:
**when something goes wrong, it leaves a trace instead of quietly becoming your conclusion.**

| It can check | It cannot check |
|---|---|
| Whether the sentence you quoted is really in the source paper | Whether the source paper actually **supports your reasoning** |
| Whether you filled in the falsification condition | Whether what you wrote there is **something you could really observe** |
| Whether the same working rule exists in two versions | Whether that working rule itself is **right** |

**The right-hand column is human work, and we leave it that way on purpose.**
A check that fires on correct work teaches you to ignore it — **and that is worse than having
no check at all.**

---

## 2. What is in this folder

<p align="center">
  <img src="docs/fig1_architecture.svg" alt="Architecture: what belongs to the framework and what belongs to you" width="100%">
</p>

⚠️ **Everything above the red line belongs to the framework — if the AI breaks it, download it again.**
🔴 **Everything below the line is yours, and nothing anywhere can restore it. Keep your own backup.**

```
SETUP.md              ← 🚩 Start here. Install, fill in, first run
INITIALIZE_PROMPT.md  ← The text you paste to your AI the first time
PROJECT.md            ← The only file you have to write yourself
corpus/               ← Your source PDFs go here, and your bibliography
corpus_md/            ← The plain text pulled out of those PDFs, used for checking quotes
ledgers/              ← Your ideas, and the source behind each sentence
governance/           ← The rules the AI works under
policy/               ← Rules by topic: sources, handovers, model identity, outside tools
profiles/             ← Pick the one that matches how you work
prompts/              ← Ready-made instructions you can paste
scripts/harness/      ← The automatic checks
```

---

## 3. Four core ideas

<p align="center">
  <img src="docs/fig2_workflow.svg" alt="Workflow: the evidence chain, who watches it, and the loop" width="100%">
</p>

### 3.1 Getting from "what the paper says" to "what you conclude" takes several steps

A sentence with a number in it passes through seven steps on its way from an idea to your
proposal. **Each one can break, and each breaks in its own way.**

| Step | The question | Can it be checked automatically? |
|---|---|---|
| ① Locate | Which passage should I be citing? | ❌ Human work |
| ② **Exists** | **Is that passage really in the source?** | ✅ **Yes, and it costs nothing** |
| ③ Fields | Have the required fields been filled in? | ✅ Yes |
| ④ Consistency | Do the different files agree with each other? | ✅ Yes |
| ⑤ Real | Does this reference actually exist? | ✅ Yes, but it needs an outside lookup |
| ⑥ Support | Does that passage bear the weight of this claim? | ❌ Human work |
| ⑦ Generalisation | Can you go from that study to yours? | ❌ Human work |

🔴 **Step ② is what the whole design rests on.**
It turns "did anyone actually open the source and read it" into a fact
**you can settle by comparing text.**

### 3.2 Two ledgers, two different jobs

| | Conjecture Ledger | Claim Ledger |
|---|---|---|
| Covers | **The idea**: does this hold up at all? | **The sentence**: which passage is it standing on? |
| Main fields | What would prove it wrong; the strongest rival explanation | The exact wording quoted, and the page |
| What goes wrong | An idea slowly becomes something nothing could disprove | A number gets rewritten from memory |

### 3.3 Mistakes get logged automatically, and the framework improves itself

**Working out a fix for one mistake buys you little**, because the next one will not look the
same. What is worth writing down is the **pattern** — so that you recognise it next time.

**And finding the pattern is a job you can hand to the AI.**
You say "log that" at the moment it happens; it does the rest.
🔴 **So the framework grows as you use it, and ends up in the shape that suits you best.**

**The failure patterns that come with the framework are in `governance/Incident_Log.md`;
what went wrong in your own project goes in `incidents/MY_INCIDENTS.md`.**

### 3.4 You are the one who decides

⚠️ **This is not caution. It is a measured result.**
Across two earlier projects, **the user caught more genuinely new errors than any other part
of the system**, and their most effective method was not "spotting a wrong answer" but
**bringing in a piece of information the AI did not have.**

**→ Any proposal to take the user out of the loop has to answer one question first:
who takes over that job?**

---

## 4. There is no perfect framework — only one that gets better as you use it

🔴 **This section is the idea the whole thing is built on.**

**No framework arrives already suited to your topic, your AI and your working habits.**
⛔ **We are not going to pretend otherwise.**

**It is built on a different premise: every hole you fall into becomes a railing for next time.**

| What you do | What the framework grows |
|---|---|
| Catch the AI getting something wrong and say "log that" | One more entry in `incidents/MY_INCIDENTS.md` |
| After a few entries, ask the AI to find the repeating patterns | You see a shape that **will happen again** |
| You decide whether it becomes a rule | One more line in `governance/RULES.md` — **and it is specific to your project** |

⚠️ **The middle step is not optional.** One mistake on its own does not help, because the next
one will not look the same; **what is worth having is the shape that repeats.**

⛔ **The last step is always your decision, never the AI's** —
**because that rule will bind both of you afterwards.**

**After a while your rule set will not look like anyone else's.**
🔴 **That is not drift. That is the point.**

⚠️ **It is also why upgrading never overwrites your material — and the reason may be the
opposite of what you expect:**
🔴 **the upgrade tool recognises nine names of its own and refuses everything else.**
**So your ledgers, your papers, your incident log, `PROJECT.md`,
and ⛔ any folder you created yourself are all left alone** —
**you never have to register them on a list.**

---

## 5. Where this came from

**Two real research projects, and forty-odd recorded mistakes between them.**
Every check and every hard working rule here carries the case that forced it into existence.

⛔ **A working rule without a real case does not get written in.**

⚠️ There is one exception, and it is the reason this framework exists:
the patterns marked `[inherited]`, `[framework's own]` or `[predicted]` in
`governance/Incident_Log.md` **have not happened in your project.**
They are listed so you know what to watch for — ⛔ **not so you can assume you are safe.**

---

## 6. Next step

👉 **Open `SETUP.md` and follow it.**

---

## Licence

**Released under the MIT licence**, from https://github.com/yama-learns/Spark2Groundwork

⚠️ **That covers the framework files only.**
**The research you produce with them is yours** — ⛔ this framework claims no rights over your
work, and takes no responsibility for it.
