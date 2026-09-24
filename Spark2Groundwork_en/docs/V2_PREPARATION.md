# Preparing for v2 (no migration yet)

v2 is in development. There is no converter yet and no promise that every custom v1 format can be converted automatically. Keep using this version; do not rename folders or delete research data in anticipation of v2.

1. Copy the complete project to a backup outside the project, including hidden files, original sources, extractions, ledgers, drafts, custom rules, handoffs and Git history if present. Checkpoints can exclude files and do not replace a full backup.
2. Ask your AI to inventory the language, version markers in the five framework folders, modified framework documents, additional tools and custom data locations. Record mixed versions honestly; do not edit markers to simulate an upgrade. Save this inventory beside the backup if convenient.
3. Open representative drafts and sources from the backup to check readability. Keep the original project in use.
4. Near v2 completion, follow the official migration guide with AI assistance on a separate copy. Compare and verify before you decide to switch. Do not pre-convert now.

The planned v2 layout separates `agents framework/` (replaceable framework), `agents data/` (project-owned collaboration data) and `research data/` (project-owned research), with short entry documents at the root. Initialization selects one language; updates fetch the core and that language, without translating research drafts. Final details will be specified in the v2 release documentation.

Migration from v1.4.4 will not require installing v1.4.5 first. Updates must preserve original research. Source location, verification and human acceptance remain separate; a passing check does not establish research correctness.
