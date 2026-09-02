#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared sensor scaffolding — uniform output format and exit codes.

⛔ **The three exit codes must not be conflated** (constitution §7.4):
    0 PASS | 1 FAIL (a definite defect) | 2 INCOMPLETE (could not check — **not a pass**)
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from framework_config import load, resolve_globs, excluded   # noqa: E402,F401

def _force_utf8():
    """⛔ **Output must be UTF-8; ⛔ never rely on the system default.**

    🔴 **Measured case (Traditional-Chinese Windows):** Python's default output encoding on
    Windows is the system ANSI code page (`cp950` there), while every message this framework
    prints contains `✅` / `⚠️` / `⛔`.
    **So a sensor crashes with `UnicodeEncodeError` at the first symbol it prints.**

    ⚠️ **What makes it worse is how it crashes:** an uncaught Python exception always exits
    with **1**, **and `run_all_sensors.py` reads exit 1 as "found a defect" (FAIL), not as
    "could not check" (INCOMPLETE).**
    🔴 **So the screen said "the whole suite FAILED" while what actually happened was that two
    sensors never finished running** — **exactly the confusion `R-22` and constitution §7.4
    exist to prevent, occurring inside the framework itself.**

    ⛔ `errors="replace"` is deliberate: **the worst case is a printed `?`, ⛔ not a dead process.**

    ## 🔴 ⛔ What this function covers: **only what WE print out**

    ⚠️ **⛔ It does ⛔ not cover what we read in.**
    **A child process's output is decoded by `subprocess` itself, ⛔ and with `text=True`
    and no `encoding` that means the locale encoding (Traditional-Chinese Windows = `cp950`).**

    🔴 **Measured (2026-08-27, Python 3.14.2): `sensor_scope_and_t0.py` therefore received
    `returncode == 0` with `stdout` set to `None`** — **the decode blew up inside
    `subprocess`'s reader thread, the thread died, and the exception ⛔ never reached the
    main thread.**

    ⛔ **⇒ Every `subprocess.run` that reads output must state
    `encoding="utf-8", errors="replace"` itself. ⚠️ This function ⛔ cannot help it.**
    **Watcher: `subprocess_encoding_case()` in `run_selftest.py` (a static check).**

    ⚠️ **⛔ This section was added afterwards: the function used to read as though
    "encoding has been dealt with", 🔴 which was a true sentence whose scope did not
    cover the other channel (`R-34`).**
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if sys.platform == "win32":
        # Make the console render UTF-8 too; without this it does not crash, it just garbles.
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:                                    # noqa: BLE001
            pass


_force_utf8()


def cli(name):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import framework_config as fc
    root = pathlib.Path(a.root).resolve() if a.root else fc.ROOT
    # ⚠️ Config comes from **the root being scanned** — see framework_config.load.
    return root, load(root), a.json, name


def emit(title, findings, stats, as_json, sensor):
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    # ⚠️ An INCOMPLETE-level finding must make the whole verdict INCOMPLETE.
    #    A predecessor project made `incomplete` a separate boolean parameter, so the
    #    screen printed [INCOMPLETE] while the summary said PASS with exit code 0 —
    #    **the project's most fundamental rule violated by its own tooling.**
    #    More worth remembering than the defect is its shape:
    #    **one verdict with two sources, and only one of them updated.**
    inc = [f for f in findings if f[0] == "INCOMPLETE"]
    code = 2 if inc else (1 if fails else 0)
    label = {0: "PASS", 1: "FAIL", 2: "INCOMPLETE (**not a pass**)"}[code]
    if as_json:
        print(json.dumps({"sensor": sensor,
                          "status": {0: "PASS", 1: "FAIL", 2: "INCOMPLETE"}[code],
                          "findings": [{"level": l, "code": c, "message": m}
                                       for l, c, m in findings], "stats": stats},
                         ensure_ascii=False, indent=2))
    else:
        print(f"-- {title} " + "-" * max(0, 40 - len(title)))
        for k, v in stats.items():
            print(f"  {k}: {v}")
        for l, c, m in findings:
            print(f"  [{l}] {c}: {m}")
        print(f"  Result: {label} ({len(warns)} warnings)")
    return code


def _glob_dir(root, g):
    """The **scan directory** a glob points at; ⛔ None if the pattern is not a scan scope.

    ⚠️ **A pattern with no wildcard (e.g. `file_index.md`) names one specific file, not a
    scan scope.** The first version resolved its "directory" to the project root, and the
    root always holds files — **so every fixture missing that file was reported as coverage
    collapse. The self-test caught seven regressions immediately.**
    → Such patterns return None and are handled by the `WARN` (file not present) path.
    """
    if "*" not in g:
        return None
    head = g.split("*", 1)[0]
    if not head:
        return root
    return (root / head) if head.endswith("/") else (root / head).parent


def dead_glob_findings(dead, where, root=None):
    """Globs that match zero files must be reported.

    ⚠️ **Same shape as a dead exemption: it looks like it is protecting something, and it is not.**
    A predecessor project had two globs that matched zero files from the day they were written —
    one because the directory had moved, one because the name was missing an "s".

    ## 🔴 Two different things look identical here (decision 20)

    | Situation | What it is | Level |
    |---|---|---|
    | **The directory does not exist** | This project is not using that part yet | `WARN` — normal for a new project |
    | **The directory exists and holds zero files** | 🔴 **coverage collapse** | `INCOMPLETE` (exit 2) |

    ⚠️ **Triggering case (measured in another project):** one round of adversarial testing found
    **five sensors** printing PASS whenever the comparison set became empty — **"nothing to
    compare against" and "everything compared consistently" produce identical output, because a
    consistency test over an empty set is vacuously true.**

    ⛔ **But promoting every case to exit 2 is wrong:** a brand-new project's first run would
    return INCOMPLETE, and constitution §4.1.1 says exit 2 means "stop and report" — **directly
    contradicting `SETUP.md`, which tells the user a batch of warnings on the first run is
    normal. And a permanent red light teaches people to ignore the whole system (`R-19`).**

    → **The criterion is structural: does the directory exist. ⛔ No history required.**
    """
    out = []
    cfg = load(root) if root is not None else None
    for g in dead:
        # ⚠️ **The criterion was narrowed twice, and the self-test caught both:**
        #    (1) "the directory exists" => a freshly created, unused directory was INCOMPLETE.
        #    (2) "the directory holds anything" => `scripts/**/*.sh` was reported as collapse
        #        in a project holding only `.py`, **which just means "no files of that kind".**
        #    → Final criterion: **files of the same extension do exist under that directory,
        #      and this glob saw none of them.** That is "the files are there and the glob
        #      cannot see them" — wrong depth, wrong name pattern.
        d = _glob_dir(root, g) if root is not None else None
        suffix = pathlib.Path(g).suffix
        collapsed = bool(d and d.is_dir() and suffix
                         and any(f.is_file() and not excluded(f, root, cfg)
                                 for f in d.rglob("*" + suffix)))
        if collapsed:
            out.append(("INCOMPLETE", "COVERAGE_COLLAPSE",
                        f"{where}: glob '{g}' — **the directory exists and holds zero files**"
                        " — ⚠️ this is not 'nothing wrong', it is **could not check**. "
                        "'Nothing to compare against' and 'everything matched' look the same"))
        else:
            out.append(("WARN", "SCAN_GLOB_MATCHES_NOTHING",
                        f"{where}: glob '{g}' matched zero files "
                        "(⚠️ the directory does not exist, or it exists and holds no file "
                        "of that extension yet) — **it protects nothing right now** "
                        f"(⚠️ not applicable is not a pass)"))
    return out
