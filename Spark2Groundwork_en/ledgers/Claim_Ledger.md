# Claim Ledger

**Tier: T1 — data class. ⛔ AI must not write to this file directly.**
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

### 1.1 Four hard rules

1. ⚠️ **`project inference` is a legitimate evidence type** — not every sentence needs an external source.
   **But it must be labelled, or downstream will read it as a literature finding.**
2. **Anchors must be verbatim.** ⛔ No paraphrase, no added punctuation, no whitespace normalisation.
3. ⛔ **An anchor's existence can be verified mechanically; whether it supports the claim cannot.**
   **The anchor's job is to make "did anyone look" a checkable fact — not to look for you.**
4. **Before comparison, the anchor and the extraction must pass through the same normalisation** —
   **single home: `scripts/harness/anchor_norm.py`.**
   ⚠️ **The order cannot be swapped: de-hyphenation must precede whitespace collapse.**
   Otherwise `individ-\nual` becomes `individ- ual`, then `individ-ual`, **and can never be rejoined**.
   ⛔ **Normalisation happens only at comparison time; never written back** — rewriting the
   extraction breaks the hash defence.

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
