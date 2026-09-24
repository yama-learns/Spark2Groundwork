#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: Claim Ledger (evidence-chain link ②) — **the fulcrum of this framework**

## What it checks

**"Is that passage actually in the source?" — answered by string comparison, zero cost, checkable by anyone.**

⛔ **It does not check whether the passage supports the claim** (link ⑥). That is human work,
**deliberately not mechanised**.
**The anchor's job is to make "did anyone actually read the source" a checkable fact — not to read it for you.**

## Checks

    ANCHOR_NOT_IN_SOURCE   Anchor not found in the extraction                         FAIL
    CORPUS_MD_MODIFIED     Extraction hash differs from manifest              FAIL
    CLAIM_NONE_CHECKED     Valid claims exist but none reached verification   INCOMPLETE

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


def is_valid_claim(f):
    """Determine whether an entry is a valid substantive claim (not purely placeholder/empty)."""
    stmt = f.get("Statement", "").strip().strip("`").strip()
    src = f.get("Source", "").strip().strip("`").strip()
    anc = f.get("Verbatim anchor", "").strip().strip("`").strip()
    # Only a whole-field placeholder is empty. Substantive text that happens to
    # mention the reserved `<<<` marker must not be silently treated as a template.
    is_empty_stmt = bool(PLACEHOLDER.fullmatch(stmt))
    is_empty_src = bool(PLACEHOLDER.fullmatch(src))
    is_empty_anc = bool(PLACEHOLDER.fullmatch(anc))
    return not (is_empty_stmt and is_empty_src and is_empty_anc)


def corpus_integrity(root, cfg, stats=None):
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

    🔴 **`B-3` (ruling 48): the number of files this function re-hashes ⛔ must appear in the
    stats line.**
    ⚠️ **Measured, twice, by two different people:** the v1.3.0 auditor could not find "which
    sensor compares `_manifest.json`", and on 2026-09-02 Project D's user wrote the same thing
    again. **⛔ It had been here the whole time.** ⇒ **A protection nobody can see looks exactly
    like no protection at all.**
    """
    stats = {} if stats is None else stats
    stats.setdefault("hash_compared", 0)
    out = []
    cdir = root / cfg["corpus_dir"]
    if not cdir.is_dir():
        return out
    mp = root / cfg["corpus_manifest"]
    extracts = sorted(cdir.glob("*.md"), key=lambda p: p.as_posix())
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
    if not isinstance(man, list):
        return [("INCOMPLETE", "CORPUS_MANIFEST_MALFORMED",
                 f"{mp.name} format error: expected a JSON array of extraction entries, got {type(man).__name__}")]
    for idx, e in enumerate(man):
        if not isinstance(e, dict):
            return [("INCOMPLETE", "CORPUS_MANIFEST_MALFORMED",
                     f"{mp.name} entry #{idx} is not a JSON object: {type(e).__name__}")]
    known = {e["md"]: e.get("md_sha256") for e in man if "md" in e}
    for f in sorted(cdir.glob("*.md"), key=lambda p: p.as_posix()):
        want = known.get(f.name)
        if want is None:
            out.append(("WARN", "CORPUS_FILE_UNTRACKED",
                        f"{f.name} is not in the manifest — re-run the extraction tool after adding sources"))
            continue
        stats["hash_compared"] += 1
        if hashlib.sha256(f.read_bytes()).hexdigest() != want:
            out.append(("FAIL", "CORPUS_MD_MODIFIED",
                        f"{f.name} content no longer matches the manifest — "
                        "**the comparison target has been altered; every anchor result this round is untrustworthy**"))
    for name in known:
        if not (cdir / name).exists():
            out.append(("FAIL", "CORPUS_FILE_DELETED", f"{name} has disappeared but is still listed in the manifest"))
    return out


YEAR_PAT = re.compile(r"\b(19\d\d|20\d\d)\b")


def resolve_source(src, corpus):
    """Resolve a citation string to an extraction filename in corpus.

    Returns:
        ("EMPTY", None)
        ("EXACT", filename)
        ("UNIQUE", filename)
        ("AMBIGUOUS", [matching_filenames])
        ("UNRESOLVED", None)
    """
    clean_src = src.strip().strip("`").strip()
    if not clean_src or PLACEHOLDER.match(clean_src) or "<<<" in clean_src:
        return "EMPTY", None

    # 1. Exact filename match (with or without .md extension)
    if clean_src in corpus:
        return "EXACT", clean_src
    if not clean_src.endswith(".md") and f"{clean_src}.md" in corpus:
        return "EXACT", f"{clean_src}.md"

    # 2. Extract author surname token and year
    m = SURNAME.match(clean_src)
    if not m:
        return "UNRESOLVED", None
    author_key = m.group(1).lower()

    year_m = YEAR_PAT.search(clean_src)
    year = year_m.group(1) if year_m else None

    # Match candidates against corpus keys
    matched = []
    for fname in sorted(corpus.keys()):
        fl = fname.lower()
        # Corpus filename convention is "Author - Year - Title.md"
        # Match only on author segment with token boundaries, forbidding unbounded substring match
        if " - " not in fname:
            continue
        file_author = fname.split(" - ")[0].strip().lower()
        author_match = (
            file_author == author_key or
            file_author.startswith(author_key + " ") or
            file_author.startswith(author_key + "_") or
            file_author.startswith(author_key + "-") or
            file_author.startswith(author_key + ",")
        )
        if not author_match:
            continue

        if year:
            if year in fl:
                matched.append(fname)
        else:
            matched.append(fname)

    if not matched:
        return "UNRESOLVED", None
    if len(matched) == 1:
        # 覆核 B-2：單一命中仍然是一次「推論」，不是台帳明說的。呼叫端會把
        # 用了哪一條規則印出來，讓這個推論可見，而不是靜默接受。
        return ("UNIQUE_AUTHOR_YEAR" if year else "UNIQUE_AUTHOR_ONLY"), matched[0]
    return "AMBIGUOUS", matched


RESOLUTION_RULE_TEXT = {
    "EXACT": "explicit filename",
    "UNIQUE_AUTHOR_YEAR": "unique match on author field + year (inferred)",
    "UNIQUE_AUTHOR_ONLY": "unique match on author field only, no year in source (inferred)",
}


def main():
    root, cfg, as_json, name = cli("claim_ledger")
    cstats = {}
    findings = corpus_integrity(root, cfg, cstats)
    led = root / cfg["claim_ledger"]
    if not led.exists():
        findings.append(("INCOMPLETE", "CLAIM_LEDGER_MISSING",
                         f"{cfg['claim_ledger']} not found — **not checked, and that is not a pass**"))
        return emit("Claim Ledger sensor", findings,
                    {"hashes compared file by file": cstats["hash_compared"]},
                    as_json, name)

    entries = parse(led.read_text(encoding="utf-8"))
    cdir = root / cfg["corpus_dir"]
    corpus = {p.name: norm(p.read_text(encoding="utf-8", errors="replace"))
              for p in cdir.glob("*.md")} if cdir.is_dir() else {}
    checked = matched = 0
    resolutions = []

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

        status, res = resolve_source(src, corpus)
        if status in ("EMPTY", "UNRESOLVED"):
            findings.append(("INCOMPLETE", "ANCHOR_SOURCE_UNRESOLVED",
                             f"{cid} cannot resolve source: 「{src}」 — **not checked is not a pass**"))
            continue
        if status == "AMBIGUOUS":
            findings.append(("INCOMPLETE", "ANCHOR_SOURCE_AMBIGUOUS",
                             f"{cid} source is ambiguous (matches multiple extractions: {res}) — specify explicit filename"))
            continue

        target_fname = res
        target_text = corpus[target_fname]
        checked += 1
        resolutions.append((cid, target_fname, RESOLUTION_RULE_TEXT[status]))
        if norm(anchor) in target_text:
            matched += 1
        else:
            findings.append(("FAIL", "ANCHOR_NOT_IN_SOURCE",
                             f"{cid} anchor not found in source {target_fname}：「{anchor[:56]}…」"))

    # D-20260921-X87 / CLAIM-EXIT-1: When valid claims exist but none reached anchor
    # verification (checked == 0), add an INCOMPLETE finding so emit yields exit 2
    # consistently in text and --json.
    # Preserve existing INCOMPLETE/FAIL priority: if a FAIL already exists, do not mask it.
    valid_entries = [cid for cid, f in entries.items() if is_valid_claim(f)]
    if valid_entries and checked == 0 and not any(l == "FAIL" for l, _, _ in findings):
        findings.append(("INCOMPLETE", "CLAIM_NONE_CHECKED",
                         f"All {len(valid_entries)} substantive claim(s) skipped anchor verification "
                         f"(empty template, missing corpus, or unresolved source) "
                         f"— **not checked is not a pass**"))

    code = emit("Claim Ledger sensor", findings,
                {"claims": len(entries), "extractions": len(corpus),
                 "hashes compared file by file": cstats["hash_compared"],
                 "anchors matched": (f"{matched}/{checked}"
                                     if checked
                                      else ("0/0 (no substantive claim was actually verified this run "
                                            "-- **not checked is not a pass**)"
                                            if valid_entries
                                            else "0/0 (no substantive claims require verification)"))}, as_json, name)
    if not as_json:
        # Review B-2: print what each claim resolved to and by which rule. An explicit
        # filename is what the ledger said; a unique author-field hit is this sensor's
        # inference, and the reader is entitled to see which one happened.
        for cid, fname, rule in resolutions:
            print(f"      -> {cid} resolved to {fname} ({rule})")
        if valid_entries and checked == 0:
            # Review B-1 / D-20260921-X87: when there are claims but none reached anchor verification,
            # say so on the summary. Exit code contract is INCOMPLETE (exit 2).
            print(f"      ⚠️ All {len(valid_entries)} substantive claim(s) skipped anchor verification "
                  f"(empty template, missing corpus, or unresolved source) "
                  f"-- **not checked is not a pass**")
        print("      ⚠️ This sensor only checks that the anchor exists,")
        print("      not whether the source supports the claim (links 6 and 7)")
    return code


if __name__ == "__main__":
    sys.exit(main())
