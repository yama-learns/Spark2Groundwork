# Profile: using external AI tools

**For: Deep Research, automation pipelines (n8n / Zapier), search agents — any AI running out of your sight.**
**⚠️ This is an add-on; combine it with another profile.**

---

## 1. One overriding rule

⛔ **External tool output ＝ an unverified lead. Its only legitimate use is pointing at a topic.**

**⛔ No assertion, bibliography, or number from it may be cited without verification against the original.**

⚠️ **This is not conservatism.** Measured: two Deep Research models restated the same paper
**both wrongly, and in opposite directions**; and the explanation proposed to reconcile them
**was also wrong** — because both restatements were false, so any hypothesis reconciling them
rested on fabricated data.

## 2. Five-way triage

Classify every item in an external report:

| Level | Content | Handling |
|---|---|---|
| **1** | Points at a topic, method, or controversy you did not know | ✅ **Most valuable.** Go find the original |
| **2** | Gives specific bibliography | ⚠️ Check each against an authoritative source. **Identifiers are often wrong** |
| **3** | Gives numbers | ⛔ **Always go to the original.** Until then it goes in no document |
| **4** | Gives a conclusion or verdict | ⛔ **Always treated as unverified** |
| **5** | Topic irrelevant to your question | Exclude. **This is the only valid exclusion reason** |

⚠️ **Run two models on the same prompt: their points of disagreement are the highest-value output** —
**a disagreement marks a place where at least one side is wrong, which is exactly where to go read the original.**

## 3. Prompts must be self-contained

⛔ **Every external prompt must be fully self-contained. No "as above", "see previous", "same as R1".**

⚠️ **Why: external tools run in independent conversations with no shared context —
"as above" is blank at the execution end, and the referenced clause effectively does not exist.**

**Measured consequence:** a prompt's §1 quoted this very rule, **and its lower half wrote "Same as R3-1"**.
The referenced marker was used **0 times** in that run; the version with the clause spelled out used it **12 times**.

**Check with:**

```
python scripts/harness/sensor_prompt_self_contained.py <your_prompt.md>
```

## 4. Extra care with automation pipelines (n8n etc.)

| Risk | Countermeasure |
|---|---|
| **Intermediate output nobody reads** | Every node's output must land as a file, **with a timestamped name** |
| **Failures swallowed** | ⛔ No silent retry on failure. **A failure record must remain** |
| **Automated writes to ledgers** | ⛔ **Absolutely forbidden.** The ledger records what *you* confirmed |

⚠️ **The most dangerous property of automation: it makes "nobody looked at this" a state with no trace.**
**The entire premise of this framework is making "did anyone look" a checkable fact.**

## 5. Where external output goes

```
external/          ← raw reports, stored unmodified
```

⛔ **Do not put external reports in the corpus (`corpus_md/`).**
The corpus is **programmatically extracted source text**, the comparison target for anchors.
**Mixing in AI-generated text destroys the meaning of anchor checking — you would be
matching against sentences the AI wrote itself.**
