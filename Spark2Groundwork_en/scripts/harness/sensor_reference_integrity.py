#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: reference integrity -- **does the referenced file exist?**

## Checks

    DANGLING_FILE_REF         A reference to a file that is not in the project      FAIL
    REF_EXEMPTED_NOT_SHIPPED  Exempted because the same line says "not shipped"     WARN
    SCAN_GLOB_MATCHES_NOTHING The scan matched zero files                           WARN

## Why it is needed (**four measured cases, all in the framework itself**)

`sensor_governance_text.py` only checks whether a `` `<file>.md` §N `` **section** resolves,
**and it only scans `.md`.** That left two gaps open:

| Gap | Measured case |
|---|---|
| **`.py` headers were never scanned** | One sensor's header carried five dangling section citations and two dangling file references, all pointing at another project |
| **File existence was never checked** | A policy document promised a mechanical defence, and **that file does not exist in the framework** |

⚠️ **The third case was created by this sensor's own author:** while rewriting the sensor
above, **the old whitelist's filenames were quoted as examples in a comment** — and instantly
became new dangling references.
**"Do not instantiate a defect while describing it" — predecessor projects hit this same
mechanism three times; that was the fourth.**

## ⚠️ Two kinds of reference that are **not** defects, and how each is handled

| Form | Example | Handling |
|---|---|---|
| **Format placeholder** | `` `<filename>.md` §N `` | ⛔ Not checked. **The angle brackets are the criterion** — a placeholder you can see at a glance |
| **Explicitly not shipped** | "suggested filename `x.md` ... ⚠️ not shipped with this framework; create your own" | ✅ Exempt, **but it must be printed** |

🔴 **The exemption criterion is deliberately "an explicit marker on the same line", ⛔ not an
exemption list.**
⚠️ Lesson from predecessor projects: string matching cannot tell whose statement a name is,
and the first two times they dodged it by rewording. The third time the string was substantive
content and could not be reworded — **so they switched to an explicit marker, and required the
marker itself to be printed.** This sensor follows that.

⛔ **A silent exemption and no exemption look the same on screen.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE (**⛔ not a pass**)
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import resolve_globs, excluded         # noqa: E402

# Only references that look like project files: an extension, no leading whitespace
REF = re.compile(r"`([\w/.一-鿿-]+\.(?:md|py|sh))`")
# ⛔ Angle brackets mean placeholder, not reference
PLACEHOLDER = re.compile(r"[<>]")
# ✅ An explicit "not shipped" marker on the same line
NOT_SHIPPED = re.compile(r"not shipped|create your own|suggested filename|to be created"
                         r"|\u672a\u96a8\u9644|\u9808\u81ea\u5efa|\u5efa\u8b70\u6a94\u540d")


# -- Self-containment: this folder must work when copied out on its own ---------
# 🔴 **Measured case:** the first version of the architecture figure lived in `docs/`
#    at the **repository root**, and the README referenced it as `../docs/framework.svg`.
#    **Inside the repository it looked perfectly fine** — but the way users work is to copy
#    this whole folder into their own project,
#    ⛔ **and once copied the figure is gone while the README still cites it confidently.**
# ⚠️ **This class of dependency never errors in place**; it breaks only in someone else's hands.
ESCAPE = re.compile(r"(?:\]\(|src=[\"']|href=[\"'])\s*(\.\./[^\)\"'\s]+)")


def escapes_root(text):
    """Every reference that climbs out of this folder. ⛔ The criterion is the path, not intent."""
    return [m.group(1) for m in ESCAPE.finditer(text)]


def main():
    root, cfg, as_json, name = cli("reference_integrity")
    globs = (cfg.get("code_globs", ["scripts/**/*.py", "scripts/**/*.sh"])
             + cfg.get("launcher_globs", [])
             + cfg.get("governance_globs", []))
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "code_globs ＋ launcher_globs ＋ governance_globs", root)

    # Every filename actually present (any depth), for references written as a bare name
    present = {p.name for p in root.rglob("*") if p.is_file()}
    exempted, checked = [], 0

    for p in files:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} is not UTF-8; not checked "
                             f"-- **and that is not a pass**"))
            continue
        for esc in escapes_root("\n".join(lines)):
            findings.append(("FAIL", "REF_ESCAPES_EDITION",
                             f"{p.relative_to(root)}: cites `{esc}`, which **climbs out of "
                             "this folder** — ⚠️ this folder must work when copied out on its "
                             "own; ⛔ visible inside the repository is not visible after a copy"))
        for lineno, line in enumerate(lines, 1):
            for m in REF.finditer(line):
                ref = m.group(1).strip()
                if PLACEHOLDER.search(ref):
                    continue                      # a format placeholder, not a reference
                checked += 1
                if (root / ref).exists() or ref.split("/")[-1] in present:
                    continue
                if NOT_SHIPPED.search(line):
                    exempted.append(f"{p.relative_to(root)}:{lineno} `{ref}`")
                    continue
                findings.append(("FAIL", "DANGLING_FILE_REF",
                                 f"{p.relative_to(root)}:{lineno} references `{ref}`, "
                                 f"which is not in the project"))

    if exempted:
        # ⛔ An exemption must be visible (the "silent filtering" family)
        findings.append(("WARN", "REF_EXEMPTED_NOT_SHIPPED",
                         f"{len(exempted)} reference(s) exempted because the same line says "
                         f"they are not shipped: {'; '.join(exempted[:4])}"
                         f"{'...' if len(exempted) > 4 else ''}"
                         f" -- **an exemption is not an absence**"))

    return emit("Reference integrity sensor", findings,
                {"files scanned": len(files), "references checked": checked,
                 "explicit exemptions": len(exempted)}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
