#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: does `my/MY_RULES.md` cover every framework rule?

## Why this sensor exists

**The framework's rules live in `governance/RULES.md`, ⛔ and that folder is replaced
wholesale on upgrade.**
🔴 **Before v1.4.0, a project that accumulated its own rules in `RULES.md` lost them at
the next upgrade — ⚠️ while `profiles/PROFILE_solo.md` was actively encouraging exactly that.**

→ **From v1.4.1 a project's rules live in `my/MY_RULES.md` (never replaced by an upgrade),
and the framework's rules exist there as a verbatim copy in §1.**

## ⚠️ This design deliberately creates two copies

🔴 **"One fact, two copies, and only one of them gets updated" is failure axis two itself.**
**⛔ So the copy cannot be left unwatched — this sensor is the watcher.**

⚠️ **Precedent: `R-24` (a prompt must be self-contained) also forced copies to exist,
and the framework's answer then was ⛔ not to ban copies but to add `sensor_clause_sync.py`.**
**This is the same move, widened from one single-line word list to the whole rule set.**

## Three checks

    RULE_MISSING_IN_MY        in the framework, ⛔ not in `MY_RULES.md`          FAIL
    RULE_TEXT_DRIFT           in both, text differs, no override marker          FAIL
    OVERRIDE_WITHOUT_REASON   marked as an override, ⛔ no reason on that line   FAIL

⚠️ **⛔ The comparison is keyed on the rule number, ⛔ not a whole-file diff.**
**Why: fix one typo in the framework and a whole-file diff fires, while the prescribed
action is "paste the framework's text in" — ⛔ without a key, pasting produces two copies
of the same rule inside `MY_RULES.md`.**

## ⛔ What this sensor does not claim

⛔ **It does ⛔ not judge the quality of a `P-xx`.** ⚠️ A rule that cannot be turned into a
concrete action looks fine to it.
⛔ **It does ⛔ not judge whether an override's reason is sound** — only that the line has text.
**⚠️ The criterion is structural on purpose: ⛔ a "one sentence that reads plausibly" criterion
is how a sensor goes permanently silent on a real defect (see the proposal-exemption comment
in `framework_config.py`).**

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402

ITEM = re.compile(r"^\*\*((?:R|P)-\d\d)\*\*")


def parse(text):
    """Split into rule bodies, bounded by lines starting `**R-xx**` or `**P-xx**`.

    ⚠️ **An item ends at the next item, a `## ` heading, or a `---` rule.**
    ⛔ Blank lines cannot be the boundary — the body of `R-34` contains blank lines.
    """
    items, cur, buf = {}, None, []
    for line in text.split("\n"):
        m = ITEM.match(line)
        if m:
            if cur:
                items[cur] = "\n".join(buf).rstrip()
            cur, buf = m.group(1), [line]
        elif cur is not None:
            # ⚠️ `<!--` is a boundary too: §1 of `MY_RULES.md` ends with an insertion-point
            #    comment. ⛔ Without this, that line joins the last rule's body and the
            #    sensor reports `RULE_TEXT_DRIFT`.
            #    🔴 **This was the first finding this sensor produced, and it was about itself.**
            if (line.startswith("## ") or line.strip() == "---"
                    or line.lstrip().startswith("<!--")):
                items[cur] = "\n".join(buf).rstrip()
                cur, buf = None, []
            else:
                buf.append(line)
    if cur:
        items[cur] = "\n".join(buf).rstrip()
    return items



def is_override(body_text, marker):
    """Return `(marker present, reason long enough)`. 🔴 **The single home of this criterion.**

    ⚠️ **The marker must be on a line of its own (`i > 0`), ⛔ never on the clause line.**
    🔴 **Measured (this sensor's own paired sample):** when the same line was allowed,
    "`**R-19** [project override] <the original clause>`" passed — **because there really
    was text after the marker, and that text was the clause itself, not a reason.
    ⛔ The criterion was therefore inert.**

    ⛔ **`tool_sync_my_rules.py` reads this same function** —
    ⚠️ **if the two criteria ever differ you get "the sensor calls it an override while the
    tool lists it as outstanding".**
    ⚠️ **(During v1.4.3's development that tool had an `--adopt` [withdrawn] that rewrote
    drifted rules for you; ⛔ the whole write path was ruled back out in v1.4.4. ⇒ Neither
    side writes anything now, ⛔ and the reason for sharing one criterion is unchanged.)**
    """
    body = body_text.split("\n")
    line = next((l for i, l in enumerate(body) if marker in l and i > 0), None)
    if line is None:
        return False, False
    return True, len(line.split(marker, 1)[1].strip()) >= 6

def main():
    root, cfg, as_json, name = cli("my_rules")
    findings, stats = [], {}

    fw_p = root / cfg.get("framework_rules", "governance/RULES.md")
    my_p = root / cfg.get("my_rules", "my/MY_RULES.md")
    marker = cfg.get("override_marker", "[project override]")

    if not fw_p.is_file():
        findings.append(("INCOMPLETE", "FRAMEWORK_RULES_MISSING",
                         f"{fw_p.name} does not exist — "
                         "**this check did not run. ⛔ Not run ≠ passed**"))
        return emit("My-rules sensor", findings, stats, as_json, name)
    if not my_p.is_file():
        findings.append(("INCOMPLETE", "MY_RULES_MISSING",
                         f"{cfg.get('my_rules', 'my/MY_RULES.md')} does not exist — "
                         "**there is no copy of the framework rules to compare against. "
                         "⛔ Not checked ≠ passed**"))
        return emit("My-rules sensor", findings, stats, as_json, name)

    fw = parse(fw_p.read_text(encoding="utf-8"))
    my = parse(my_p.read_text(encoding="utf-8"))

    fw_ids = {k for k in fw if k.startswith("R-")}
    my_r = {k for k in my if k.startswith("R-")}
    my_p_ids = {k for k in my if k.startswith("P-")}

    overrides = []
    for rid in sorted(fw_ids):
        if rid not in my:
            findings.append(("FAIL", "RULE_MISSING_IN_MY",
                             f"{rid} is in the framework and ⛔ not in {my_p.name} — "
                             "**run `python scripts/harness/tool_sync_my_rules.py` to copy "
                             "the text in verbatim. ⛔ Do not retype it from memory**"))
            continue
        if my[rid] == fw[rid]:
            continue
        # ⚠️ **The override marker must be on a line of its own, ⛔ not on the rule's own line.**
        #    🔴 **Measured (this sensor's paired sample):** allowing it on the same line lets
        #    "`**R-19** [project override] <the original clause>`" pass — **because there IS
        #    text after the marker, and that text is the clause itself, not a reason.
        #    ⛔ The criterion would be decorative.**
        marked, has_reason = is_override(my[rid], marker)
        if not marked:
            findings.append(("FAIL", "RULE_TEXT_DRIFT",
                             f"{rid} differs between the two and carries no {marker} — "
                             "**the framework's text is the definition. ⛔ To change it, "
                             "add a `P-xx` that tightens it**"))
            continue
        if not has_reason:
            findings.append(("FAIL", "OVERRIDE_WITHOUT_REASON",
                             f"{rid} is marked {marker} with ⛔ no reason on that line — "
                             "**an exemption is allowed, ⛔ but it has to be visible**"))
            continue
        overrides.append(rid)

    for rid in sorted(my_r - fw_ids):
        findings.append(("WARN", "RULE_NOT_IN_FRAMEWORK",
                         f"{rid} is in {my_p.name} and not in the framework — "
                         "**⚠️ if this is a rule of your own, ⛔ number it `P-xx`: "
                         "the next framework version may use that same `R-xx`**"))

    stats["framework rules"] = len(fw_ids)
    stats["covered here"] = f"{len(fw_ids & my_r)} / {len(fw_ids)}"
    stats["project rules"] = f"{len(my_p_ids)} (`P-xx`)"
    stats["overrides"] = (f"{len(overrides)}: {', '.join(overrides)}"
                          if overrides else "0")
    return emit("My-rules sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
