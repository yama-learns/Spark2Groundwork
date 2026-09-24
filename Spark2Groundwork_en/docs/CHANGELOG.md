# v1.4.5 changes (2026-09-24)

- Mac index/configuration compatibility fixes preserve custom exclusions.
- Buttons for checks, saves, human-reviewed snapshots, diffs, update checks and rule sync; saving is not human review.
- Missing dependencies and interpreter crashes report incomplete, with clearer guidance.
- [Preparing for v2](V2_PREPARATION.md) adds backup and inventory guidance, without moving research data.

Mac automated processes are checked in GitHub Actions; native Finder, Gatekeeper and physical-machine double-click acceptance remain pending and are not reported as passed.

- Scope checks now include committed and reverted changes since the human-reviewed snapshot. A missing or unrelated `reviewed` baseline reports INCOMPLETE. Inspect the project and use the existing human-reviewed snapshot button to establish a baseline only after you have reviewed it; saving alone does not establish human review.
- The check is read-only, including Git index metadata. Malformed Git output reports INCOMPLETE.
- Coverage boundary: tracked assume-unchanged / skip-worktree flags and .gitignore-ignored files inside deny or outside declared scopes now report INCOMPLETE rather than passing silently; clearing flags or fixing configurations restores normal checks. Regular research attachments and framework caches pass quietly. This check does not authenticate authors or protect against rewriting Git history or moving the reviewed baseline. A legitimate new human review deliberately advances that baseline.


### E2b repair: generated metadata and recovery

The scope sensor reads ignored paths with `git ls-files --others --ignored --exclude-standard -z`. It exempts only Finder `.DS_Store` files, the exact `scripts/harness/harness_status.json` report and root `git-checkpoint.log`; it reports the excluded count. These are generated metadata, including beneath protected folders. An exact deny entry naming one of these files overrides this exemption. Similar names, other JSON/log files and arbitrary `.gitignore` rules do not gain this exemption. Tracked changes and hidden tracked flags still undergo the normal checks.

A protected ignored research file is genuinely outside Git's evidence: moving the reviewed tag cannot establish its contents or history. INCOMPLETE here is not an accusation of an AI change. Ask your AI to list the paths and explain the choice; you need not type terminal commands. After your approval, the AI can add protected files to **local** version tracking (this does not upload them), verify the change and complete the normal human-review process. If you intentionally want untracked material, the AI can propose placing it outside protected scope and updating references, for your approval. Do not delete research data, clear all deny rules, or advance reviewed just to hide the warning. Large/private data should not be uploaded without your separate approval.

Hidden flags must likewise be explained before the AI removes them; real sparse checkout may require a complete working tree for this check. Inspection itself does not change files, index, flags or reviewed. This release does not build a second hash-baseline system for ignored files.

### E3a repair: Chinese conjecture ledger cross-tree target configuration

Fixed a defect in the Chinese `sensor_conjecture_ledger.py` where cross-tree `--root` invocations read module-level configuration instead of the target project's configuration. The sensor now respects custom conjecture ledger paths, proposal markers, and excluded directories specified in the target's `governance_config.json`. The English edition preserves its existing correct behavior; all selftests and cross-tree integration tests pass.

### E3b repair: Bilingual startup, initialization, solo profile, and closeout contradictions

Fixed documentation contradictions (D-1 through D-6):
- `PROFILE_solo.md` and `Audit_Protocol.md`: Clarified that while single-AI projects do not run two-model adversarial audits, automated sensors rely on `Audit_Protocol.md` for clause definitions and specs; instructed keeping the file rather than deleting it, and updated section 2 heading.
- Project rule path: Corrected the governance AI start prompt to direct custom rule proposals to `my/MY_RULES.md` (rather than `governance/RULES.md` which is overwritten on upgrade).
- Ledger permissions: Standardized exclusion headings to closed-by-default (`**⛔ Closed to you by default:**` / `**⛔ 預設不可以寫入：**`); aligned start prompts and initialization prompts across all three roles with constitution §6.1/§6.3 and `deny` in `governance_config.json` (maintained by user by default; requires explicit authorization and removal from deny, with auditor prohibited from self-exemption).
- Initialization and closeout ritual: Added `my/MY_RULES.md` to the required reading list in `INITIALIZE_PROMPT.md`, and added Step 4 closeout ritual strictly aligned with Constitution §4.2 order (checks → memo overwrite → initial handoff packet → decision requests).
- Standard user workflows: Section 5 of `NEXT_SESSION_MEMO.md` clarifies direct execution by AI environments versus double-clicking root launcher buttons, without requiring users to copy-paste terminal commands.

### E3b r3 correction: Solo profile retention list

Following the earlier Solo guide and deleting the other three profiles made the full sensor run fail in both editions because of dangling references. Solo users should retain all supplied profile files; retaining a file does not activate another collaboration mode. The required keep list now also includes the root `check_project` launcher.

### V145-REVIEW-BASELINE-1: Stop comparison without a human-reviewed baseline

Both Review Changes entry points now report INCOMPLETE / exit 2 when HEAD is missing, `refs/tags/reviewed` is not a valid commit, the tag is outside the current HEAD history, or a Git query fails. They no longer substitute HEAD and announce no unread changes. With a valid human baseline, they still list AI-saved commits, working-tree changes, and untracked files without moving the reviewed tag.
