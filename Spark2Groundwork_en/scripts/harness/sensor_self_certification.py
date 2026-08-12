#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: artefact self-certification (failure family ⑦)

## Triggering case

In one project, 64 files all ended with:
> "All sample sizes, statistics and citations herein have been verified against the full
> originals, rigorously ensuring zero fabrication."

A fabricated sample size was found in the same batch.
**The claim was not merely unverifiable; it was demonstrably false.**

## Why this is its own failure type

**"Index as authority" is treating weak evidence as strong; "self-certification" is treating
"I say I did it" as "it was done" — the evidence does not exist at all.**
It is harder to catch, because what the reader sees is a passage that is careful in tone,
correct in terminology, and shows no visible seam.

## Criteria (**structural, not keyword hunting. All four must hit before FAIL**)

    (a) Self-reference    the subject is the document itself
    (b) Universal scope   all / every / none / entirely
    (c) Correctness object verified / checked / no errors / zero fabrication
    (d) Completive mood   ⛔ exempt if it contains must / shall / should / if / unless
                          — "any item that does not pass must not be submitted" is a **gate**,
                          which is exactly what we want, not a certification

    Further exemption: (e) names a tool, command, or file anyone can re-run

⚠️ **This sensor deliberately does not judge whether the claim is true** — that needs the source.
It judges only whether the sentence treats itself as evidence.
⛔ **The fix is to delete the claim or point at a tool, not to change "all" to "most"
in order to dodge a string match.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings          # noqa: E402
from framework_config import resolve_globs                 # noqa: E402

# ⚠️ Both English and CJK markers are kept. A framework used bilingually that only
#    matched one language would silently skip the other — failure family ④.
SELF = re.compile(r"this (?:document|file|report|summary)|herein|the present (?:report|document)"
                  r"|\u672c\u6587\u4ef6|\u672c\u5831\u544a|\u6587\u4e2d\u6240\u6709")
SCOPE = re.compile(r"\ball\b|\bevery\b|\bzero\b|\bnone\b|\bentirely\b|\bcompletely\b"
                   r"|\u6240\u6709|\u5168\u90e8|\u5168\u6578|\u7121\u4e00")
OBJECT = re.compile(r"verified|cross-?checked|no fabricat|without error|fully accurate"
                    r"|\u6838\u5be6|\u67e5\u8b49|\u9a57\u8b49|\u7121\u8aa4|\u96f6\u634f\u9020")
MODAL = re.compile(r"\bshould\b|\bmust\b|\bshall\b|\bif\b|\bunless\b|\brequired\b"
                   r"|\u4e0d\u5f97|\u5fc5\u9808|\u7981\u6b62")
TOOLPROOF = re.compile(r"`[^`]*\.(py|sh|md|json)`|scripts/|sensor_|run_[a-z_]+|[0-9a-f]{7,40}")
APPRAISAL = re.compile(r"extremely (?:high|robust)|very robust|flawless|airtight"
                       r"|no (?:holes|vulnerabilit)|nothing to fix|impeccable")


def main():
    root, cfg, as_json, name = cli("self_certification")
    files, dead = resolve_globs(cfg["artifact_globs"], root, cfg)
    findings = dead_glob_findings(dead, "artifact_globs")

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # ⛔ Never skip silently: unreadable is not the same as fine
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} is not UTF-8; not checked — **that is not a pass**"))
            continue
        for para in text.split("\n\n"):
            if MODAL.search(para) or TOOLPROOF.search(para):
                continue                       # gate or checkable -> exempt
            if SELF.search(para) and SCOPE.search(para) and OBJECT.search(para):
                findings.append(("FAIL", "UNVERIFIABLE_SELF_CERT",
                                 f"{p.relative_to(root)}：「{para.strip()[:52]}…」"
                                 " — an artefact must not claim it has verified itself"))
                break
        for para in text.split("\n\n"):
            if TOOLPROOF.search(para):
                continue
            if APPRAISAL.search(para) and SELF.search(para):
                findings.append(("WARN", "UNSUPPORTED_GLOBAL_APPRAISAL",
                                 f"{p.relative_to(root)}：global appraisal with no checkable basis"))
                break

    return emit("Self-certification sensor", findings, {"artefacts scanned": len(files)}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
