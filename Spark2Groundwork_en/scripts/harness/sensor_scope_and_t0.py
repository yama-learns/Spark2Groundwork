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


def _text(cp):
    """Return a child process's stdout, ⛔ guaranteed to be a string.

    🔴 **Measured case (2026-08-27, Traditional-Chinese Windows, Python 3.14.2,
    the principal's machine):** `subprocess.run(..., capture_output=True, text=True)`
    returned `returncode == 0` **with `stdout` set to `None`.**

    ## The cause (**established by running one diagnostic, ⛔ not guessed**)

    ```
    UnicodeDecodeError: 'cp950' codec can't decode byte 0x94 in position 16
      File ".../subprocess.py", line 1613, in _readerthread
        buffer.append(fh.read())
    ```

    **With `text=True` and ⛔ no `encoding`, Python decodes the child's output using the
    locale encoding. On Traditional-Chinese Windows that is `cp950`, and git prints paths
    in UTF-8 — the third byte of `輔` is `0x94`, which cp950 cannot decode.**

    🔴 **The worst part is not that it fails; it is how it fails:**
    **the decode happens inside `subprocess`'s reader thread. ⚠️ That thread dies, the
    exception ⛔ never reaches the main thread, and `communicate()` returns `None` — so the
    caller sees "exit 0 and no output".**
    **⛔ "Succeeded but produced nothing" and "succeeded and genuinely had nothing" look identical.**

    ## ⚠️ The same fix, applied to only half the code

    **`run()` in `checkpoint.py` and `review_changes.py` says
    `encoding="utf-8", errors="replace"` verbatim — ⛔ and this file did not.**
    🔴 **The fix already existed in two programs in the same folder; it was simply never
    carried to the third.**

    ⚠️ **It is also the `R-34` shape: `_common._force_utf8()` fixes *our own output*,
    ⛔ and it was treated as "encoding has been dealt with". ⛔ A true fix whose scope
    does not cover this channel.**

    ## What this function is for

    **Even with `encoding` specified, ⛔ this defence stays:**
    **whenever `stdout` is not a string it must become a readable INCOMPLETE —
    ⛔ never a crash, ⛔ never a pass.**

    ⚠️ **The defect has been here since v1.0.0 and surfaced for the first time in v1.4.1** —
    🔴 **because the old code skipped the whole block when `write_scopes` was empty, and a
    solo project always leaves it empty. ⛔ That code had never once run on a real user's machine.**
    **⇒ D2 ⛔ did not cause this crash; it is what made it visible.**
    """
    return cp.stdout if isinstance(cp.stdout, str) else ""


def _text_err(cp):
    return cp.stderr if isinstance(cp.stderr, str) else ""


def git_changed(root):
    """This round's change list. Returns (list, error message)."""
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20)
        if top.returncode != 0:
            return None, "version control not initialised"
        out = _text(top).strip()
        if not out:
            # ⛔ "git said it succeeded and handed me nothing" must ⛔ not fall through.
            #    ⚠️ Falling through turns `pathlib.Path("")` into the current directory,
            #    **so it would report "the project sits inside another repository" — a
            #    diagnosis that reads plausibly and is wrong.**
            return None, ("git reported success (exit 0) ⛔ and produced no output "
                          "— **⛔ this is not a pass, it is could-not-check.** "
                          f"(stdout type {type(top.stdout).__name__}; "
                          f"stderr {(_text_err(top) or 'empty')[:120]})")
        # 🔴 **When the project is a subdirectory of a repo, ⛔ stop refusing to report (v1.4.1).**
        #
        # ⚠️ **The old code always returned "sits inside another repository" and went INCOMPLETE.**
        #    **⛔ The concern was right (⛔ never judge the wrong repo), ⛔ the remedy was too blunt:**
        #    🔴 **this framework's own repository has exactly that shape (each edition is a
        #    subdirectory), and so does a user who drops the project into an existing notes repo.**
        #    **⇒ That is a light that is always on, and a permanent red light teaches people
        #    to ignore the whole harness (`R-19`).**
        #
        # ✅ **The right move: narrow the report to this project's subtree, ⛔ not refuse it.**
        #    `git status --porcelain` prints paths relative to the **repository root**,
        #    ⛔ not to the directory named by `-C` — **so strip the prefix; ⛔ do not assume.**
        top_path, root_r = pathlib.Path(out).resolve(), root.resolve()
        prefix = ""
        if top_path != root_r:
            try:
                prefix = root_r.relative_to(top_path).as_posix()
            except ValueError:
                # ⛔ The repo root git named does not contain this project — that IS
                #    the case where refusing to report is correct.
                return None, ("the repository root git reported ⛔ does not contain this "
                              "project — **refusing to report, to avoid judging the wrong repo**")
        r = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false",
                            "status", "--porcelain", "--", "."],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20)
        if r.returncode != 0 or not isinstance(r.stdout, str):
            return None, ("`git status` produced no readable output "
                          f"(exit {r.returncode}; stdout type {type(r.stdout).__name__})"
                          " — **⛔ not checked is not a pass**")
        paths = [ln[3:].strip().strip('"') for ln in r.stdout.splitlines() if ln.strip()]
        if prefix:
            # ⛔ **Drop anything outside the subtree.** ⚠️ `-- .` already narrowed it once;
            #    **this is the second pass** — ⛔ because "I assume it was narrowed" and
            #    "it was narrowed" are two different things.
            paths = [p[len(prefix) + 1:] for p in paths if p.startswith(prefix + "/")]
        return paths, None
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
    #
    # 🔴 **From v1.4.1 this check ⛔ no longer depends on whether `write_scopes` is set.**
    # ⚠️ **Old behaviour: an empty `write_scopes` skipped the whole block, ⛔ `deny` included.**
    #    **And `profiles/PROFILE_solo.md` §6 tells a solo project to leave it empty —
    #    🔴 so `deny` was inert in every solo project, and solo is the default situation.**
    #    ⛔ **Consequence: constitution §6.3's "clear `deny` and you have full authorisation"
    #    made no difference either way in a solo project** — **the sentence described a
    #    mechanism that was not running.**
    scopes = cfg.get("write_scopes") or {}
    stats = {"T0 documents": len(cfg["t0_docs"])}

    # 🔴 **`deny` is `deny`. ⛔ Nothing is appended to it here (v1.4.1).**
    # ⚠️ **The old code folded in `t0_docs` unconditionally, so no configuration could turn
    #    T0 protection off — while the comment in `framework_config.py` said the opposite:
    #    "the two T0 files are deliberately absent here; a governance agent may maintain them".**
    #    🔴 **Two comments by the same author with opposite intent: the absence of T0 from
    #    `deny` is a gap, and a gap carries no intent, so each side gave it its own meaning.**
    # ✅ **T0 is now listed verbatim in the `deny` default. ⚠️ That is ⛔ not "one rule written
    #    twice" — `t0_docs` says "exactly one copy exists project-wide"; `deny` says "who may
    #    write". ⛔ Two different facts about the same files.**
    denied = [d.rstrip("/") for d in cfg.get("deny", [])]

    changed, err = git_changed(root)
    if changed is None:
        findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                         f"{err} — **not checked, and that is not a pass**"))
    else:
        def under(path, tops):
            return any(path == a or path.startswith(a + "/") for a in tops)

        stats["changes this round"] = len(changed)
        stats["deny scope"] = len(denied)
        hits = [c for c in changed if under(c, denied)]

        if scopes:
            allowed = [a.rstrip("/") for v in scopes.values() for a in v]
            # ⚠️ `_human` is not a role, it is an exception. **⛔ The exempted count must be
            #    printed.** ⚠️ **It is removed in the v1.6.0 permission table, replaced by
            #    "attribution unavailable" rather than a silent exemption.**
            human = [h.rstrip("/") for h in scopes.get("_human", [])]
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
            if exempted:
                stats["⚠️ deny hits exempted via _human"] = (
                    f"{exempted} — **the exemption happened; it was judged to be a human's**")
        else:
            # 🔴 **Solo project: no roles declared, and `git status` cannot tell a human's
            #    edit from an AI's.**
            # ⛔ **⛔ Not a FAIL**: the principal editing their own ledger is entirely normal,
            #    **and a criterion that fires on correct behaviour teaches people to switch
            #    the whole harness off (`R-19`).**
            # ⛔ **And ⛔ not silence either**: that is the "silent filtering" family (`R-22`).
            # → **List them and let a person claim them.**
            stats["write scope"] = ("write_scopes not set (solo): ⛔ no out-of-scope verdict "
                                    "this round; changes inside the deny scope are listed")
            if hits:
                findings.append(("WARN", "DENIED_PATH_TOUCHED_UNATTRIBUTED",
                                 f"{len(hits)} change(s) this round fall inside the AI's "
                                 "default no-write area: "
                                 + ", ".join(hits[:8])
                                 + ("…" if len(hits) > 8 else "")
                                 + " — **⚠️ if you made them yourself this is normal; "
                                   "if not, read this list**"))

    return emit("Scope and T0 sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
