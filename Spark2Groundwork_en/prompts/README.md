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

## ⚠️ Which templates FAIL the sensor, and why

```
python scripts/harness/sensor_prompt_self_contained.py prompts/TEMPLATE_prior_art.txt
→ FAIL [PROMPT_NOT_ASSEMBLED] ×6
```

| Template | Verdict | Why |
|---|---|---|
| `TEMPLATE_decompose.txt` | ✅ **PASS** | It is a finished prompt. ⛔ **No block slots in it.** |
| `TEMPLATE_adversarial.txt` | ✅ **PASS** | Same |
| `TEMPLATE_prior_art.txt` | ❌ **FAIL** | Six `<<<PASTE BLOCK X>>>` — **the parts were never pasted in** |

⛔ **This section used to be wrong. Correction below.**

**The old text said "the templates themselves will FAIL the sensor, and that is correct",
on the grounds that "the template says `<<<PASTE BLOCK B>>>`". ⚠️ That holds for
`TEMPLATE_prior_art.txt` and not for the other two — they contain no block slots at all.**

**They FAILed because the sensor applied the Deep-Research-specific 8-clause list to every
prompt. And `TEMPLATE_decompose.txt` opens with "⛔ do not search the literature this round" —
a prompt that forbids literature search cannot and should not carry bilingual search clauses.
It would have kept FAILing after assembly, forever.**

> 🔴 **And this section had written the explanation for that false alarm.**
> **A sensor that fires on correct text, plus an official note saying the FAIL is correct —**
> **the second layer is the more dangerous one, because it turns "ignore this sensor" into policy.**

**How it works now:**

- **Self-containment** (cross-prompt references / unassembled blocks / prompt pollution)
  → **runs on every prompt**
- **The DR clause list** (8 items) → **only under `--profile deep-research`**

```
python scripts/harness/sensor_prompt_self_contained.py <assembled DR prompt> --profile deep-research
```

⚠️ **Only one of the three `<<<...>>>` slot kinds is a defect:**

| Kind | Example | Verdict |
|---|---|---|
| Block slot | `<<<PASTE BLOCK B (enumerate, do not summarise)>>>` | ❌ FAIL |
| **Content slot** | `<<<PASTE YOUR IDEA IN FULL>>>` | ✅ **Not a defect** — you fill it at use time |
| Fill-in slot | `<<<FILL IN: one sentence>>>` | ⚠️ WARN |

→ **Correct use: paste the parts in full, assemble the finished prompt, then run the sensor.**
→ **A FAIL after assembly is a real problem.**
