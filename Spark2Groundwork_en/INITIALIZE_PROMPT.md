# Initialisation Prompt (**the first thing you say to your AI**)

> **Usage: first put your idea in `FIRST_IDEA.md` beside this file, then paste everything
> inside the box below to an AI that can read this project.**

---

```
You will help me develop a research idea into an executable proposal.
This project uses a file-based governance framework.

=== Step 1: read, then restate ===

Read the following files in order, then do three things in your first reply:

  1. Declare your model (read verbatim from the authoritative source; if you cannot
     read it, write "cannot read" -- ⛔ do not substitute a platform name)
  2. Restate your write scope (see governance/WORKFLOW_CONSTITUTION.md §6 and the
     profiles/PROFILE_*.md I have chosen)
  3. In your own words, explain what this project's verification-level tags are

Required reading:
  governance/AGENTS.md
  governance/WORKFLOW_CONSTITUTION.md
  governance/RULES.md
  governance/Incident_Log.md          <- required on first participation
  my/MY_RULES.md                     <- project-custom rules (if present)
  ledgers/Conjecture_Ledger.md §0
  ledgers/Claim_Ledger.md §0-§1
  PROJECT.md
  FIRST_IDEA.md

⛔ Do not begin any substantive work until those three are done.

=== Step 2: decompose, do not verify ===

Then follow the decomposition rules in `FIRST_IDEA.md` and decompose the idea at its end.

⛔ Do not search the literature this round.
⛔ Do not evaluate whether the idea is good.
⛔ Do not propose a research design.

Reason: if the decomposition is already wrong, every paper you read afterwards is
evidence for the wrong thing.

=== Step 3: stop and wait ===

Stop when the decomposition is done. ⛔ Do not write to any ledger.

Report back in decision-request format (constitution §5):
  - how many conjectures you produced
  - which ones you could not give a falsification condition, and why
  - which two you think are actually the same one
  - which sentence in my original text you think is most valuable and I may not have noticed

=== Step 4: Closeout ritual (Constitution §4.2) ===

After finishing the decomposition and organizing decision requests, close out following Constitution §4.2 order:
  1. Run checks: execute `python scripts/harness/run_all_sensors.py` (if the environment lacks terminal access, remind the user to double-click `check_project.bat` / `.command`).
  2. Overwrite status memo: overwrite `NEXT_SESSION_MEMO.md`, recording current decomposition progress, unfinished items, and items awaiting adjudication.
  3. Deliver handoff packet: produce initial handoff packet in `handoffs/` (format in `governance/HANDOFF.md`, including complete list of this round's changes).
  4. Present the decision requests from Step 3 and await my adjudication.

=== Three things you need to know ===

1. I am the sole adjudicator. You raise decision requests, I adjudicate, you execute.
   ⛔ Ledgers are maintained by the user by default (protected by deny in governance_config.json); unless I explicitly authorize it and lift deny, you may not write to any ledger.

2. Every sentence carrying a number or an assertion needs a verification-level tag.
   ⛔ [checked]-level material must not be used to judge a claim false,
   nor to build a new hypothesis.

3. ⛔ Do not claim you have verified yourself.
   If you want to describe what you did, name a command or file I can re-run.
```

---

## After the first round

**Paste this at the start of each subsequent round:**

```
Follow the session-start ritual in governance/WORKFLOW_CONSTITUTION.md §4.1.
This round's task is in NEXT_SESSION_MEMO.md.
⛔ Do not copy any path or scope from this message -- use whatever the governance
documents currently say.
```

⚠️ **That last line is deliberate.**
A predecessor project copied the write scope into its dispatch template; when permissions changed,
the template did not, **so a document declaring "this file does not restate the scope"
restated an outdated version further down the same page.**
