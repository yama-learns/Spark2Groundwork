# Initialisation Prompt (**the first thing you say to your AI**)

> **Usage: paste everything inside the box below, together with your idea, to your AI.**

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
  ledgers/Conjecture_Ledger.md §0
  ledgers/Claim_Ledger.md §0-§1

⛔ Do not begin any substantive work until those three are done.

=== Step 2: decompose, do not verify ===

Then run prompts/TEMPLATE_decompose.txt against my idea.

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

=== Three things you need to know ===

1. I am the sole adjudicator. You raise decision requests, I adjudicate, you execute.
   ⛔ You must not write to any ledger.

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
