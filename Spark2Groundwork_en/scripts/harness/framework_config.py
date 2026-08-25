#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Framework configuration — **the single source of settings for every sensor**.

## Why settings live in one file

Both predecessor projects hard-coded paths inside each sensor. The consequence:
**renaming one directory meant editing five programs, and the one you missed did not error.
It simply, quietly, scanned nothing.**

⚠️ Measured case (the "silent filtering" family): one project's scan list contained two globs that
**matched zero files from the day they were written** — one because the directory had moved,
one because the name was missing an "s".
**They looked like they were protecting something. They were not.**

→ So besides centralising settings, this file requires every sensor to
**report globs that match zero files**.

## How to change things

**Change only this file.** Then run `run_selftest.py` to confirm you did not break anything.
⛔ Do not hard-code paths inside individual sensors.
"""

import json
import pathlib

# ── Project root ──────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[2]

# ── User override: drop a governance_config.json in the project root ──
_USER = ROOT / "governance_config.json"

DEFAULTS = {
    # T0 required reading: exactly one copy each, project-wide.
    # Subdirectories must not hold copies.
    "t0_docs": ["governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"],

    # Governance documents (where rules live) — used by the duplicate and
    # section-reference checks.
    # ⚠️ These are **globs**, not a hard-coded list (R-21: whitelists filter silently)
    "governance_globs": ["governance/*.md", "policy/*.md", "ledgers/*.md", "file_index.md"],

    # Ledgers
    "conjecture_ledger": "ledgers/Conjecture_Ledger.md",
    "claim_ledger": "ledgers/Claim_Ledger.md",

    # Corpus: programmatically extracted full text; the comparison target for anchors.
    # ⛔ Extractions must never be hand-edited (R-14)
    "corpus_dir": "corpus_md",
    "corpus_manifest": "corpus_md/_manifest.json",
    # Source PDFs live here; tool_pdf_to_md.py reads it from here.
    # ⛔ Do not hard-code it again inside the tool: one home per rule (§3.2).
    "pdf_dir": "corpus",

    # 🔴 **Proposal-file markers.** A file under handoffs/ whose name contains one of
    #    these is exempt from the conjecture-citation existence check.
    #
    # ⚠️ **Why: the framework's own workflow contradicts its own sensor.**
    #    The workflow is "AI proposes -> human adjudicates -> human writes the ledger"
    #    (`governance/AGENTS.md` §5), so between proposal and adjudication **a proposal
    #    file necessarily cites IDs that do not exist yet**, and `CITATION_NOT_IN_LEDGER`
    #    necessarily FAILs. Measured: 12 in a single round.
    #    → Exactly the question `profiles/PROFILE_multi_agent.md` §4.3 G-1b asks:
    #      "can this new rule and an existing rule both be obeyed at the same time?"
    #
    # ⛔ **The criterion is deliberately structural (path + filename), not a free-text
    #    reason.** ⚠️ Lesson from a predecessor project: an exemption that required only
    #    "a reason" meant **one plausible sentence silenced the sensor on a real
    #    fabrication for good, with the dashboard green.**
    # ⛔ **Exempted files are always printed.** A silent exemption is the "silent filtering" family.
    "proposal_markers": ["pending-adjudication", "待套用"],

    # 🔴 **Scan scope for model attribution** (`sensor_model_attribution.py`).
    # ⚠️ Deliberately **only AI output**; ⛔ never the project root.
    #    Root-level .md files are framework templates (README / SETUP / file_index ...) and
    #    **were never supposed to carry an author field**. The old version scanned the root
    #    and therefore needed a hard-coded exemption list to suppress the alarms it created
    #    for itself — **a whitelist compensating for a wrong scan scope** (`R-21`).
    "attribution_globs": ["handoffs/*.md", "outputs/*.md", "reports/*.md"],

    # 🔴 **Scan scope for code** (`sensor_reference_integrity.py`).
    # ⚠️ The header comments of `.py` and `.sh` files are where rule citations
    #    accumulate, and nothing scanned them before.
    "code_globs": ["scripts/**/*.py", "scripts/**/*.sh"],

    # 🔴 **Launcher scripts** (`sensor_reference_integrity.py`).
    # ⚠️ **Measured: `.bat` and root-level `.command` files were in no sensor's scan
    #    scope** — `code_globs` only covered `scripts/**`, and these live at the root.
    #    Consequence: four `.bat` files carried 5 dangling references inherited from a
    #    predecessor project, unnoticed for a long time.
    #    **Same shape as decisions 12/14: residue hidden by a wrong scan scope.**
    # ⚠️ This file once had a dead switch called `enable_bat_checks` that nothing read.
    #    ⛔ This key is its opposite: a scope that actually reaches something.
    # ⚠️ ⛔ Do not put `*.sh` here: the root has none while `scripts/` does, so the
    #    coverage-collapse rule would fire ("files of that extension exist under the
    #    directory and the glob saw none"). **`.sh` belongs to `code_globs`.**
    "launcher_globs": ["*.bat", "*.command"],



    # 🔴 **Clause lists that are copied elsewhere** (`sensor_clause_sync.py`, decision 18).
    #
    # ⚠️ **This entry exists because two rules exclude each other:**
    #    `R-24` requires every prompt to be fully self-contained (so a template **must** carry
    #    its own copy of the banned list), while constitution §3.2 requires every rule to have
    #    exactly one home. **The product of that exclusion is drift.**
    #    Observed: `TEMPLATE_adversarial.txt` said "very 穩健" while `Audit_Protocol.md` §3
    #    says "very 強健" -- **one character, found only by a human comparing them.**
    #
    # ⛔ `home` is a **pointer**, not a scan scope -- copies are discovered via `marker`,
    #    and this framework keeps no list of copy filenames (`R-21`).
    "synced_lists": [
        {"id": "banned tone words",
         "home": "governance/Audit_Protocol.md",
         "marker": r"⛔.*Banned"},
    ],
    # Where copies may live. ⚠️ ⛔ `scripts/` is excluded --
    #    the changelog and the sensor source **describe** this list, and a description
    #    is not a copy.
    "sync_scan_globs": ["prompts/*.txt", "prompts/*.md", "governance/*.md",
                        "policy/*.md", "profiles/*.md"],

    # Artefacts: things downstream will cite; subject to the self-certification check
    "artifact_globs": ["handoffs/*.md", "outputs/*.md", "reports/*.md"],

    # Always excluded from scans
    # (⚠️ evaluated on paths **relative to root** — see R-18)
    #
    # ⚠️ **`excluded_dirs` and `write_scopes` are about different things.
    #    ⛔ Do not derive one from the other:**
    #    `excluded_dirs` = "do not look here when scanning" — it governs **sensor field of view**.
    #    `write_scopes`  = "who may write here"            — it governs **permission**.
    #    So `archive` can be both "not scanned" and "not writable". That **is not a contradiction**.
    # ⛔ **Never make the write_scopes check skip excluded_dirs automatically** — that hands the
    #    exclusion list a write exemption, and **the exclusion list exists to save scan cost,
    #    not to grant authority.**
        # ⚠️ What these directories ARE is defined in constitution §6.2; ⛔ this key only lists them.
    "excluded_dirs": ["archive", ".git", "__pycache__", "selftest", "scratch",
                      "_to_delete", "node_modules", ".venv"],

    # 🔴 **Paths the AI does not write to — ⚠️ a DEFAULT, ⛔ not a prohibition.**
    #
    # **A user may empty it; that is full authorisation** (constitution §6.3).
    # ⛔ **This framework has no standing to forbid that** — each project is the
    #    responsibility of its principal.
    #
    # ⚠️ **Why these three and not the governance documents:** the criterion is
    #    **restorability**. `governance/` `policy/` `prompts/` `scripts/` can be
    #    re-downloaded from GitHub and overwritten;
    #    🔴 **a broken ledger or corpus can be restored from nowhere.**
    # ⛔ Information, not persuasion — **what to do with it is the user's decision.**
    #
    # ⚠️ **The two T0 files are deliberately absent here** — a governance agent **may** now
    #    maintain them, **which is the precondition for a user keeping this framework alive.**
    #
    # ⚠️ **Only in effect when `write_scopes` is set** (the sensor reads `git status` and
    #    cannot tell a human's edit from an AI's).
    "deny": ["ledgers", "corpus", "corpus_md"],

    # Only needed for multi-role projects: each role's write scope.
    # Solo projects: leave as {} and the sensor will skip the check explicitly.
    "write_scopes": {},

    # ⚠️ enable_reference_authenticity and enable_bat_checks used to live here.
    #    ⛔ Nothing in the project ever read them — **a switch that looks like it turns
    #    something on, and turns nothing on.** Same shape as the dead glob this file warns
    #    about at the top, so they are gone.
    #    Link ⑤ is now watched per policy/SOURCES.md §3 and §5.
}


def load(root=None):
    """Load config; a user file overrides the defaults (shallow merge).

    ⚠️ **Why `root` exists:** the old version always read `ROOT/governance_config.json`,
    where `ROOT` is derived from **the sensor file's own location**. So pointing `--root`
    at another directory **changed the scan scope but not the config** — the sensor would
    check project B using project A's settings, ⛔ silently.
    **It also made any config-dependent behaviour untestable by fixtures.**
    """
    cfg = dict(DEFAULTS)
    user = (pathlib.Path(root) / "governance_config.json") if root else _USER
    if user.exists():
        try:
            cfg.update(json.loads(user.read_text(encoding="utf-8")))
        except Exception as e:                       # noqa: BLE001
            # ⛔ Never swallow this: broken settings with sensors still running
            #    means declaring a pass over the wrong scope.
            raise SystemExit(f"[FAIL] governance_config.json could not be parsed: {e}")
    return cfg


def excluded(path, root, cfg):
    """Is this path inside the exclusion list?

    ⚠️ **Must use relative paths** (R-18). Both predecessor projects hit this once:
    comparing absolute path parts excludes every file under the fixture directory,
    **making self-tests all-green or all-red** — and neither outcome looks like an
    exclusion-logic problem.
    """
    try:
        parts = set(pathlib.Path(path).resolve().relative_to(root).parts)
    except ValueError:
        return True
    return bool(parts & set(cfg["excluded_dirs"]))


def resolve_globs(globs, root, cfg):
    """Expand globs and report any that match zero files.

    Returns (files, dead_globs).
    ⚠️ **Dead globs must be reported** — they are the same shape as a dead exemption:
    they look like they are protecting something, and they are not.
    """
    files, dead = [], []
    for g in globs:
        hit = [p for p in root.glob(g) if p.is_file() and not excluded(p, root, cfg)]
        if not hit:
            dead.append(g)
        files.extend(hit)
    return sorted(set(files)), dead
