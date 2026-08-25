# Spark2Groundwork

**Turn a spark of an idea into a research proposal that holds up.**

---

## All you have to do is three things

| What | Where |
|---|---|
| **Fill in one file** | `PROJECT.md` at the root — ⛔ every other governance document is AI-maintained |
| **Press three buttons** | snapshot / review changes / check update (`.bat` on Windows, `.command` on macOS) |
| **Adjudicate** | You are the only adjudicator. The AI asks; you decide |

⚠️ **Framework folders can be replaced wholesale from GitHub, ⛔ and your ledgers, corpus and
`PROJECT.md` are never touched.**

---

## 0. What this is

A **file-based governance framework** for developing research ideas with AI assistance.
It lets you answer three questions at any point:

| Question | Answered by |
|---|---|
| **Which page does this sentence rest on?** | Claim Ledger ＋ anchor sensor |
| **What would it take to refute this idea?** | Conjecture Ledger ＋ falsification field |
| **What did the AI just change, and have I reviewed it?** | Git checkpoints ＋ two scripts |

⚠️ **This is not a way to make AI smarter.**
It assumes AI will be wrong, and that **it will be wrong where it is most confident**.
Every defence in this framework corresponds to a failure that actually happened.

---

## 1. What it does not claim (**read this first**)

⛔ **This framework does not guarantee your research is correct.** It guarantees only that
**when it is wrong, the error leaves a trace instead of quietly becoming your conclusion.**

| It can check | It cannot check |
|---|---|
| Whether a quoted sentence exists in the source | Whether the source **supports your inference** |
| Whether the falsification field is filled | Whether what you filled in is **actually observable** |
| Whether a rule has two versions | Whether the rule itself is **right** |

**The right-hand column is human work, and it is deliberately not mechanised** —
a sensor that fires on correct text teaches you to ignore it, which is worse than no sensor.

---

## 2. Five-minute tour

<p align="center">
  <img src="docs/fig1_architecture.svg" alt="Architecture: what is the framework and what is yours" width="100%">
</p>

⚠️ **Above the red line is the framework — break it and you re-download it. Below the line is
your data, and nothing anywhere can restore it.**


```
SETUP.md              ← 🚩 Start here. Install, fill in, first run
INITIALIZE_PROMPT.md  ← The prompt you paste to your AI
profiles/             ← Pick the one matching how you work
governance/           ← Governance documents (where rules live)
ledgers/              ← Ledgers (where evidence lives)
policy/               ← Topic policies (model identity, handoff, sources, external tools)
prompts/              ← Prompt building blocks and templates
scripts/harness/      ← Sensors (mechanical checks)
```

---

## 3. Four core ideas

<p align="center">
  <img src="docs/fig2_workflow.svg" alt="Workflow: the evidence chain, who watches it, and the loop" width="100%">
</p>


### 3.1 The evidence chain has links, not just "did you cite something"

A sentence containing a number passes through seven links on its way from idea to page.
**Each can break, and each breaks differently.**

| Link | Question | Mechanisable? |
|---|---|---|
| ① Locate | Which passage should I cite? | ❌ |
| ② **Exists** | **Is that passage actually in the source?** | ✅ **Zero cost** |
| ③ Fields | Are the required fields filled? | ✅ |
| ④ Consistency | Do the documents agree with each other? | ✅ |
| ⑤ Authenticity | Does this reference actually exist? | ✅ Needs external lookup |
| ⑥ Support | Does that passage bear the weight of this claim? | ❌ **Human work** |
| ⑦ Generalisation | Can you go from that sample to here? | ❌ **Human work** |

**② is the fulcrum of the whole design**: it turns "did anyone actually read the source"
into a fact you can settle with string comparison.

### 3.2 Two ledgers, two different jobs

| | Conjecture Ledger | Claim Ledger |
|---|---|---|
| Governs | **Literature level**: does this idea hold up? | **Sentence level**: which passage backs this? |
| Key fields | **Falsification condition**, strongest rival | **Verbatim anchor**, page number |
| Failure mode | An idea becomes an unfalsifiable worldview | A number gets rebuilt from memory |

### 3.3 Failures come in families; incidents pass, families recur

**Logging a single incident is not useful**, because the next one will not look the same.
What you record is the **mechanism** — see `governance/Incident_Log.md` §2.

### 3.4 The human is the only adjudicator

⚠️ **This is not conservatism; it is a measured result.**
Across two predecessor projects, **the user had the highest novel-error interception rate
of any layer in the system**, and their most effective method was not "spotting a wrong answer"
but **supplying a piece of external data the AI did not have**.

**→ Any proposal that removes the human from the loop must first answer: who takes over that layer?**

---

## 4. Where this comes from

**Two real projects, forty-odd logged incidents between them.**
Every sensor and every hard rule here carries the case that triggered it.

⛔ **Rules without a case do not get written in** — the framework has its own rule saying so.

⚠️ **But that rule has one exception, and it is the reason this framework exists:**
the failure families marked `[inherited]`, `[framework's own]` or `[predicted]` in
`governance/Incident_Log.md` **have not happened in your project.** They are listed for honesty, not because they are in force —
**you may defend against them, but do not claim immunity because of them.**

---

## 5. Next step

👉 **Open `SETUP.md`.**

---

## Licence

**This framework is released under the MIT licence**, from
https://github.com/yama-learns/Spark2Groundwork

⚠️ **That covers the framework files only.**
**The research you produce with it is yours** — ⛔ this framework claims no rights over your
final product, and takes no responsibility for it.
