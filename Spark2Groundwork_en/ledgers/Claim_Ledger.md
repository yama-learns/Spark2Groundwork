# Claim Ledger

**Tier: T1 — data class. ⚠️ By default the AI does not write here (constitution §6.3) — a default, ⛔ not a prohibition.**
**Watcher:** `scripts/harness/sensor_claim_ledger.py`

---

## 0. What this file solves

**The Conjecture Ledger works at the literature level** — "does this study matter".
**This one works at the sentence level** — "which passage backs this sentence".

> **A load-bearing ledger can remember "this paper is important". It cannot remember
> "this sentence has no source".**

### 0.1 How it lowers cost

Verifying a citation is three problems whose costs differ by three orders of magnitude:

| Layer | Question | What this ledger does | Cost |
|---|---|---|---|
| ① Locate | Which passage? | — | Medium |
| ② **Exists** | Is that passage in the source? | **Anchor field ＋ extracted full text** | **Zero** (string comparison) |
| ③ Support | Does it bear this claim? | Verification-status field | High, **but paid once per claim** |

**Sentence unchanged, source unchanged → no need to re-verify.**

### 0.2 Registration scope (**deliberately narrow, not exhaustive**)

| Must register | Need not register |
|---|---|
| Contains a **specific number** (sample size, effect size, percentage, coefficient) | General theoretical framing |
| Contains a **causal or priority assertion** ("causes", "no study has…", "the first to…") | Your own design description |
| A specific restatement of **someone else's finding** | Generic methodological description |

⚠️ **Why narrow: precision over coverage.**
**A ledger requiring every sentence gets abandoned in week two — and an unmaintained ledger
is worse than none, because it makes you believe someone is watching.**

---

## 1. Field definitions

| Field | Meaning |
|---|---|
| **Claim ID** | `M-NN`. Append-only, never reused; deletion is a state change, not a removed row |
| **Statement** | An excerpt containing the key number or assertion |
| **Source** | Author (year). Must exist as a file in the corpus |
| **Verbatim anchor** | **Quoted exactly**, must match by string comparison in the corresponding extraction |
| **Page** | The page the anchor sits on |
| **Evidence type** | `source figure` / `source conclusion` / `project inference` / `⚠️ no source` |
| **Verification status** | `✅ read the original` / `🟡 abstract only` / `🔴 unverified` |

### 1.1 Five hard rules

1. ⚠️ **`project inference` is a legitimate evidence type** — not every sentence needs an external source.
   **But it must be labelled, or downstream will read it as a literature finding.**
2. **Anchors must be verbatim.** ⛔ No paraphrase, no added punctuation, no whitespace normalisation.
   🔴 **Copied verbatim from the extract (`corpus_md/*.md`), ⛔ not from the PDF.
   OCR artefacts and all.**
   ⚠️ **Why: what gets compared is the extract, not the source — they are not the same object.**
   **Measured case:** a headline result reads `d = 0.50, 95% CI = 0.45–0.54` in the PDF and
   `d - 0.50, 95% confidence interval (CI) = 0.45-0.54` in the extract — **OCR turned the
   equals sign into a hyphen.** An anchor copied from the PDF returns "not found in source",
   ⛔ **and that looks exactly like fabrication.**
   → Where no verbatim anchor is possible (e.g. the figure exists only inside a table the
   extraction flattened), write `⚠️<reason>`. ⛔ **Never leave it blank** — blank and
   "I checked" look identical in the output.
3. ⛔ **An anchor's existence can be verified mechanically; whether it supports the claim cannot.**
   **The anchor's job is to make "did anyone look" a checkable fact — not to look for you.**
4. **Before comparison, the anchor and the extraction must pass through the same normalisation** —
   **single home: `scripts/harness/anchor_norm.py`.**
   ⚠️ **The order constraint (de-hyphenation before whitespace collapse), its reason, and
   "normalise only at comparison time, never write back": see `governance/RULES.md` R-27
   and R-28 — ⛔ this file does not restate them.**
   ⛔ Consequence specific to this ledger: rewriting the extraction breaks the hash defence.
5. 🔴 **An anchor ⛔ must not span a page break.**
   ⚠️ **Two reasons, and the second is the real one:**
   ① The page field above holds one page number — for an anchor that spans two pages,
   every possible value of that field is wrong.
   ② **The extract carries a `<!-- page: N -->` marker between pages, and anchors are matched
   verbatim.** So a sentence running from the foot of one page into the head of the next
   **is not a contiguous string in the extract at all, and will never hit.**
   ⚠️ **Measured case:** 30 sentences sampled from a 9-page paper and looked up in itself
   produced two misses — **both were page-spanning sentences**, and the first reaction was
   "the extract is broken". **The sampling was what was broken.** (constitution §7.3, step 1)
   → For a load-bearing sentence that spans a break: **take a complete clause from within one
   page** as the anchor, and note the span in the statement field.

---

## 2. Claims

*(Registration starts here. Example format below; delete this example in real use.)*

### M-01
- **Statement:** <<<FILL IN: excerpt containing the key number>>>
- **Source:** <<<FILL IN: Author (year)>>>
- **Verbatim anchor:** `<<<FILL IN: quoted exactly; must match in the extraction>>>`
- **Page:** <<<FILL IN>>>
- **Evidence type:** <<<FILL IN>>>
- **Verification status:** <<<FILL IN>>>
- **Related conjecture:** <<<FILL IN: C-NN or —>>>
