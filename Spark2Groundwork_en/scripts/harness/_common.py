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


def cli(name):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import framework_config as fc
    root = pathlib.Path(a.root).resolve() if a.root else fc.ROOT
    return root, load(), a.json, name


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


def dead_glob_findings(dead, where):
    """Dead globs must be reported.

    ⚠️ **Same shape as a dead exemption: it looks like it is protecting something, and it is not.**
    A predecessor project had two globs that matched zero files from the day they were written —
    one because the directory had moved, one because the name was missing an "s".
    """
    return [("WARN", "SCAN_GLOB_MATCHES_NOTHING",
             f"{where}: glob '{g}' matched zero files — **it protects nothing**")
            for g in dead]
