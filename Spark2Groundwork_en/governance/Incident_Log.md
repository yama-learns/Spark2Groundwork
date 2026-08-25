# Incident Log

**Tier: T1 — data class. Required reading for first-time participants.**

---

## 0. Provenance tags (**read this first**)

| Tag | Meaning |
|---|---|
| (no tag) | **Actually happened in this project** |
| `[framework's own]` | 🔴 **Happened while maintaining this framework itself.** ⚠️ **Not "somebody else's incident" — it happened to the author of the document in your hands** |
| `[inherited]` | **Measured in another project; watched here.** Has not happened here |
| `[predicted]` | **Derived from architectural risk; has not happened anywhere** |

⚠️ **The effects of `[predicted]` entries are unverified. They are listed for honesty, not because they are in force.**

⛔ **Do not claim immunity because an item is tagged `[inherited]` or `[predicted]`.**
**You may defend against it, but that is not the same as it not happening.**

---

## 1. This project's incident table

🔴 **Its home is `incidents/MY_INCIDENTS.md`.**
⚠️ **Why it moved out:** that is **your data**, and this is a **framework file**.
Framework files must be upgradable by wholesale replacement, ⛔ and replacing a file
that holds your incident records deletes them.
**This file now holds only failure families — mechanisms, safe to replace wholesale.**

---

## 2. Failure families (**incidents pass; families recur**)

**Logging a single incident is not useful, because the next one will not look the same. What you record is the mechanism.**

⛔ **Cite a family by name, ⛔ never by number.**
**The number is this table's ordinal; the name is the identifier.**
⚠️ **Measured:** two places once read "failure family ⑧", and ⑧ was later reassigned —
**both citations still resolved, they just pointed at a different family.**
🔴 **Why that is worse than a dangling reference: constitution §3.4.** ⛔ Not restated here.

### 2.0 🔴 Axis one: **two states carrying very different information look identical on screen**

| Family | The two things you cannot tell apart |
|---|---|
| **Required fields induce fabrication** | a plausible fabricated value / the real value |
| **Silent filtering** | never checked / checked and clean |
| **Tools failing while "technically correct"** | a false success / a real success |
| **Artefact self-certification** | claims to have verified / actually verified |
| **Text about a defect vs the defect itself** | an explanation / a specimen |
| (`R-35`) | "none" as the result of taking stock / "none" as an omission |
| (coverage collapse, constitution §7.4) | nothing to compare against / compared and consistent |

⛔ **These are deliberately not merged into one family.** A family exists so that someone can
**recognise a shape in the field**, and a family covering five families recognises no shape at
all — **it becomes an aphorism, not a diagnostic tool.**

⚠️ **But knowing they share a root has one practical use: fixing one of them ⛔ does not mean
the others are safe.** See `governance/Audit_Protocol.md` §6, "cross-family is not independence".

### 2.0b Axis two: **one fact has two copies, and only one of them gets updated**

**The whole "fixed one layer, missed another" family sits on this one**, its forms distinguished
by where the second copy lives (see the table).
**P2, "construct drift", is its predicted form**: what gets copied is a term's definition.

### 2.1 Families that have occurred

| # | Family | Mechanism | Defence |
|---|---|---|---|
| **①** | **Index as authority** `[inherited]` | Read an index, abstract, error message, or tool report; asserted without checking the authority. **Three variants get missed most often:** (a) **treating a tool's failure as your own capability limit**; (b) **dropping the source's hedge** (`more than 75%`→`75%`; `may have no network`→`no network`); (c) 🔴 **treating "this looks like a known family" as "this is that family"** — classifying without reading the line | Verification-level tags; name what you checked before declaring absence; **`R-34`** (capability = tool list); (c) **a classification must land on a specific line number or verbatim text** |
| **②** | **Fixed one layer, missed another** `[inherited]` `[axis 2]` | **One fact has two copies, and only one of them gets updated. ⛔ When they disagree, nothing says so.** Forms are distinguished by where the second copy lives: (a) **another document**; (b) 🔴 **a carrier that evaporates** (a conversation, screen output, memory); (c) **a number written into prose** | One home per rule (constitution §3.2); `DUPLICATE_RULE_TEXT`; `sensor_clause_sync.py`; (b) a single registry; (c) **`R-16`** |
| **③** | **Required fields induce fabrication** `[inherited]` `[axis 1]` | The field is mandatory and the fact is unavailable, so a plausible value gets entered | **"Not reported" is a valid field value**; ⛔ do not back-derive from other numbers |
| **④** | **Silent filtering** `[inherited]` `[axis 1]` | A whitelist or hard-coded list means some objects are never checked, with no message | Discovery-based scanning replaces whitelists (R-21) |
| **⑤** | **Document proliferation** `[inherited]` | Governance documents keep growing until nobody can read them | Proliferation defence (constitution §3.3) |
| **⑥** | **Tools failing while "technically correct"** `[inherited]` `[axis 1]` | The predicate is right and the message is true, but the tool failed at its actual job | Ask "what is this tool's job", not "is this predicate correct" |
| **⑦** | **Artefact self-certification** `[inherited]` `[axis 1]` | The artefact claims it has verified itself, and that claim cannot be independently checked | `sensor_self_certification.py`; R-10, R-12 |
| **⑧** | **Text about a defect, and the defect itself, are indistinguishable to string matching** `[framework's own]` `[axis 1]` | When a document explains a defect, its wording **cannot be told apart from a specimen of that defect**. ⚠️ **Two forms pointing in opposite directions, with opposite dispositions** (see §2.2) | Form one: ⛔ **reword into description, add no exemption**; form two: ✅ **quotation detection** (a prohibition marker earlier on the same line), ⛔ **not an exemption list** |

### 2.2 Concrete cases (**recorded here because their mechanisms are worth remembering verbatim**)

#### The textbook form of "index as authority"

> Four figures in an assessment report had no source in the original,
> and the original's headline conclusion ran **opposite** to the report's summary.
> ⚠️ **One layer deeper: the entry had already been correctly tagged `[checked]`
> with a note saying "must verify against original" —
> the institution worked, and the author still treated it as verified in his reasoning.**
>
> **The tag told the reader it was unverified. It did not stop the author.**

#### "Index as authority", form two: treating a tool's failure as your own capability limit (**three times, three different actors**)

> **The textbook form of ① is "read the index, never checked the authority." This one is
> harder to see: the index was never read either.**
>
> | # | Trigger | Assertion written down | Reality |
> |---|---|---|---|
> | 1 | `rm` failed | "this platform has no delete permission" | **The authorising tool was in the tool list all along.** A whole cross-platform division of labour rested on it |
> | 2 | A sensor printed "**may** have no network" | "the sandbox has no network", written into a delivery note | The sensor used urllib; another channel reached the service directly |
> | 3 | `unlink` was denied | "my tools cannot delete files", written into three deliverables | A second, permission-gated channel was never enumerated |
>
> ⚠️ **The shared shape is not "guessed wrong". It is "turned one channel's limit into a
> universal statement about myself".**
> **Case 2 did one more thing: it deleted the word "may" — the other half of the same move.**
>
> ⛔ **All three were caught by a human. None was self-detected.** Countermeasure: `governance/RULES.md` `R-34`.

#### "Technically correct" failures have three forms, running in different directions

> **Form one (message true, job not done):** a checking tool reported "the artefact is defective";
> re-checking with a second independent tool showed **the artefact was fine from end to end**.
> **Acting on it would have meant fixing a problem that did not exist.**
>
> **Form two (message false, and it concealed success):** a batch file did
> `set RC=%errorlevel%` and then read `%RC%` inside the same `( )` block, while cmd expands
> every variable in a block **at parse time** — so it read an empty string → always true →
> **the commit had actually succeeded but it reported `[ERROR] commit failed, code .`**
> (the empty code is the proof).
>
> **Form three (message false, and it concealed failure):** the framework's own
> `scripts/harness/ai_checkpoint.sh` used to run
> `find .git -name "*.lock" -delete 2>/dev/null`, then `git add -A`, then decide
> "no changes" from `git diff --cached --quiet` and `exit 0`.
> In a mount that denies unlink: the delete fails and `2>/dev/null` eats the message →
> `add` fails because the lock is still there → the index is empty →
> **the script prints "no changes", reports success, and no checkpoint exists.**
>
> ⚠️ **Forms two and three are the same conditional pointing two ways, and the danger is
> asymmetric: a false failure gets investigated; a false success does not.**
> ⛔ Countermeasure: `governance/RULES.md` R-33.

#### "Artefact self-certification" has two forms

> **Form one (a demonstrably false claim):** 64 files all ended with
> "all sample sizes, statistics and citations verified against the full originals, ensuring zero fabrication",
> while a fabricated sample size was found in the same batch.
>
> **Form two (flattering summary):** offering a reassuring global appraisal such as
> "has achieved a very high level of theoretical coherence" when the user asked nothing about quality.
> ⚠️ **This is harder to catch than form one, because what the reader sees is a passage that is
> careful in tone, correct in terminology, and shows no visible seam.**

#### "Index as authority", form three: treating "this looks like a family" as "this is that family"

> **Form one is "read the index, not the authority". Form two is "read nothing at all".**
> **This one is harder to see: something was consulted — a classification table.**
>
> ⚠️ **Measured:** a change proposal justified itself by stating "this program decides
> INCOMPLETE from an independent boolean" — the shape of a known family.
> **On inspection the code had always derived it from the findings.**
> **The proposal was caught by its own author just before acting; in the other order it would
> have left a record of a defect that never existed, reading perfectly plausibly.**
>
> 🔴 **This form is induced by the failure-family table itself.**
> **A well-written family table lets every new phenomenon be classified — including the ones
> that belong to no class at all.**
>
> ⛔ **Defence: a classification must land on a specific line number or verbatim text.**
> "This looks like family X" ⛔ is not a reason for any action.

#### "Fixed one layer, missed another": forms two and three (**where the second copy lives**)

> **Form one is "another document" — the family's original shape. The other two are just as
> common and harder to see:**
>
> **Form two (the copy lives on a carrier that evaporates):** something exists both in a registry
> and in a conversation, screen output, or memory.
> ⚠️ **Measured:** a pending-decision registry's "recommendation" column read option A, while its
> author had actually recommended option B in conversation; the full analysis of the three
> options **existed only in that conversation.**
> **⛔ "I said so" is not "it is registered" — and conversations end, screens scroll.**
>
> **Form three (the copy is a number written into prose):** a README said "5 sensors" from its
> first version; the real number was 7. **The file was read at least three times during
> maintenance and the line was never seen.**
> 🔴 **Because a stale number and a correct number look identical, and `5` does not make anything
> report an error.**
> ⛔ **Rereading will not find it — only verifying the number will.** Defence: `R-16`.

#### "Text about a defect vs the defect itself": two forms (**opposite directions, opposite dispositions**)

> **Form one (mentioning it actually commits it):** while rewriting a sensor's file header, its
> old whitelist's filenames were quoted as examples in a comment, **so those filenames instantly
> became new dangling references** — and catching dangling references is that sensor's job.
> ⛔ **Disposition: reword into description; add no exemption.**
> **Exempting an incident log or a file header hollows out the learning material.**
>
> **Form two (mentioning it is mistaken for committing it):** a sensor keyed on the presence of
> the word "to-do", **so the rule text saying "must not contain to-dos" was itself flagged**;
> and a prompt quoting "⛔ do not write 'see below'" **had its embedded "see below" read as a
> cross-file reference.**
> ✅ **Disposition: quotation detection** — a prohibition marker (⛔ / must not / do not /
> forbidden) appearing **before** the phrase on the same line marks it as quoted.
> ⛔ **Not an exemption list.**
>
> ⚠️ **Shared mechanism: string matching can tell whether a phrase is present; ⛔ it cannot tell
> who is saying it.**
> 🔴 **And the danger is asymmetric: form one really does damage the document; form two teaches
> people to switch the sensor off (`R-19`).**

### 2.3 Predicted families (**have not occurred in any project**)

⛔ **Predicted families use their own `P` numbering; ⛔ they do not share a sequence with
families that have occurred.**
⚠️ **Why (measured):** the two used to share one run of numbers ①–⑬, so **the next number
available for a newly occurred family was ⑭** — while ⑧–⑬, things that have *not* happened,
sat in the middle of the sequence.
🔴 **Worse: if a predicted family were ever removed or promoted, ⑧ would fall free and be
reused by something else, and every citation reading "family ⑧" would silently retarget —
still resolving, just pointing at something different.**
→ **Two namespaces cannot collide by construction.**

⚠️ **If a predicted family does occur:** add a new occurred-family number in §2.1 and mark this
row "**occurred → family 〈new number〉**". ⛔ Do not delete the row.

| # | Family `[predicted]` | When it might occur |
|---|---|---|
| **P1** | **Conjecture drifting into premise** | An unverified conjecture is cited repeatedly and becomes assumed known |
| **P2** | **Construct drift** | The same term quietly changes definition across documents |
| **P3** | **Metaphor carrying the argument** | An analogy is treated as a mechanistic explanation |
| **P4** | **Circular support between lines** | Line A cites line B's unverified conclusion, and B cites A |
| **P5** | **Normative slippage** | A descriptive finding is extended into "what ought to be done" |
| **P6** | **Falsifiability dilution** | Falsification conditions are progressively loosened until nothing can refute the claim |

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
