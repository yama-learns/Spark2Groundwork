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
   obtain them from an authoritative bibliography.
2. **A missing DOI is not grounds for exclusion.** A substantial share of non-English journals
   are registered by regional agencies and do not appear in the main lookup services.
   ⚠️ **Leaving them permanently marked "unverified" amounts to silently excluding
   non-English literature** (failure family ④).
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
