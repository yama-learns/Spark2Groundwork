#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: T0 uniqueness and write scope

## Two checks

    T0_DUPLICATE_IN_SUBDIR   A subdirectory contains a file named like a T0 document   FAIL
    WRITE_OUT_OF_SCOPE       This round's changes fall outside the declared scope      FAIL

⚠️ **Why T0 uniqueness is FAIL rather than WARN:**
**You change one and miss the others, and each one reads fine on its own.**
This is the hardest-to-notice form of the "fixed one layer, missed another" family.

⚠️ **Solo projects should leave `write_scopes` empty** — the sensor will say
"not applicable" explicitly, **rather than passing silently**.

## Two pits already fallen into (**written here because they will recur**)

1. `git rev-parse --show-toplevel` must equal the project root.
   Otherwise, when the project sits inside another repository, **it reports against the
   wrong repository, and does so with complete confidence.**
2. `git -c core.quotepath=false`. Otherwise non-ASCII paths print as octal escapes, and
   **the one column you actually need to read — which file changed — becomes a string of digits.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from framework_config import excluded                      # noqa: E402


def git_changed(root):
    """This round's change list. Returns (list, error message)."""
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=20)
        if top.returncode != 0:
            return None, "version control not initialised"
        if pathlib.Path(top.stdout.strip()).resolve() != root.resolve():
            # ⛔ Do not skip this. See pit 1 in the header.
            return None, "the project sits inside another repository — **refusing to report, to avoid judging the wrong repo**"
        r = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false",
                            "status", "--porcelain"],
                           capture_output=True, text=True, timeout=20)
        return [ln[3:].strip().strip('"') for ln in r.stdout.splitlines() if ln.strip()], None
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git could not run：{e}"


def main():
    root, cfg, as_json, name = cli("scope_and_t0")
    findings = []

    # (1) T0 uniqueness
    t0_names = {pathlib.Path(t).name for t in cfg["t0_docs"]}
    t0_paths = {(root / t).resolve() for t in cfg["t0_docs"]}
    for p in root.rglob("*.md"):
        if excluded(p, root, cfg) or p.resolve() in t0_paths:
            continue
        if p.name in t0_names:
            findings.append(("FAIL", "T0_DUPLICATE_IN_SUBDIR",
                             f"{p.relative_to(root)} — exactly one copy of each T0 exists project-wide. "
                             "**Change one and miss the others; each reads fine on its own**"))

    # (2) Write scope
    scopes = cfg.get("write_scopes") or {}
    stats = {"T0 documents": len(cfg["t0_docs"])}
    if not scopes:
        stats["write scope"] = ("write_scopes not set; not applicable "
                                "(⚠️ not applicable is not a pass)")
    else:
        changed, err = git_changed(root)
        if changed is None:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{err} — **not checked, and that is not a pass**"))
        else:
            allowed = [a.rstrip("/") for v in scopes.values() for a in v]
            # 🔴 **deny: no role may write here.** The first mechanical counterpart to
            #    constitution §6, general rule 2.
            #    ⚠️ The two T0 files are folded in from `t0_docs` — ⛔ never restated in
            #    `deny` itself (constitution §3.2).
            denied = ([d.rstrip("/") for d in cfg.get("deny", [])]
                      + [t.rstrip("/") for t in cfg["t0_docs"]])
            # ⚠️ `_human` is not a role, it is an exception. **Its cost is written down in
            #    framework_config; the duty here is that ⛔ the number of exempted hits must
            #    be printed.** A silent exemption and no exemption look the same on screen
            #    (the "silent filtering" family).
            human = [h.rstrip("/") for h in scopes.get("_human", [])]

            def under(path, tops):
                return any(path == a or path.startswith(a + "/") for a in tops)

            exempted = 0
            for c in changed:
                if under(c, denied):
                    if under(c, human):
                        exempted += 1
                        continue
                    findings.append(("FAIL", "WRITE_TO_DENIED_PATH",
                                     f"{c} falls inside the deny scope — **⛔ no AI role may "
                                     f"write here** (constitution §6, general rule 2)"))
                    continue
                if not under(c, allowed):
                    findings.append(("FAIL", "WRITE_OUT_OF_SCOPE",
                                     f"{c} is not in any role's declared scope"))
            stats["changes this round"] = len(changed)
            stats["deny entries"] = len(denied)
            if exempted:
                stats["⚠️ deny hits exempted by _human"] = (
                    f"{exempted} — **an exemption is not an absence; it is a judgement that "
                    f"a human made the change**")

    return emit("Scope and T0 sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
