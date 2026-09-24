# Working State Memo

**Last updated:** <<<FILL IN: date>>>
**Maintenance rule: overwrite this file at the end of each session, ⛔ do not append. Remove anything that has landed.**

> ⚠️ **This is the only place in the project allowed to contain state** (along with any per-line `*_MEMO.md`).
> History and lessons live elsewhere: incidents → `governance/Incident_Log.md`;
> sensor changes → `scripts/harness/SENSOR_CHANGELOG.md`; cross-role items → `handoffs/`.
> **Restating them here only creates a second version that will drift.**

---

## 1. Current state

<<<FILL IN: one paragraph. Where things stand>>>

---

## 2. 🔴 Awaiting adjudication

| ID | Item | Raised in round | **Rounds waited** |
|---|---|---|---|
| — | *(none yet)* | — | — |

⚠️ **The "rounds waited" column is not decoration.** You are the single adjudication point;
when the queue grows faster than it drains, **the failure mode is "adjudication quality drops",
not "adjudication stops" — and that shows no red light.**

---

## 3. Next steps

| # | Item | Who |
|---|---|---|
| 1 | <<<FILL IN>>> | |

---

## 4. Deferred (**has a trigger; not rejected**)

| Item | Trigger |
|---|---|
| — | — |

---

## 5. Fixed actions before starting

- **AI assistant / automated environment:** Run `python scripts/harness/run_all_sensors.py` directly (0=PASS 1=FAIL 2=INCOMPLETE; `run_selftest.py` only needed if you changed a sensor).
- **Human user:** Double-click the root launcher button (`check_project.bat` on Windows / `check_project.command` on macOS); standard workflows do not require copying and pasting terminal commands.

⚠️ **Green covers only what is mechanised.** Argument quality, whether a source substantively
supports a claim, and honesty of generalisation are **deliberately not mechanised**.
