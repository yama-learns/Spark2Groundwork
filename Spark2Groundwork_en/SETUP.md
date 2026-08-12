# Setup Guide

**No programming background required.** About 40 minutes, 30 of which is you answering questions.

> ⚠️ **Do the steps in order.** Everything before step 3 exists so that step 3's checks actually run.

---

## Step 0: Confirm this is what you need

**This framework suits you if:**

- You have a **research idea that has not taken shape yet**, and want to turn it into an executable proposal
- You will use AI, but **you are accountable for the result**
- You accept spending ~20% more time in exchange for errors leaving a trace

**It does not suit you if:**

- You want speed (this framework will slow you down — deliberately)
- Your work has no factual claims that need verifying
- ⛔ **You want the AI to run autonomously while you only read the final output** —
  **the framework's core assumption is the opposite**

---

## Step 1: Install three things (~10 min)

| Software | Why | How |
|---|---|---|
| **Git** | Records what the AI changed so you can review it line by line | https://git-scm.com/download/win (Windows) / macOS built-in or `brew install git` |
| **Python 3.9+** | Runs the sensors | https://www.python.org/downloads/ ⚠️ **Tick "Add Python to PATH" during install** |
| **An AI working environment** | See table below | — |

### 1.1 AI environment: this framework is vendor-neutral

| Environment | Usable | Note |
|---|---|---|
| AI with file access (Claude Cowork / Claude Code / Cursor / Antigravity, etc.) | ✅ **Recommended** | The AI can run sensors itself |
| Chat-only interface (ChatGPT / Claude web / Gemini web) | ✅ Usable | You copy-paste files and run sensors yourself |
| Local models | ✅ Usable | Same as above |

⚠️ **If you use a chat-only interface, `profiles/PROFILE_chat_only.md` has a simplified flow.**

### 1.2 Confirm the installs worked

Open a terminal (Windows: search `cmd` in the Start menu) and type:

```
git --version
python --version
```

**Both must print a version number.** If `python` does nothing, try `python3`.

---

## Step 2: Pick a profile (~5 min)

**Open `profiles/` and choose one:**

| Your situation | Use |
|---|---|
| Just you and one AI | `PROFILE_solo.md` |
| Multiple AIs with divided roles (research / governance / audit) | `PROFILE_multi_agent.md` |
| No file access, chat window only | `PROFILE_chat_only.md` |
| You use Deep Research, n8n, or other external tools | Either of the above ＋ `PROFILE_external_tools.md` |

**Each profile tells you: what to keep, what to delete, which sensors to run.**

⛔ **Do not keep everything.** A governance document nobody maintains is worse than not having it —
**it makes you believe someone is watching.**

---

## Step 3: Make the framework yours (~20 min, **do not outsource this step to the AI**)

### 3.1 Copy the folder

Copy the whole framework to wherever your project will live, and rename it to your project name.

### 3.2 Fill in the blanks

**These files contain `<<<FILL IN:...>>>` markers. All of them need filling:**

```
governance/AGENTS.md          ← what the project is, your academic bottom lines, your ethical red lines
ledgers/Conjecture_Ledger.md  ← your first batch of conjectures
```

⚠️ **The three questions in `governance/AGENTS.md` §1.1 must be in your own hand. ⛔ The AI must not answer them:**

> **① If this question gets answered, which existing claim stops standing?**
> (Not "advance understanding" or "fill a gap". **Name a specific casualty.**)
>
> **② Has nobody answered this, or has someone answered it and I don't know?**
> (A factual question, answerable by literature search. **Not an adjective.**)
>
> **③ Why is it me who should do this one?**

**Why the AI must not answer them:** these three exist to stop **your research agenda being
quietly taken over by the AI**. If you cannot answer the third, what you are doing may be
the question the AI finds easy, not the question you wanted.

### 3.3 Start version control

**Windows:** double-click `snapshot.bat`
**macOS/Linux:** run `bash scripts/harness/human_checkpoint.sh` in the project folder

`New checkpoint created.` means it worked.

---

## Step 4: First sensor run (~2 min)

```
python scripts/harness/run_selftest.py
```

**You should see "all self-tests passed".**

⚠️ **If it does not pass, do not start editing sensors.**
A self-test failure means **the sensors themselves or your environment are broken**,
not your documents. Give the full output to your AI and say explicitly:
"this is the self-test, not the project check".

Then:

```
python scripts/harness/run_all_sensors.py
```

**A fresh project will produce a batch of WARNs on the first run. That is normal** —
your ledgers are empty and the sensors are telling you the fields are unfilled.

### 4.1 What the three exit codes mean

| Code | Meaning | What you do |
|---|---|---|
| **0** | PASS | Continue |
| **1** | FAIL | **A definite defect.** Fix it first |
| **2** | **INCOMPLETE** | **Could not check.** ⛔ **This is not a pass** |

⚠️ **The third matters most.** INCOMPLETE means the sensor failed to check.
Treating it as a pass is the first class of error this framework guards against.

---

## Step 5: Hand your idea to the AI (~5 min)

**Open `INITIALIZE_PROMPT.md` and paste the whole thing, together with your idea, to your AI.**

That prompt requires the AI to:

1. Read the governance documents first, and **restate its write scope**
2. **Decompose your idea into numbered conjectures**, each with a falsification condition
3. **Not** start searching the literature — **let you confirm the decomposition first**

⚠️ **Point 3 is deliberate.** If the decomposition is already wrong,
every paper you read afterwards is evidence for the wrong thing.

---

## Step 6: The loop from here on

```
      ┌────────────────────────────────────────────────────┐
      │  ① Before dispatch: snapshot.bat (create checkpoint) │
      │  ② Run run_all_sensors.py, confirm green            │
      │  ③ Hand the task to the AI                          │
      │  ④ AI finishes, produces a handoff packet           │
      │  ⑤ review_changes.bat (see what it changed)         │
      │  ⑥ You adjudicate → update the ledgers              │
      │  ⑦ Press snapshot.bat again (= "I have reviewed")   │
      └────────────────────────────────────────────────────┘
```

⚠️ **Step ⑦ is not a formality.** It moves a marker called `reviewed`;
**the next "what changed" is measured from there.** Skip it and you will re-read the same diffs.

---

## Step 7: Three things you will run into. Better to hear them now

### 7.1 Sensors will produce false alarms

**They will. And the first time one does, you will want to turn it off.**

⛔ **Do not loosen the criterion.** The correct fix is to repair the comparison logic **and add a
"must not false-alarm" test fixture**. `governance/RULES.md` R-19 explains why.

### 7.2 The AI will be wrong where it is most confident

**Across two predecessor projects, forty-odd incidents almost all occurred in the passages
where the author sounded most certain.**

→ Hence `governance/Audit_Protocol.md` requires: **spot-check the most confident claims,
not the least confident ones.**

### 7.3 You will want to skip the ledgers

**Logging one claim with an anchor and a page number is five times slower than just writing a sentence.**

⚠️ **And that is exactly the point: filling in the page number forces you to actually open that page —
and once you are on that page, you see that it does not say what you thought it said.**

---

## FAQ

**Q: Can I use only part of it?**
Yes — that is what `profiles/` is for. **But keep the Claim Ledger and Git checkpoints**;
those two have the lowest cost and the highest return.

**Q: Can the AI update the ledgers itself?**
⛔ **Not recommended.** The ledger records **what you have confirmed**. If the AI writes to it directly,
nobody is confirming anything. Correct flow: AI reports in **decision-request** format → you adjudicate → write.

**Q: I don't know Git. Do I have to?**
**The two scripts exist so that you don't.** You only need to remember two things:
**press once before dispatching, press once after reviewing.**

**Q: Isn't this too heavy?**
It is, if you use all of it. **That is why `profiles/` exists.**
⚠️ Also note: **this framework has a rule called "document proliferation defence"** —
it assumes governance documents will bloat, rather than assuming you will show restraint.
