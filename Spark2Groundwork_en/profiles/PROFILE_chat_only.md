# Profile: chat window only (AI has no file access)

**For: ChatGPT / Claude web / Gemini web, where you copy and paste.**

---

## 1. Cut hard: keep three things

| Keep | Why |
|---|---|
| `ledgers/Claim_Ledger.md` | **Lowest cost, highest return.** Fully workable by hand |
| `ledgers/Conjecture_Ledger.md` | Same |
| `governance/AGENTS.md` | Paste at the start of each conversation |

**Everything else can go, including the sensors** —
**because you will not run them, and a check that never runs is not a check.**

⚠️ **But if you have Python on your machine, keep at least `sensor_claim_ledger.py`.**
It is the only tool that answers "is this sentence really in the source",
which is exactly where chat interfaces go wrong most often.

## 2. Per-round loop

```
① Paste governance/AGENTS.md in full into a new conversation
② Paste your current ledger state (or the relevant few entries)
③ State explicitly: "for every sentence with a number, give me the verbatim
   original sentence and the page number"
④ After the reply, **you** register new claims into the ledger yourself
⑤ Periodically (every 5–10 rounds) paste the ledger to a **different vendor's** model and ask:
   "Which of these anchors is most likely to have been made up?"
```

## 3. ⚠️ The biggest risk in this setup

**With no version control, you will not know what the AI changed this round.**

**Cheapest compensation:** after each significant step, save the whole ledger under a
dated filename such as `Claim_Ledger_2026-01-15.md`.

⛔ **Do not overwrite.** What you need is not the latest version but **two versions you can compare**.

## 4. The minimum manual verification action

**When the AI gives you a number, do this one thing:**

> Open the source PDF and **Ctrl+F the verbatim sentence it gave you.**

⚠️ **If you cannot find it, do not ask the AI "did I get this wrong".**
**Assume the sentence does not exist** — a predecessor project's first incident had exactly this shape:
four figures had no source in the original, and the original's conclusion ran **opposite** to the summary.
