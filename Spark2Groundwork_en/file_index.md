# File Index and Rule Homes

**Tier: T1 — index. ⛔ Says only where things are; restates no rule content.**

> ⚠️ **This index is not authoritative.** The files themselves are.
> **Using the index in place of checking is the "index as authority" family itself.**

---

## 0. Where each rule lives

**To change a rule, change only the place named below** (constitution §3.2).

| Rule / criterion | Single home |
|---|---|
| Verification-level tags | `governance/AGENTS.md` §2.1 |
| The two limits on `[checked]` | `governance/AGENTS.md` §2.2 |
| Verdict vs exploratory vocabulary | `governance/AGENTS.md` §2.3 |
| The support/refutation asymmetry | `governance/AGENTS.md` §2.4 |
| Academic bottom lines | `governance/AGENTS.md` §3 |
| Topological facts | `governance/WORKFLOW_CONSTITUTION.md` §1 |
| Evidence chain links ①–⑦ | `governance/WORKFLOW_CONSTITUTION.md` §2 |
| Document tiers by update frequency | `governance/WORKFLOW_CONSTITUTION.md` §3 |
| Document proliferation defence | `governance/WORKFLOW_CONSTITUTION.md` §3 |
| Session-start / session-end rituals | `governance/WORKFLOW_CONSTITUTION.md` §4 |
| **Handling an instruction that conflicts with T0** | `governance/WORKFLOW_CONSTITUTION.md` §4 |
| Decision request format | `governance/WORKFLOW_CONSTITUTION.md` §5 |
| Write scope general rules / "output area" | `governance/WORKFLOW_CONSTITUTION.md` §6 |
| Sensor gates / false-alarm handling / exit codes | `governance/WORKFLOW_CONSTITUTION.md` §7 |
| All working rules (`R-xx`) | `governance/RULES.md` |
| Failure family table | `governance/Incident_Log.md` §2 |
| Conjecture states / retirement and dormancy | `ledgers/Conjecture_Ledger.md` §0 |
| Claim registration scope / four anchor rules | `ledgers/Claim_Ledger.md` §0–§1 |
| **Anchor normalisation function** | `scripts/harness/anchor_norm.py` |
| **All sensor path settings** | `scripts/harness/framework_config.py` |
| **Mechanical implementation of exit-code semantics** | `scripts/harness/_common.py` (`emit`) — ⚠️ **the semantics are defined in constitution §7.4; this is their only implementation** |
| Handoff packet spec | `policy/HANDOFF.md` |
| **Project identity, is-it-worth-doing, ethical red lines, search keywords** | 🔴 **`PROJECT.md` (root; the only file the user fills in)** |
| **Incidents that actually happened in this project** | `incidents/MY_INCIDENTS.md` |
| **Who decides the AI's write permissions** | `governance/WORKFLOW_CONSTITUTION.md` §6.3 |
| **The cost ceiling on governance, and the three-question review** | `governance/WORKFLOW_CONSTITUTION.md` §10 |
| **Operational directories** (`scratch/` / `archive/` / `_to_delete/`) | `governance/WORKFLOW_CONSTITUTION.md` §6.2 |
| Bibliography and sources | `policy/SOURCES.md` |
| External tools | `policy/EXTERNAL_TOOLS.md` |
| Model identity | `policy/MODEL_IDENTITY.md` |
| Audit tooling / tone / coverage declaration | `governance/Audit_Protocol.md` |

---

## 1. Document classes (by update frequency)

| Class | Files |
|---|---|
| **State** (overwritten each round) | `NEXT_SESSION_MEMO.md` |
| **Spec** (rarely changed) | `governance/*`, `policy/*`, `profiles/*`, `prompts/*` |
| **Data** (append-only) | `ledgers/*`, `handoffs/*`, `SENSOR_CHANGELOG.md` |
| **Index** | `file_index.md` (this file) |

---

## 2. Sensors

⚠️ **This section deliberately states no counts** — those are state (R-16). Check with:

```
python scripts/harness/run_all_sensors.py
python scripts/harness/run_selftest.py
```

| File | What it watches |
|---|---|
| `sensor_claim_ledger.py` | **Whether the anchor is really in the source** (zero cost) ＋ extraction tampering |
| `sensor_conjecture_ledger.py` | Falsification adjudication, rival hypotheses, field completeness |
| `sensor_self_certification.py` | Artefact self-certification and unsupported global appraisal |
| `sensor_governance_text.py` | Cross-file duplicates, section citations, state in spec documents |
| `sensor_scope_and_t0.py` | T0 uniqueness, write-scope violations, **the deny scope** |
| `sensor_reference_integrity.py` | **Whether a referenced file exists** (including `.py` / `.sh` headers) |
| `sensor_clause_sync.py` | **Whether a clause list copied elsewhere still matches its home** (the product of `R-24` × constitution §3.2) |
| `anchor_norm.py` | The normalisation function (**single home**) |
| `framework_config.py` | Path settings (**single home**) |
| `tool_pdf_to_md.py` | PDF → Markdown programmatic extraction (the corpus that link ② compares against — **not a sensor**) |
| `checkpoint.py` | **Single home** of the human/AI checkpoint (`.bat` / `.command` are thin shells) |
| `review_changes.py` | **Single home** of "what changed since I last reviewed" |
| `upgrade.py` | Check / diff / replace framework folders (⛔ never user data) |
| `tool_extract_compare.py` | Cross-checks two extracts: strict / loose / gap columns (**not a sensor**) — the gap column separates "normalisation does not cover this" from "the extraction is poor" |

### On demand (**not in the default suite — their interface is a single file**)

```
python scripts/harness/sensor_prompt_self_contained.py <prompt.md>
python scripts/harness/sensor_model_attribution.py
```

⚠️ **Forcing these into the runner only produces a permanently-INCOMPLETE false signal —
and INCOMPLETE is the one state this framework cannot afford to dilute.**
