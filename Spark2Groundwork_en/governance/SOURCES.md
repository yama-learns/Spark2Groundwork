# Source Policy

**Tier: T1 — spec class.**

---

## 1. In one sentence

**Bibliographic identifiers produced by AI are treated as unverified.
A human checking downstream beats asking the AI upstream not to get it wrong.**

## 2. Empirical basis (**this is not a statement of principle**)

| Observation | Source |
|---|---|
| One model's eight references were **all canonical papers, but at least three had wrong identifiers** (wrong DOI, wrong pages) | Item-by-item comparison against an authoritative bibliography |
| Two models restated the same paper **both wrongly, in opposite directions** | Comparison after obtaining the original |
| The explanation proposed to reconcile them **was also wrong** | Same |

⚠️ **The mechanism behind the first is worth remembering on its own:**

> **"Are these canonical papers in the field" and "are these bibliographic fields correct"
> are two different questions.** The first was used to answer the second —
> **because the first can be judged from background knowledge and the second requires item-by-item checking.**
> **Only the easy one got checked.**

## 3. Handling rules

1. **Bibliographic identifiers** (DOI / journal / volume / pages) ⛔ must not be AI-generated;
   obtain them from an **authoritative bibliography file**.
   **That file = a bibliography exported from a reference manager (Zotero, EndNote, …)
   and kept in the workspace.**
   ⚠️ **Keep exactly one, and let every citation format defer to it.**
   Register its filename in `governance/AGENTS.md` §1.
   ⛔ **The AI must not rewrite it.** ⚠️ It is not an extraction, so `R-14`
   ("regenerate with the tool") does not apply — **it is the result of one query between
   a human (or an approved tool, §5) and a publisher database.**
2. **A missing DOI is not grounds for exclusion.** A substantial share of non-English journals
   are registered by regional agencies and do not appear in the main lookup services.
   ⚠️ **Leaving them permanently marked "unverified" amounts to silently excluding
   non-English literature** (the "silent filtering" family).
   → Correct handling: create a separate "non-mainstream registry" category, log the query date
   and response code, and ⛔ **never infer from the prefix**.
3. **The human's downstream check is: open the original and Ctrl+F the verbatim sentence the AI gave.**
   ⚠️ **When you cannot find it, first assume the sentence does not exist.**

## 4. Why downstream beats upstream

**You can write ten "do not fabricate" clauses into a prompt and it will still fabricate** —
because fabrication is not it disobeying an instruction; it is it doing what it always does:
producing text that looks right.

**And the downstream check takes one action: Ctrl+F.**

⛔ **Do not substitute a stricter prompt for the downstream check.**
The former cannot be verified; the latter can.

---

## 5. Who may take over link ⑤ (**this is a widening clause, not a prohibition**)

**Link ⑤ ("does this reference exist") is watched by a human today.
⚠️ Not because the AI cannot be trusted, but because the AI has no authoritative source in hand.**

> **Once an AI holds an authoritative source, it watches this link exactly as well as a human —
> because they are reading the same thing.**
> ⛔ **Do not write "this link belongs to humans" as a permanent prohibition.** That leaves the
> framework unable to follow the tooling, **and by then the real watcher becomes nobody —
> because the human stops checking too.**

### 5.1 Three approval tests (**all three, or none**)

| # | Test | Why |
|---|---|---|
| 1 | **The data is not model-generated** — it is the result of querying an external bibliographic database | Model-generated bibliography is the three errors in §2 |
| 2 | **A human can re-run the same tool and get the same result** | A check that cannot be re-run is self-certification (`R-10`) |
| 3 | **On a miss it reports "not found" and ⛔ does not guess** | The "required fields induce fabrication" family: a required field invites fabrication |

✅ **Known to qualify:** a bibliography exported from a reference manager (Zotero, EndNote, …) —
**whether a human exported it or an AI obtained it through a trustworthy integration.**
⛔ **Does not qualify:** the model's own recall, search-result snippets, any generated text that
merely *looks* like a bibliography.

### 5.2 ⚠️ Passing all three widens this link only

**The approval covers "obtaining and comparing bibliographic fields."**
⛔ **It does not cover "judging whether this paper supports your claim" — that is link ⑥,
and this document has no authority over it.**

⚠️ **The reason is already in §2:** "are these canonical papers" and "are these fields correct"
are two different questions, **and only the easy one got checked. Widening invites the same mistake.**
