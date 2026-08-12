# Profile: one person ＋ one AI

**For: just you and one AI assistant that has file access.**

---

## 1. What to keep

| Keep | May delete |
|---|---|
| `governance/AGENTS.md` | `governance/Audit_Protocol.md` (no second model to audit with) |
| `governance/WORKFLOW_CONSTITUTION.md` | `handoffs/` (no cross-role handoff needed) |
| `governance/RULES.md` | |
| `governance/Incident_Log.md` | |
| Both files in `ledgers/` | |
| `NEXT_SESSION_MEMO.md` | |
| `scripts/harness/` | |

⚠️ **Deleting `Audit_Protocol.md` costs you the adversarial-audit layer.**
**Compensate: periodically paste your output to a model from a different vendor and ask one question:**

> "Which sentence in this document is the author most confident about
> and I should be most suspicious of?"

⚠️ You do not need a full audit process, but **you do need a second pair of eyes that is not the same model** —
**reason: three of this framework's four core defences came from "another model saw what the author could not".**

## 2. `framework_config.py` setting

```python
"write_scopes": {}          # leave empty; the sensor will say "not applicable"
```

## 3. Per-round loop (simplified)

```
snapshot → hand over task → AI produces → review changes → you adjudicate → update ledgers → snapshot
```

## 4. The **specific** risk of a solo setup

⚠️ **You and the AI will form a two-person closed loop.**

The candidate papers, counterexamples, and theoretical links you see may all have been filtered by the AI —
**so you will not see what the AI did not think of, and you will not know that you did not see it.**

**→ Every few rounds, run an AI-free search:**

1. Search professional databases yourself with Boolean logic, **60-minute limit**
2. Produce a plain list, **not processed by any AI**
3. Compare with your existing corpus in three columns: **both / AI only / human only**

⚠️ **The third column is the point.** Empty means the AI's search missed nothing;
non-empty **means your hypothesis space was filtered by the AI — and until you ran this,
nobody knew that.**
