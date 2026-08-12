#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Framework configuration — **the single source of settings for every sensor**.

## Why settings live in one file

Both predecessor projects hard-coded paths inside each sensor. The consequence:
**renaming one directory meant editing five programs, and the one you missed did not error.
It simply, quietly, scanned nothing.**

⚠️ Measured case (failure family ④): one project's scan list contained two globs that
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

    # Artefacts: things downstream will cite; subject to the self-certification check
    "artifact_globs": ["handoffs/*.md", "outputs/*.md", "reports/*.md"],

    # Always excluded from scans
    # (⚠️ evaluated on paths **relative to root** — see R-18)
    "excluded_dirs": ["archive", ".git", "__pycache__", "selftest", "scratch",
                      "node_modules", ".venv"],

    # Only needed for multi-role projects: each role's write scope.
    # Solo projects: leave as {} and the sensor will skip the check explicitly.
    "write_scopes": {},

    # Optional feature switches
    "enable_reference_authenticity": False,   # needs network access
    "enable_bat_checks": False,               # only if you use Windows batch files
}


def load():
    """Load settings. A user file, if present, overrides defaults (shallow merge)."""
    cfg = dict(DEFAULTS)
    if _USER.exists():
        try:
            cfg.update(json.loads(_USER.read_text(encoding="utf-8")))
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
