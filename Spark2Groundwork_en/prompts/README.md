# Prompt library

**This folder holds text you can paste straight to an AI.**

| File | When to use it |
|---|---|
| `START_governance_AI.md` | Paste as the first message when you put an AI in the **governance** role |
| `START_research_AI.md` | Paste as the first message when you put an AI in the **research** role |
| `START_audit_AI.md` | Paste as the first message when you put an AI in the **audit** role |
| Root `FIRST_IDEA.md` | Break an idea into **falsifiable conjectures** (project-owned; the first round's job) |
| `TEMPLATE_prior_art.txt` | Prior-art search: **has anyone already done this?** |
| `TEMPLATE_adversarial.txt` | Adversarial audit: **please attack my output** |
| `_COMMON_BLOCKS.md` | The parts bin, for when you want to build a prompt of your own |

⚠️ **A solo setup (just you and one AI) does not need the `START_*` files** —
**you use `INITIALIZE_PROMPT.md` at the top level instead.**

---

## One rule: paste the whole thing, ⛔ never "see above"

⛔ **Every prompt has to say everything it needs by itself.**

**The reason is mechanical:** each run of an outside tool happens in its own conversation, and
⛔ they share no context. **"As above" is a blank at the other end** — the clause you thought
you had given it simply does not exist in that run.

**Measured consequence:** one prompt quoted this very rule at the top, then wrote
"Same as R3-1" further down.
🔴 **The marker it referred to was used 0 times in that run; the version that spelled the
clause out was used 12 times.**

**You can check before sending:**

```
python3 scripts/harness/sensor_prompt_self_contained.py <your prompt file>
```

**If it is a search prompt for something like Deep Research, add one argument:**

```
python3 scripts/harness/sensor_prompt_self_contained.py <file> --profile deep-research
```

⚠️ **Keeping that separate is deliberate.**
**The search-specific clauses (bilingual passes, bibliographic tags) only mean something for a
search prompt** — **⛔ applied to a prompt like root `FIRST_IDEA.md`, which says "do not
search the literature this round", they produce a FAIL that can never be fixed.**

---

## Three kinds of `<<<…>>>`, and only one is a defect

| Kind | Example | Verdict |
|---|---|---|
| **Block placeholder** | `<<<PASTE BLOCK B>>>` | ❌ **FAIL** — a part has not been pasted in; the prompt is incomplete |
| **Content slot** | `<<<PASTE YOUR IDEA IN FULL>>>` | ✅ **Not a defect** — you fill it in when you use it |
| **Fill-in slot** | `<<<FILL IN: one sentence>>>` | ⚠️ **WARN** — a reminder that you have not filled it |

---

## ⚠️ One thing to remember: `TEMPLATE_prior_art.txt` is an assembled copy

**The six sections inside it are the same text as in `_COMMON_BLOCKS.md`.**

🔴 **So if you edit a block in the parts bin, ⛔ remember to come back and update the template.**

⚠️ **⛔ No program is watching this for you.**
**The clause-sync check looks at single-line term lists, ⛔ not multi-line passages.**

**⚠️ This is a known cost, written down here so it does not get forgotten silently:**
**one day the two copies will differ, and both will read perfectly normally.**
