#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: Claim Ledger (evidence-chain link ②) — **the fulcrum of this framework**

## What it checks

**"Is that passage actually in the source?" — answered by string comparison, zero cost, checkable by anyone.**

⛔ **It does not check whether the passage supports the claim** (link ⑥). That is human work,
**deliberately not mechanised**.
**The anchor's job is to make "did anyone actually read the source" a checkable fact — not to read it for you.**

## Two checks

    ANCHOR_NOT_IN_SOURCE   Anchor not found in the extraction                         FAIL
    CORPUS_MD_MODIFIED     Extraction hash differs from manifest              FAIL

⚠️ **The second is a precondition for letting AI write to the corpus, not an add-on.**
All of the anchor check's force comes from one fact: the comparison target is a
programmatic extraction the model had no hand in.
**If a party with write access can alter that text, the evidence chain goes from
verifiable to circular — and silently so.**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                      # noqa: E402
from anchor_norm import norm                       # noqa: E402

HEAD = re.compile(r"^###\s+(M-\d+)\s*$")
FIELD = re.compile(r"^-\s*\*\*(.+?)[:：]\*\*\s*(.*)$")
PLACEHOLDER = re.compile(r"^(—|-|<<<.*>>>|)$")
# Surname pattern. The CJK range is intentional: author names are not always Latin,
# and a sensor that silently skips non-Latin sources is the "silent filtering" family.
SURNAME = re.compile(r"^\s*\**([^\W\d_][\w'’-]+)", re.UNICODE)


def parse(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = HEAD.match(line.rstrip())
        if m:
            cur = {}
            out[m.group(1)] = cur
            continue
        if cur is None:
            continue
        f = FIELD.match(line.rstrip())
        if f:
            cur[f.group(1).strip()] = f.group(2).strip()
    return out


def corpus_integrity(root, cfg):
    """Corpus integrity.

    ⚠️ **Three states, ⛔ not two.** "No corpus", "a corpus with nothing in it yet" and
    "a corpus that cannot be checked" are different things:
      no directory              → not applicable, skip silently
      directory, no extractions → nothing to protect yet, WARN
      extractions, no manifest  → INCOMPLETE
    **An over-broad criterion pays for itself by reporting "not applicable" as "at risk".**

    🔴 **Measured:** the framework began shipping an empty `corpus_md/` so that a new user can
    see where extractions go. **Every fresh project then reported INCOMPLETE on its first run**
    — ⛔ and a first run that cries wolf is exactly what teaches people to ignore the output.
    ⚠️ **The same shape as an earlier defect**: a tool created its output directory before
    checking whether there was anything to put in it.
    ⛔ **The fix is structural, not an exemption (`R-20`/`R-21`): the criterion now keys on
    whether extractions exist, ⛔ not on whether the directory exists.**
    """
    out = []
    cdir = root / cfg["corpus_dir"]
    if not cdir.is_dir():
        return out
    mp = root / cfg["corpus_manifest"]
    extracts = sorted(cdir.glob("*.md"))
    if not extracts and not mp.exists():
        return [("WARN", "CORPUS_EMPTY",
                 f"{cfg['corpus_dir']}/ holds no extractions yet — "
                 "**nothing to protect, and ⛔ nothing checked either**. "
                 "Put your PDFs in the source folder and run the extraction tool")]
    if not mp.exists():
        return [("INCOMPLETE", "CORPUS_MANIFEST_MISSING",
                 f"{cfg['corpus_dir']}/ exists but no manifest found — "
                 "**extractions are unprotected against tampering; not checked, and that is not a pass**")]
    try:
        man = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e:                                    # noqa: BLE001
        return [("INCOMPLETE", "CORPUS_MANIFEST_UNREADABLE", f"manifest could not be parsed：{e}")]
    known = {e["md"]: e.get("md_sha256") for e in man if "md" in e}
    for f in sorted(cdir.glob("*.md")):
        want = known.get(f.name)
        if want is None:
            out.append(("WARN", "CORPUS_FILE_UNTRACKED",
                        f"{f.name} is not in the manifest — re-run the extraction tool after adding sources"))
            continue
        if hashlib.sha256(f.read_bytes()).hexdigest() != want:
            out.append(("FAIL", "CORPUS_MD_MODIFIED",
                        f"{f.name} content no longer matches the manifest — "
                        "**the comparison target has been altered; every anchor result this round is untrustworthy**"))
    for name in known:
        if not (cdir / name).exists():
            out.append(("FAIL", "CORPUS_FILE_DELETED", f"{name} has disappeared but is still listed in the manifest"))
    return out


def main():
    root, cfg, as_json, name = cli("claim_ledger")
    findings = corpus_integrity(root, cfg)
    led = root / cfg["claim_ledger"]
    if not led.exists():
        findings.append(("INCOMPLETE", "CLAIM_LEDGER_MISSING",
                         f"{cfg['claim_ledger']} not found — **not checked, and that is not a pass**"))
        return emit("Claim Ledger sensor", findings, {}, as_json, name)

    entries = parse(led.read_text(encoding="utf-8"))
    cdir = root / cfg["corpus_dir"]
    corpus = {p.name: norm(p.read_text(encoding="utf-8", errors="replace"))
              for p in cdir.glob("*.md")} if cdir.is_dir() else {}
    checked = matched = 0

    for cid, f in entries.items():
        anchor = f.get("Verbatim anchor", "").strip().strip("`")
        src = f.get("Source", "")
        if PLACEHOLDER.match(anchor) or "<<<" in anchor:
            findings.append(("WARN", "ANCHOR_EMPTY", f"{cid} anchor is empty or still the template"))
            continue
        if not corpus:
            findings.append(("INCOMPLETE", "CORPUS_ABSENT",
                             f"{cid} cannot compare: corpus is empty — **not checked is not a pass**"))
            continue
        m = SURNAME.match(src)
        key = m.group(1).lower() if m else ""
        cands = [t for n, t in corpus.items() if key and key in n.lower()] or list(corpus.values())
        checked += 1
        if any(norm(anchor) in t for t in cands):
            matched += 1
        else:
            findings.append(("FAIL", "ANCHOR_NOT_IN_SOURCE",
                             f"{cid} anchor not found in the corpus：「{anchor[:56]}…」"))

    code = emit("Claim Ledger sensor", findings,
                {"claims": len(entries), "extractions": len(corpus),
                 "anchors matched": f"{matched}/{checked}"}, as_json, name)
    if not as_json:
        print("      ⚠️ This sensor only checks that the anchor exists,")
        print("      not whether the source supports the claim (links 6 and 7)")
    return code


if __name__ == "__main__":
    sys.exit(main())
