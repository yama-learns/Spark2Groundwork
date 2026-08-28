# Profile: you use outside AI tools

**For:** Deep Research, automation flows (n8n, Zapier), search agents,
**and anything that runs where you cannot see it and hands you a result.**

⚠️ **This is an add-on, ⛔ not a profile on its own.**
**Use it alongside whichever one you already chose (solo / multi-agent / chat-only).**

---

## 1. One overriding rule

⛔ **Whatever an outside tool hands back is an unverified lead.**
**Its one legitimate use is to tell you that a topic exists.**

⛔ **Until you have gone to the source yourself, do not cite any statement, reference or number
it gave you.**

⚠️ **This is not caution. It was measured.**

**One case:** two different Deep Research models read the same paper.
**Both summaries were wrong, and wrong in opposite directions.**
The part worth noticing came next — to reconcile the two contradictory summaries, someone put
forward a very reasonable-sounding explanation, **and that explanation was wrong too.**

🔴 **Because neither summary was right, any hypothesis built to reconcile them was built on
false data.**

---

## 2. When a report arrives, sort it into five grades

| Grade | What it is | What to do |
|---|---|---|
| **1** | Points to a topic, method or controversy you did not know about | ✅ **The most valuable kind.** Go and find the source |
| **2** | Gives specific references | ⚠️ Check each one against your bibliography. **The identifiers are often wrong** |
| **3** | Gives numbers | ⛔ **Always go back to the source.** Until you have, it goes in no file |
| **4** | Gives a conclusion or a judgement | ⛔ **Treat as unverified without exception** |
| **5** | Has nothing to do with your question | Discard. **⚠️ This is the only reason to discard something outright** |

🔴 **A technique worth using: run the same instructions past two models and look at where they
disagree.**

**The disagreements are the highest-value output** —
**each one marks a place where at least one of them is wrong, ⛔ and that is exactly where you
should be opening the source.**

---

## 3. Instructions to an outside tool must stand on their own

⛔ **Every set of instructions you send out must be completely self-contained.**
**⛔ No "as above", "see previous", "same as R1".**

**The reason is mechanical:**
each run of an outside tool happens in its own separate conversation. ⛔ **They share no
context.** **"As above" is a blank at the other end** — the clause you thought you had given
it simply does not exist in that run.

**A measured consequence:** one set of instructions quoted this very rule at the top,
**and then wrote "Same as R3-1" further down.**
🔴 **The marker it referred to was used 0 times in that run; the version that spelled the
clause out was used 12 times.**
⚠️ **Quoting the rule and breaking it, in the same file.**

**Before sending, you can check with:**

```
python3 scripts/harness/sensor_prompt_self_contained.py <your-instructions.md>
```

---

## 4. Extra care with automation flows

| Risk | What to do |
|---|---|
| **Intermediate output nobody looks at** | Every node's output lands in a file, **with a timestamp in the name** |
| **Failures swallowed** | ⛔ No silent retry on failure. **A failure must leave a record** |
| **Writing into the ledgers automatically** | ⛔ **Never** |

🔴 **The most dangerous thing about automation is that it makes "nobody looked at this" a state
with no trace.**
**And the entire premise of this framework is to make "did anyone look at this" a question you
can answer.**

---

## 5. Where outside reports go

**Make a folder in your project:**

```
external/          ← the raw reports, stored and never edited
```

⛔ **Do not put them in `corpus_md/`.**

**The reason is worth remembering:** everything in `corpus_md/` is **text a program pulled out
of a source PDF**, and it is what the "is this quotation really in the source" check compares
against.
🔴 **The moment AI-written text is mixed in, that check stops meaning anything — you will match
against a sentence the AI wrote itself, and conclude that yes, it is in there.**

⚠️ **Upgrading does not touch `external/`** — **the upgrade tool recognises nine names of
its own and refuses everything else.**
⛔ **It does not back it up for you either.** If there is something in there you cannot lose,
⛔ keep your own copy.

---

## 6. How the framework keeps getting better here

**Outside tools go wrong in their own ways, ⛔ and those ways are not the same as your everyday
AI's.** So they deserve a record of their own.

### 6.1 What you record is "which instruction produced which mistake"

**Every time an outside report is clearly wrong, add an entry to `my/MY_INCIDENTS.md` —
but with the weight in a different place:**

| What to write | Why |
|---|---|
| **The exact instructions you sent** | 🔴 **The most important column** — most outside-tool errors come from instructions that did not say enough |
| What was wrong | The fact |
| **Which of the five grades above it was** | Over time you will see which grade this tool is least reliable at |

### 6.2 What accumulates is a better instruction template, ⛔ not a new rule

🔴 **This is the biggest difference between this profile and the others.**

**In the solo and multi-agent setups, accumulated incidents turn into a new rule.**
**With outside tools, accumulated incidents turn into a rewritten set of instructions** —
**because you do not control how the tool behaves. ⛔ You only control what you hand it.**

**In practice: put the fix into your own template under `prompts/`, and use that one next time.**

### 6.3 What this gets you

**You build up a set of instruction patterns that work for this particular tool.**
⚠️ **They usually do not transfer** — **a different tool means starting again.**
🔴 **That fact is itself worth writing down, ⛔ so that next time you do not assume it carries
over.**
