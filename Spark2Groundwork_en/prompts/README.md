# Prompt Library

**`_COMMON_BLOCKS.md` is the parts bin; `TEMPLATE_*.txt` are the finished items.**

⛔ **Finished prompts must be fully self-contained.** When assembling, paste the block's
**full text**; do not write "see block A".
**Reason and measured consequence: `policy/EXTERNAL_TOOLS.md` item 2.**

| File | Purpose |
|---|---|
| `_COMMON_BLOCKS.md` | Reusable passages |
| `TEMPLATE_decompose.txt` | **Split an idea into falsifiable conjectures** (initialisation, step one) |
| `TEMPLATE_prior_art.txt` | Prior-art check: has anyone done this |
| `TEMPLATE_adversarial.txt` | Adversarial audit: attack my output |

**Intake: triage every external report with `profiles/PROFILE_external_tools.md` §2.**

---

## ⚠️ The templates themselves will FAIL the sensor. That is correct

```
python scripts/harness/sensor_prompt_self_contained.py prompts/TEMPLATE_prior_art.txt
-> FAIL [CROSS_PROMPT_REFERENCE]
```

**Because the template says `<<<PASTE BLOCK B>>>` rather than the text of block B.**

**That is exactly why the sensor exists:** at the execution end,
`<<<PASTE BLOCK B>>>` is equivalent to "as above" — **the referenced clause does not exist.**

→ **Correct use: assemble the full text first, then run the sensor.**
→ **A FAIL after assembly is a real problem.**
