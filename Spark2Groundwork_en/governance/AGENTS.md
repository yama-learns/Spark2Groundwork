# Project Rules (T0 — required reading before any work)

**Tier: T0.** The project has exactly two T0 documents: this one and `WORKFLOW_CONSTITUTION.md`.
**Precedence:** this file ＞ constitution ＞ `RULES.md` ＞ everything else.

> ⛔ **This file must contain no state** (progress, to-dos, "currently").
> State belongs only in `NEXT_SESSION_MEMO.md`.

---

## 1. Project overview

**<<<FILL IN: one sentence on what this project does>>>**

| Item | Content |
|---|---|
| Field | **<<<FILL IN: e.g. cognitive psychology / materials science / education policy>>>** |
| Stage | **<<<FILL IN: ideation / proposal / execution / writing>>>** |
| Deliverable | **<<<FILL IN: e.g. MA thesis proposal / grant application / journal submission>>>** |
| Principal and accountable party | **<<<FILL IN: your name>>>** |

### 1.1 🔴 Is it worth doing (**must be in your own hand. ⛔ AI must not answer**)

> **① If this question gets answered, which existing claim stops standing?**
> **<<<FILL IN>>>**
>
> **② Has nobody answered this, or has someone answered it and I don't know?**
> **<<<FILL IN>>>**
>
> **③ Why is it me who should do this one?**
> **<<<FILL IN>>>**

⚠️ **Why these three exist:** the usual selection criteria (can it be finished, does the
inference hold together) **contain no question asking why this is worth knowing**.
Select on feasibility alone and you end up with a topic that is
**methodologically neat but theoretically modest**.

⛔ **If you cannot answer the third, what you are doing may be the question the AI finds easy,
not the question you wanted.**

---

## 2. Verification rules

### 2.1 Verification-level tags (**every sentence carrying a number or an assertion**)

| Tag | Meaning |
|---|---|
| `[source verified]` | I read that passage in the original and logged a verbatim anchor and page |
| `[checked]` | I read an abstract / search result / secondhand summary. **I did not read the original** |
| `[background]` | Field common knowledge, no specific source |
| `[inference]` | This project's own derivation. **Not anyone's research finding** |

### 2.2 ⛔ Two hard limits on `[checked]`

1. **It must not be used to judge a claim false.**
2. **It must not be used to build a new hypothesis** — only to raise an open question.

⚠️ **Source: the first incident in a predecessor project.** The entry had been correctly tagged
`[checked]` with a note saying "must verify against original".
**The tag was there, and it did not stop the inference.**

> **The tag told the reader it was unverified. It did not stop the author from treating it
> as verified in his own reasoning.**

### 2.3 Verdict vocabulary

| Type | Examples | Condition of use |
|---|---|---|
| **Verdict** | refuted / established / does not hold / already answered | ⛔ **Only when quoting a ledger's recorded state, with the ID in the same sentence** |
| **Exploratory** | conflicts with… / failed to replicate / no support found so far | ✅ Use this class for your own reasoning |

**"This paper conflicts with your claim" is search and exploration.
"Your claim has been refuted" is a verdict. They are not the same act.**

### 2.4 The support/refutation asymmetry, stated correctly

⚠️ **The common wrong version is "refuting requires a higher evidential standard than supporting".
That is imprecise — evidential thresholds are symmetric in inference.**

**What is actually asymmetric is the opportunity for correction:**

> A claim that is supported will still be checked by readers;
> **a claim that is declared dead is never checked again — so the error becomes permanent.**

**That is an asymmetry in the social process, not in the evidential standard.**

### 2.5 Output from external AI tools (Deep Research, search agents, automated pipelines)

⛔ **No assertion from an external AI tool may be cited without verification against the original.**

**Their value is pointing at topics, not supplying bibliography or numbers.**
See `policy/SOURCES.md`.

---

## 3. Academic bottom lines (**inviolable; on violation, stop**)

1. ⛔ **Do not fabricate any number, sample size, effect size, statistic, DOI, page, journal, or author.**
2. ⛔ **Do not write "could not find" as "does not exist."** Before declaring absence, name the authority you checked.
3. ⛔ **Do not write a single sample's result as a universal conclusion.**
4. ⛔ **Do not write "no significant difference" as "the two are the same."**
5. ⛔ **Do not delete a refuted record.** Change its state; do not remove the row.
6. **<<<FILL IN: other hard bottom lines in your field>>>**

### 3.1 Ethical red lines (**fill in per field; if not applicable, delete this section — do not leave it blank**)

**<<<FILL IN: e.g. "group comparison must not be the default analytic frame",
"descriptive findings must not be extended into normative recommendations">>>**

⚠️ **If a source you cite carries normative claims, cite only its descriptive findings;
do not carry its normative recommendations forward.**

---

## 4. Models and roles

**Full spec in `policy/MODEL_IDENTITY.md` and your chosen `profiles/PROFILE_*.md`.
This section lists only the inviolable items.**

1. **The first act of every working session is declaring your model**, read verbatim from the authoritative source.
   ⛔ **If you cannot read it, output "cannot read". Do not substitute a platform name.**
2. ⛔ **Generation and checking must not be performed by the same party.**
3. ⛔ **Do not run git commands that rewrite the working tree** (`reset --hard` / `checkout -- .` / `clean`).
   ⚠️ A predecessor project's "probe and restore" **rewrote the line endings of the entire working tree**,
   including batch files the user was actively using.
   **General rule: any report claiming "restored" must state which aspects were checked.**

---

## 5. Decision authority

**The sole adjudicator is the project principal.**

| Who | May do what |
|---|---|
| AI | Raise a **decision request** (format in constitution §5) |
| Principal | Adjudicate |
| AI | Execute what has been adjudicated |

⛔ **AI must not write directly to any ledger.**

⚠️ **The reason is not distrust; it is measurement:** across two predecessor projects,
**the user had the highest novel-error interception rate of any layer**,
and the most effective method was **supplying external data the AI did not have**.

**→ Any proposal that removes the user from the loop must first answer: who takes over that layer?**
