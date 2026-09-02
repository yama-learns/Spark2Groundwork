#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: are the framework packages all on the same version?

## Why this exists

🔴 **Upgrading replaces one package at a time, ⛔ and "half-replaced" produces no error.**

⚠️ **Real case (Project D, 2026-08-31):** `governance/`, `profiles/` and `docs/` were at
v1.4.2 while `policy/` was still at v1.3.0. **The project looked fine: every sensor green,
every self-test passing.** ⛔ **No sensor was looking at "are these packages the same
version", so that state was silent — ⛔ and it took an outside audit to find it.**

## ⛔ What it does not claim

⛔ **A version marker only answers "what does this folder call itself"; ⛔ it does not
prove the contents are complete.**
⚠️ **The same Project D had the other half too: `prompts/_VERSION` read v1.4.2 while
`prompts/_COMMON_BLOCKS.md` was still v1.3.0 content.**
🔴 **⇒ This sensor catches "the labels disagree", ⛔ not "the labels agree and the
contents differ".** **The required action for that is `upgrade.py diff`, ⛔ not this
sensor. Written down here rather than left blank.**

## Three checks

    VERSION_MISMATCH      packages report different versions (= half an upgrade)   FAIL
    VERSION_UNREADABLE    package is there, ⛔ but its `_VERSION` cannot be read   INCOMPLETE
    PACKAGE_ABSENT        this project does not have that package                  WARN

⚠️ **`PACKAGE_ABSENT` is a `WARN`, ⛔ not a `FAIL`:** a project may legitimately lack a
package (upgraded from an older version, `docs/` not yet added), 🔴 **and "you are missing
a package" is a different thing from "two of your packages disagree", with a different fix.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402


def read_version(p):
    """Take the first non-comment, non-blank line.

    ⚠️ **Same rule as `upgrade.py::read_version()`.**
    ⛔ **If the two implementations diverge, this sensor and the upgrade tool will report
    different versions for the same file** — 🔴 **which is exactly the shape this sensor
    exists to catch, happening to the sensor itself (constitution §3.2).**
    """
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                return s
    except Exception:                                       # noqa: BLE001
        return None
    return None


def survey(root, cfg):
    """Return (versions found, packages absent, packages unreadable).

    ⛔ All three need a denominator (`R-35`).
    """
    pkgs = cfg.get("version_packages",
                   ["governance", "profiles", "prompts", "scripts", "docs"])
    fname = cfg.get("version_file", "_VERSION")
    found, absent, unreadable = {}, [], []
    for name in pkgs:
        d = root / name
        if not d.is_dir():
            absent.append(name)
            continue
        v = read_version(d / fname)
        if v is None:
            unreadable.append(name)
        else:
            found[name] = v
    return found, absent, unreadable


def main():
    root, cfg, as_json, name = cli("version_consistency")
    findings, stats = [], {}
    found, absent, unreadable = survey(root, cfg)

    stats["packages"] = len(found) + len(absent) + len(unreadable)
    stats["versions read"] = len(found)

    for pkg in absent:
        findings.append(("WARN", "PACKAGE_ABSENT",
                         f"this project has no `{pkg}/` — "
                         "**⚠️ a project upgraded from an older version may not have it; "
                         "`upgrade.py apply " + pkg + "` adds it back**"))
    for pkg in unreadable:
        findings.append(("INCOMPLETE", "VERSION_UNREADABLE",
                         f"`{pkg}/` is there, ⛔ but its version marker cannot be read — "
                         "**⛔ this package was not compared this round, and that is not "
                         "the same as it being right**"))

    versions = set(found.values())
    if len(versions) > 1:
        rows = ", ".join(f"{k}={v}" for k, v in sorted(found.items()))
        # 🔴 **This deliberately makes ⛔ no claim about which version is newest
        #    (adjudication `A4b: B`, 2026-09-02).**
        #    ⚠️ **The old code used `sorted(versions)[-1]`, a string sort** — measured,
        #    **`{v1.9.0, v1.10.0}` selects `v1.9.0`, ⛔ which is the older one.**
        #    🔴 **The deeper reason: this sensor cannot see `_upgrade/`, ⛔ so it has no way to
        #    know the target version.** **"Which version to bring them up to" is answered by the
        #    upgrade source, and that is `upgrade.py diff`'s job (`R-34`).**
        findings.append(("FAIL", "VERSION_MISMATCH",
                         f"framework packages are not on one version: {rows} — "
                         "🔴 **half an upgrade.** "
                         "**Run `upgrade.py diff` to see which version the new source is, "
                         "then replace one package at a time** "
                         "(⛔ this sensor cannot see the upgrade source, so it ⛔ does not "
                         "decide the target version for you)"))
        stats["🔴 distinct versions"] = len(versions)
    elif versions:
        stats["version"] = versions.pop()

    if not found:
        findings.append(("INCOMPLETE", "VERSION_UNREADABLE",
                         "not one framework package version could be read — "
                         "**⛔ this could not be checked; that is not a pass**"))
    return emit("version consistency sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
