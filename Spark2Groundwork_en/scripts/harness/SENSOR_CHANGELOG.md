# Sensor Changelog

**⛔ Every sensor change must log its triggering case here** (constitution §7.1, gate three).

**Format:** number | date | one line. Must state: the triggering case, what was changed,
and where the paired fixtures live.

---

## #0 | Initial framework version

**This sensor suite was ported from two projects in real use; every one carries a real case:**

| Sensor | Triggering case |
|---|---|
| `sensor_claim_ledger.py` | Four figures in an assessment report had no source in the original, and the original's conclusion ran **in the opposite direction** |
| ├ anchor normalisation | An anchor was truncated to a 20-character fragment by the `fi` ligature in `identified`; at the time this was misdiagnosed as "a limitation of the extraction" |
| └ extraction hashing | Found when opening corpus write access: **if a party with write access can alter the extraction, the evidence chain becomes circular** |
| `sensor_conjecture_ledger.py` | Falsification fields sat empty for a long time while the conjecture was still cited as a premise |
| `sensor_self_certification.py` | 64 files claimed "all figures verified against the originals" while a fabricated sample size sat in the same batch |
| `sensor_governance_text.py` | 17 verbatim cross-file duplicates; 8 dangling section citations, **4 of which had existed since the project was created** |
| `sensor_scope_and_t0.py` | A checking program reported 16 violations **against the wrong repository**, with complete confidence |
| `sensor_prompt_self_contained.py` | A prompt's §1 quoted "do not write 'as above'", **and its lower half wrote "Same as R3-1"** |

⚠️ **This is the single exception to "no measured case, no sensor", and the reason is written here:**
**those cases happened in other projects, not yours.**
They are listed **to save you the detour, not to claim you are immune.**

⛔ **Every sensor you add still obeys "no measured case, no sensor".**

---

## #1 | Live solo-agent test of the framework itself (**11 defects, all found by the tested agent**)

**Method:** an independent agent ran the full flow inside a copy of the framework
(read the rules → decompose a cross-domain essay → fill in blanks → run sensors → file a handoff),
and answered four feedback questions.

### 🔴 Worst: the framework's own template taught a phrasing that switched off its own sensor

`TEMPLATE_decompose.txt` originally advised marking an unfillable falsification field
as "falsification pending".

**Measured: following that advice dropped `FALSIFICATION_EMPTY` from 2 to 1, with the exit code unchanged.**
Cause: the placeholder list matched exact strings only, so **"falsification pending" counted as filled.**

⚠️ **That is failure family ④ (silent filtering), triggered by the framework's own template.**

### 🔴 Deeper: the incentives ran backwards

The tested agent's own words:

> Leaving "-" makes it look like I did less; writing "if X exceeds r > .8 then this is refuted"
> reads as entirely acceptable, and **nobody, human or sensor, can tell it is decorative**.
> It would even take that entry from WARN to silent.
> **The incentives run backwards: honesty gets a yellow light, invention does not.**

**Fix: the warning condition changed from "field is empty" to "not yet adjudicated by a human".**
Added a `Falsification adjudicated` field; **filling in text does not clear the warning —
only a human setting it to `adjudicated` does.** ⛔ AI must not set that field.
Check code renamed to `FALSIFICATION_UNADJUDICATED`.

### The other nine

| # | Defect | Handling |
|---|---|---|
| 1 | A heading said "three-level tags" while the table listed four | Renamed; no count in the clause (R-16) |
| 2 | "Output area" was undefined while §6 required writing only to it | Defined in constitution §6.1 |
| 3 | §4.2 required overwriting the state document; §6 implied otherwise | State document explicitly included in every role's output area |
| 4 | **No rule for "instruction conflicts with T0, what do I do now"** | Constitution §4.3, four cases |
| 5 | Ledger "scope" field undefined | Values defined |
| 6 | Handoff `<role>` had no enumerated values | Enumerated (an entry point for family ③) |
| 7 | A dangling section citation | Fixed (caught by a sensor) |
| 8 | A cross-file duplicate sentence | Changed to a citation (caught by a sensor) |
| 9 | No handling when the authoritative model field is absent | Three-step fallback added |

### ⚠️ Item 4 is the deepest structural gap

The tested agent was told to write into the ledger while **four documents said AI must not**.
It derived its own handling from the exemption clause, executed, and logged the exemption.

> **An agent deriving on its own that it may make an exception
> is exactly what this framework should worry about most.**

**The framework can tolerate an exception; it cannot tolerate nobody knowing one was made.**

### ✅ Two observations that the framework works

1. **The tested agent judged all seven WARNs individually and changed no document to turn the screen green.**
2. The failure-family table did work — its own words:
   **"It was the name 'silent filtering' that let me recognise what shape the template-and-sensor defect was."**

### ⛔ What this test could not verify (**coverage declaration**)

- **The tested agent was the same model family as the framework's author.**
  The cross-model adversarial layer was **entirely untested**.
- Single round. Cross-round drift (families ①②⑤) **untested**.
- External-tool, multi-role, and Windows batch scenarios untested.

---

## #2 | English edition: constants that do not port across languages

**The duplicate check used a sentence-length window of 24–80 characters (tuned on Chinese).**
Ported unchanged to English, a ~100-character rule sentence **fell outside the window and the
duplicate check silently found nothing** — caught by the paired fixture, not by reading the code.

**Fix: window widened to 40–220 for the English edition, with the reason noted in the code.**

> **A rule that is "the same rule" in two languages can still need different constants.**
