# Incident Log

**Tier: T1 — data class. Required reading for first-time participants.**

---

## 0. Three provenance tags (**read this first**)

| Tag | Meaning |
|---|---|
| (no tag) | **Actually happened in this project** |
| `[inherited]` | **Measured in another project; watched here.** Has not happened here |
| `[predicted]` | **Derived from architectural risk; has not happened anywhere** |

⚠️ **The effects of `[predicted]` entries are unverified. They are listed for honesty, not because they are in force.**

⛔ **Do not claim immunity because an item is tagged `[inherited]` or `[predicted]`.**
**You may defend against it, but that is not the same as it not happening.**

---

## 1. This project's incident table

| # | Date | Pressure conditions at the time | Incident | Root cause | Response | Status |
|---|---|---|---|---|---|---|
| — | — | — | *(none yet — the first one goes here)* | — | — | — |

> **How to fill "pressure conditions":** only what the incident text or its source **already recorded**.
> "— not recorded" means **it was not recorded at the time, not that there was no pressure** —
> reconstructing pressure conditions retrospectively is filling in data from memory. **Blank is more useful than invented.**
>
> The purpose is not exculpation. It is to make "which task design induces which failure" a queryable fact.

---

## 2. Failure families (**incidents pass; families recur**)

**Logging a single incident is not useful, because the next one will not look the same. What you record is the mechanism.**

### 2.1 Inherited families (**distilled from forty-odd incidents across two predecessor projects**)

| # | Family | Mechanism | Defence |
|---|---|---|---|
| **①** | **Index as authority** `[inherited]` | Read an index, abstract, error message, or tool report; asserted without checking the authority | Verification-level tags; name what you checked before declaring absence |
| **②** | **Fixed one layer, missed another** `[inherited]` | Changed a rule or program in one place; the other place is still the old version | One home per rule; cross-layer checklist |
| **③** | **Required fields induce fabrication** `[inherited]` | The field is mandatory and the fact is unavailable, so a plausible value gets entered | **"Not reported" is a valid field value**; ⛔ do not back-derive from other numbers |
| **④** | **Silent filtering** `[inherited]` | A whitelist or hard-coded list means some objects are never checked, with no message | Discovery-based scanning replaces whitelists (R-21) |
| **⑤** | **Document proliferation** `[inherited]` | Governance documents keep growing until nobody can read them | Proliferation defence (constitution §3.3) |
| **⑥** | **Tools failing while "technically correct"** `[inherited]` | The predicate is right and the message is true, but the tool failed at its actual job | Ask "what is this tool's job", not "is this predicate correct" |
| **⑦** | **Artefact self-certification** `[inherited]` | The artefact claims it has verified itself, and that claim cannot be independently checked | `sensor_self_certification.py`; R-10, R-12 |

### 2.2 Three concrete cases (**recorded here because their mechanisms are worth remembering verbatim**)

#### The textbook form of ①

> Four figures in an assessment report had no source in the original,
> and the original's headline conclusion ran **opposite** to the report's summary.
> ⚠️ **One layer deeper: the entry had already been correctly tagged `[checked]`
> with a note saying "must verify against original" —
> the institution worked, and the author still treated it as verified in his reasoning.**
>
> **The tag told the reader it was unverified. It did not stop the author.**

#### ⑥ has two forms, running in opposite directions

> **Form one (message true, job not done):** a checking tool reported "the artefact is defective";
> re-checking with a second independent tool showed **the artefact was fine from end to end**.
> **Acting on it would have meant fixing a problem that did not exist.**
>
> **Form two (message false, and it concealed success):** a batch file did
> `set RC=%errorlevel%` and then read `%RC%` inside the same `( )` block, while cmd expands
> every variable in a block **at parse time** — so it read an empty string → always true →
> **the commit had actually succeeded but it reported `[ERROR] commit failed, code .`**
> (the empty code is the proof).

#### ⑦ has two forms

> **Form one (a demonstrably false claim):** 64 files all ended with
> "all sample sizes, statistics and citations verified against the full originals, ensuring zero fabrication",
> while a fabricated sample size was found in the same batch.
>
> **Form two (flattering summary):** offering a reassuring global appraisal such as
> "has achieved a very high level of theoretical coherence" when the user asked nothing about quality.
> ⚠️ **This is harder to catch than form one, because what the reader sees is a passage that is
> careful in tone, correct in terminology, and shows no visible seam.**

### 2.3 Predicted families (**have not occurred in any project**)

| # | Family `[predicted]` | When it might occur |
|---|---|---|
| ⑧ | **Conjecture drifting into premise** | An unverified conjecture is cited repeatedly and becomes assumed known |
| ⑨ | **Construct drift** | The same term quietly changes definition across documents |
| ⑩ | **Metaphor carrying the argument** | An analogy is treated as a mechanistic explanation |
| ⑪ | **Circular support between lines** | Line A cites line B's unverified conclusion, and B cites A |
| ⑫ | **Normative slippage** | A descriptive finding is extended into "what ought to be done" |
| ⑬ | **Falsifiability dilution** | Falsification conditions are progressively loosened until nothing can refute the claim |

⚠️ **Each has a defence in place, but the effectiveness of those defences is unverified.**

---

## 3. Known weaknesses of participants (**for building gates, not for blame**)

| Participant | Expected weakness | Gate |
|---|---|---|
| **AI (generator)** | Wrong where most confident; rhetorical strength ≠ evidential strength | Verification tags; spot-check the most confident claims |
| **AI (auditor)** | Treats "restating" as "independently verifying" | Three-column report; "what I did not test" must not be empty |
| **Principal** | Single point of coordination — every adjudication passes through one person | Decision-request format; **pending queue must show rounds waited** |

⚠️ **One further observation: across two predecessor projects, the user had the highest
novel-error interception rate of any layer in the system.**
**Their most effective method was not "spotting a wrong answer" but designing a check
the AI could not pass by inference** — usually supplying external data the AI did not have.

**→ Inference: any proposal removing the principal from the loop must first answer who takes over that layer.**
