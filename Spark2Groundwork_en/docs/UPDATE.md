# Updating, saving and confirming review without pasted commands

## Choose the right button

Double-click .bat on Windows or the same-named .command on Mac. Read the result and press a key to close. For missing tools, use the [startup guide](START_HERE.html).

| Button | Action and writes |
|---|---|
| save_progress | Save current contents using Git; may initialize Git and write commits/logs, but never advances the reviewed marker |
| snapshot | The existing human-review confirmation. Press only after reading the contents; advances the reviewed marker. AI must not press for you |
| review_changes | Show changes since the reviewed marker; does not change it or prove you read the output |
| check_update | Look up the release and, when _upgrade exists, compare local packages; does not apply updates |
| sync_rules | Save a tool restore point first; stop if it fails. Append missing rules without replacing existing text, then check for drift |

Use save_progress for unread work. In a new project, read your starting contents and press snapshot before assigning work to establish a human baseline. Without that marker, review_changes reports INCOMPLETE (exit 2) and does not substitute HEAD for human review. If work was saved before you read it, ask your AI to inventory it and read it yourself; only then personally press snapshot.

## Update with your file manager

1. Pause AI writes and close editors. Copy the **entire project, including hidden .git and settings**, to an external backup folder and check that research files open. Keep the backup outside the project. Save unread work with save_progress, not snapshot.
2. Download a new ZIP from the original GitHub repository and extract it. Put the complete matching-language Spark2Groundwork_en (or Spark2Groundwork_zh) folder inside `_upgrade/` at your project root. Do not mix editions.
3. Press check_update and read the version and differences. A version marker is not proof of complete contents. Local comparison can still run when the release lookup is offline; a failed lookup never means you are up to date.
4. Replace **one package at a time**: governance, profiles, prompts, scripts, docs. First compare the inventory yourself or with AI. Move project-owned files/tools out of the old package (for example to my/tools) and fix their references. Stop if ownership is unclear. Move the old package outside the project into your backup area, then insert the complete new same-named folder. Do not merge folders and silently retain retired files. Read each package's differences and stop on a problem.
5. At root replace only README.md, SETUP.md, INITIALIZE_PROMPT.md, file_index.md and this edition's framework buttons. Preserve custom text from old root guides in project-owned documents and keep references. Leave PROJECT.md, FIRST_IDEA.md (第一個想法.md in Chinese), my, ledgers, corpus, corpus_md, governance_config.json and all custom files in place. Never replace the whole project with the fresh download.
6. Do not replace .gitignore or .gitattributes wholesale: they contain both framework defaults and user rules. Ask AI to compare defaults and add only missing requirements. A project can keep only .bat or .command for its platform. Handle a blocked Mac file using the startup guide, never by clearing protections for the whole folder.
7. After replacing governance, press sync_rules. For RULE_TEXT_DRIFT, have AI show the differing clauses; decide whether to take the new text or retain a reasoned project override. Edit only that clause, never the entire my/MY_RULES.md, and rerun the button. Unresolved drift is not complete.
8. After all intended packages are replaced, press check_project and review_changes. Mixed versions during an incomplete update are reported; partial replacement is not a completed upgrade. Only after your actual review should you press snapshot to advance the human baseline. Retain the backup until verification finishes.

Manual replacement has no automatic per-package transaction or restore point. Your **full external backup** is the recovery source. On failure, stop and preserve the message; restore the complete backup into another location and check it, rather than overwriting the only surviving research copy. An AI with local execution access may use the existing per-package upgrade tool after your authorization; its restore point is not human review either. A read-only/remote AI can still help compare inventories without asking you to paste commands.

## Additional checks for older projects

- Before v1.4.3, preserve the filled prompts/TEMPLATE_decompose.txt as root FIRST_IDEA.md (第一個想法.md in Chinese). Move custom tools to my/tools and repair references. If you authorize a governance role to maintain my, have AI add only that role's needed write_scopes to governance_config.json; do not replace the settings.
- policy/ retired in v1.4.4. Confirm SOURCES.md, MODEL_IDENTITY.md, HANDOFF.md and EXTERNAL_TOOLS.md exist in the new governance folder, then move old policy outside the project for safekeeping. Manual replacement does not discover or remove it automatically.
- v1.4.1/v1.4.2 upgrades may have advanced the reviewed marker incorrectly. If its provenance is uncertain, do not trust that baseline to expose all unread work or guess a rollback point. Keep a full backup, use AI to inventory the material, and reread the research content you are responsible for before confirming a new human baseline. An AI with local execution access can investigate exact history; ordinary users need not paste Git commands.

## Finder files and connection problems

New defaults ignore .DS_Store, but previously tracked Finder files remain tracked. Have an AI with local execution access **first list the exact Git-tracked .DS_Store paths**, then, after you confirm, untrack only those files while retaining disk copies. Do not perform broad cleanup or delete research files. If the AI cannot execute locally, leave the harmless metadata for later and do not claim it was cleaned.

For TLS/certificate errors, check date/time, network sign-in and certificate setup in the official Python installation guidance. Never disable certificate verification, import an unknown certificate or share credentials. For DNS/offline failures, retry later or download the official ZIP separately and compare locally. A failed lookup is not evidence that no newer version exists. If a tool hangs, close its result window and retain the message; do not repeatedly click, remove locks or reinstall over research files.
