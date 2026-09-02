# Project Rules (T0 — required reading before any work)

**Tier: T0.** The project has exactly two T0 documents: this one and `WORKFLOW_CONSTITUTION.md`.
**Precedence:** this file ＞ constitution ＞ `RULES.md` ＞ everything else.

⛔ **This file must contain no state** (progress, to-dos, "currently").
State belongs only in `NEXT_SESSION_MEMO.md`.

---

## 1. Read before starting

| Order | What |
|---|---|
| 1 | `PROJECT.md` at the root — what this project is, who the principal is, ethical red lines |
| 2 | this file |
| 3 | `WORKFLOW_CONSTITUTION.md` |
| 4 | `NEXT_SESSION_MEMO.md` — where the last round left off |

---

## 2. Verification

### 2.1 Verification-level tags

**Every sentence carrying a number or an assertion takes one.**

| Tag | Meaning |
|---|---|
| `[source verified]` | I read that passage in the original and logged a verbatim anchor and page |
| `[checked]` | I read an abstract, a search result or a second-hand account, **not the original** |
| `[background]` | Field common knowledge, no specific source |
| `[inference]` | This project's own derivation, **not anybody's research finding** |

### 2.2 Two limits on `[checked]`

1. ⛔ **It may not be used to judge any claim false.**
2. ⛔ **It may not be used to build a new hypothesis**, only to raise an open question.

⚠️ **The tag will not stop you.** In the predecessor projects' first incident the entry was
correctly tagged and annotated "must verify against the original",
**and the author still treated it as verified in his reasoning.**

### 2.3 Verdict vocabulary

| Type | Example | Condition |
|---|---|---|
| **Verdict** | refuted / established / does not hold | ⛔ **Only when quoting a ledger's recorded state, with the ID in the same sentence** |
| **Exploratory** | conflicts with… / did not replicate / no support found so far | ✅ Use this for your own writing |

### 2.4 Support and refutation are asymmetric

⛔ **Do not write "refutation requires a higher evidential standard than support"** — the
evidential bar is symmetric.

**What is asymmetric is the chance of correction: a supported claim still gets checked; a claim
declared dead is never checked again.**

### 2.5 Output from external AI tools

⛔ **No assertion from an external AI tool may be cited without verification against the original.**
**Their use is to point at questions, not to supply bibliography or numbers.** See `governance/SOURCES.md`.

---

## 3. Academic bottom line (**violation stops work**)

**This section is the home of the following; `RULES.md` R-01–R-04 cite it.**

1. ⛔ **Do not fabricate any figure, sample size, effect size, statistic, DOI, page, journal or author.**
2. ⛔ **Do not write "not found" as "does not exist".** Name the authority you checked first.
3. ⛔ **Do not write a single sample's result as a general conclusion.**
4. ⛔ **Do not write "no significant difference" as "the two are the same".**
5. ⛔ **Do not delete a refuted record.** Change its state; keep the row.
6. ⛔ **When citing a source that carries normative claims, cite only its descriptive findings.**

**Field-specific bottom lines go in `PROJECT.md` §3.**

---

## 4. Model and roles

**Full specification: `governance/MODEL_IDENTITY.md` and the chosen `profiles/PROFILE_*.md`.
This section lists only what cannot be violated.**

1. **The first act of every session is to declare the model**, read verbatim from the authority.
   ⛔ If it cannot be read, output "unreadable"; **never substitute a platform name**.
2. ⛔ **Generation and checking must not be done by the same party.**
3. ⛔ **Do not run git commands that rewrite the working tree** (`reset --hard` / `checkout -- .` / `clean`).
4. **Any report claiming "restored / done / passed" must state which aspects were checked.**

---

## 5. Decision rights

**The project's principal is the only adjudicator.**

| Who | Does what |
|---|---|
| AI | files a decision request (format: constitution §5) |
| Principal | adjudicates |
| AI | carries out what was adjudicated |

**What the AI may write to is the principal's decision; the setting is `deny` in
`governance_config.json`** (constitution §6.3). ⛔ This framework sets no prohibition the user
cannot lift.

⛔ **However wide the authorisation, the AI still declares which files it wrote**
(`governance/HANDOFF.md` §3.3).
