#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor: T0 uniqueness and write scope

## Checks

    T0_DUPLICATE_IN_SUBDIR          A subdirectory contains a file named like a T0 document   FAIL
    WRITE_TO_DENIED_PATH            Changes fall inside the deny scope                        FAIL
    WRITE_OUT_OF_SCOPE              Changes fall outside the declared scope                   FAIL
    DENIED_PATH_TOUCHED_UNATTRIBUTED Changes in solo project fall inside the deny scope       WARN
    TRACKED_HIDDEN_FLAGS_PRESENT    Tracked files carry assume-unchanged/skip-worktree flags  INCOMPLETE
    CONFIGURATION_CONFLICT          deny and excluded_dirs configuration conflict             INCOMPLETE
    IGNORED_DENIED_PATH_PRESENT     .gitignore-ignored files inside deny scope                INCOMPLETE
    IGNORED_OUT_OF_SCOPE_PRESENT    .gitignore-ignored files outside declared scopes          INCOMPLETE
    SCOPE_UNCHECKABLE               Git inspection failed or output truncated                 INCOMPLETE

⚠️ **Why T0 uniqueness is FAIL rather than WARN:**
**You change one and miss the others, and each one reads fine on its own.**
This is the hardest-to-notice form of the "fixed one layer, missed another" family.

⚠️ **Solo projects should leave `write_scopes` empty** — the sensor will say
"not applicable" explicitly, **rather than passing silently**.

## Five pits already fallen into (**written here because they will recur**)

1. `git rev-parse --show-toplevel` must equal the project root.
   Otherwise, when the project sits inside another repository, **it reports against the
   wrong repository, and does so with complete confidence.**
2. `git -c core.quotepath=false`. Otherwise non-ASCII paths print as octal escapes, and
   **the one column you actually need to read — which file changed — becomes a string of digits.**
3. Benchmark must anchor to the `reviewed` tag, traversing the historical touch set of
   each commit in `reviewed..HEAD` plus working tree changes. Never rely on working tree
   status or net diff alone (commits and reverts would otherwise lose their record).
   If `reviewed` is missing or not an ancestor, fail-closed as INCOMPLETE; never fallback to HEAD or fake PASS.
4. Path parsing must follow Git `-z` NUL format; rename/copy include both endpoints in the touch set;
   subdirectory projects narrow to their subtree prefix and correctly capture endpoints within scope.
5. When hidden flags (assume-unchanged/skip-worktree) or .gitignore files obscure changes,
   modification status cannot be proven; always fail-closed as INCOMPLETE, never pass silently.

Exit codes: 0 PASS | 1 FAIL | 2 INCOMPLETE
"""
import pathlib
import os
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from framework_config import excluded                      # noqa: E402


def _text(cp):
    """Return a child process's stdout, ⛔ guaranteed to be a string.

    🔴 **Measured case (2026-08-27, Traditional-Chinese Windows, Python 3.14.2,
    the principal's machine):** `_run_git(..., capture_output=True, text=True)`
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
    if isinstance(cp.stderr, bytes):
        return cp.stderr.decode("utf-8", "replace")
    return cp.stderr if isinstance(cp.stderr, str) else ""


def _run_git(*args, **kwargs):
    # git status may refresh the index even when used only to inspect changes.
    kwargs["env"] = dict(os.environ, **kwargs.get("env", {}))
    kwargs["env"]["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(*args, **kwargs)


def _nul_tokens(data):
    if not isinstance(data, bytes):
        raise ValueError("Git did not return a byte stream")
    if not data:
        return []
    if not data.endswith(b"\0"):
        raise ValueError("Unterminated Git NUL record")
    tokens = data[:-1].split(b"\0")
    if any(not t for t in tokens):
        raise ValueError("Empty Git NUL record")
    return tokens


def _git_path(token):
    path = token.decode("utf-8", "strict")
    if not path or path.startswith("/") or any(p in ("", ".", "..") for p in path.split("/")):
        raise ValueError("Invalid repository-relative Git path")
    return path


def _parse_history(data):
    tokens = _nul_tokens(data)
    paths = []
    i = 0
    while i < len(tokens):
        status = tokens[i].decode("ascii", "strict")
        i += 1
        if not re.fullmatch(r"(?:[ADMTUXB]|[RCM][0-9]{1,3})", status):
            raise ValueError("Unknown git diff-tree status")
        if len(status) > 1 and int(status[1:]) > 100:
            raise ValueError("Invalid Git similarity score")
        count = 2 if status[0] in "RC" else 1
        if len(tokens) - i < count:
            raise ValueError("Truncated git diff-tree record")
        paths.extend(_git_path(t) for t in tokens[i:i+count])
        i += count
    return paths


def _parse_status(data):
    tokens = _nul_tokens(data)
    paths = []
    i = 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if len(entry) < 4 or entry[2:3] != b" ":
            raise ValueError("Malformed git status record")
        code = entry[:2].decode("ascii", "strict")
        if code != "??" and (code == "  " or any(c not in " MADRCUT" for c in code)):
            raise ValueError("Unknown git status code")
        paths.append(_git_path(entry[3:]))
        if "R" in code or "C" in code:
            if i == len(tokens):
                raise ValueError("Missing git status rename/copy endpoint")
            paths.append(_git_path(tokens[i]))
            i += 1
    return paths


def _is_generated_metadata(path):
    """Narrow fixed metadata names; user ignore rules do not grant exemptions."""
    return (path in ("scripts/harness/harness_status.json", "git-checkpoint.log")
            or pathlib.PurePosixPath(path).name == ".DS_Store")


def git_hidden_flags(root):
    """Check whether tracked files within the project subtree carry assume-unchanged (h) or skip-worktree (S/s) hidden flags.

    Returns (flagged_list, error_message).
    flagged_list is [("path", "flag_type"), ...]
    """
    try:
        proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                         "ls-files", "-v", "-z", "--", "."],
                        capture_output=True, timeout=20)
        if proc.returncode != 0:
            return None, ("`git ls-files -v` execution failed "
                          f"(exit {proc.returncode}; stderr {(_text_err(proc) or 'empty')[:120]}) "
                          "— **⛔ not checked is not a pass**")
        tokens = _nul_tokens(proc.stdout)
        flagged = []
        for token in tokens:
            if not token:
                continue
            if len(token) < 3 or token[1:2] != b" ":
                raise ValueError("Malformed git ls-files record")
            tag = token[:1].decode("ascii", "strict")
            if tag not in "HSMRCK?hsmrck":
                raise ValueError("Unknown git ls-files flag")
            _git_path(token[2:])
            if tag in ("S", "s"):
                flagged.append((_git_path(token[2:]), "skip-worktree"))
            elif tag.islower():
                flagged.append((_git_path(token[2:]), "assume-unchanged"))
        return flagged, None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return None, f"git flag inspection could not run: {e}"


def git_ignored(root):
    """Get list of all untracked files within the project subtree ignored by .gitignore.

    Returns (ignored_paths_list, error_message).
    """
    try:
        proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                         "ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--", "."],
                        capture_output=True, timeout=20)
        if proc.returncode != 0:
            return None, ("`git ls-files --ignored` execution failed "
                          f"(exit {proc.returncode}; stderr {(_text_err(proc) or 'empty')[:120]}) "
                          "— **⛔ not checked is not a pass**")
        tokens = _nul_tokens(proc.stdout)
        paths = [_git_path(t) for t in tokens if t]
        return paths, None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return None, f"git ignored files inspection could not run: {e}"


def git_changed(root):
    """Union of touched paths from reviewed benchmark through HEAD plus working tree.

    Returns (paths_list, error_message).
    If verification fails or cannot be determined, paths_list is None, and error_message gives the diagnosis.
    """
    try:
        top = _run_git(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
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
        # 🔴 **When the project is a subdirectory of a repo, narrow to this project's subtree (v1.4.1).**
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

        # 1. Verify reviewed tag exists (V145-E2)
        rev_tag = _run_git(["git", "-C", str(root), "rev-parse", "--verify", "reviewed^{commit}"],
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=20)
        if rev_tag.returncode != 0:
            return None, ("reviewed benchmark does not exist (no reviewed tag) "
                          "— **⛔ not checked is not a pass**")

        # 2. Verify reviewed tag is an ancestor of HEAD (V145-E2)
        anc = _run_git(["git", "-C", str(root), "merge-base", "--is-ancestor", "reviewed", "HEAD"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20)
        if anc.returncode != 0:
            return None, ("reviewed benchmark is not an ancestor of HEAD (diverged history or unreviewed) "
                          "— **⛔ not checked is not a pass**")

        candidate_paths = []

        # 3. Touch set across commits in reviewed..HEAD (historical union, not net diff; includes merge commits)
        rev_list = _run_git(["git", "-C", str(root), "rev-list", "reviewed..HEAD"],
                                  capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=30)
        if rev_list.returncode != 0:
            return None, ("git rev-list failed "
                          f"(exit {rev_list.returncode}; stderr {(_text_err(rev_list) or 'empty')[:120]}) "
                          "— **⛔ not checked is not a pass**")
        if not isinstance(rev_list.stdout, str):
            return None, "Unreadable git rev-list output"
        commits = [c.strip() for c in _text(rev_list).splitlines() if c.strip()]
        if commits:
            diff_tree = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                                        "diff-tree", "--stdin", "-r", "-z", "-m", "-M", "-C",
                                        "--no-commit-id", "--name-status"],
                                       input=("\n".join(commits) + "\n").encode("utf-8"),
                                       capture_output=True, timeout=30)
            if diff_tree.returncode != 0:
                return None, ("git diff-tree failed "
                              f"(exit {diff_tree.returncode}; stderr {(_text_err(diff_tree) or 'empty')[:120]}) "
                              "— **⛔ not checked is not a pass**")
            candidate_paths.extend(_parse_history(diff_tree.stdout))

        # 4. Touch set in working tree (staged, unstaged, untracked)
        status_proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                                      "status", "--porcelain", "-z", "-uall"],
                                     capture_output=True, timeout=20)
        if status_proc.returncode != 0:
            return None, ("`git status` produced no readable output "
                          f"(exit {status_proc.returncode}; stderr {(_text_err(status_proc) or 'empty')[:120]}) "
                          "— **⛔ not checked is not a pass**")
        candidate_paths.extend(_parse_status(status_proc.stdout))

        # 5. Narrow to subtree prefix
        project_paths = set()
        if prefix:
            prefix_slash = prefix + "/"
            for p in candidate_paths:
                p_norm = p
                if p_norm.startswith(prefix_slash):
                    rel = p_norm[len(prefix_slash):]
                    if rel and rel != ".":
                        project_paths.add(rel)
        else:
            for p in candidate_paths:
                p_norm = p
                if p_norm and p_norm != ".":
                    project_paths.add(p_norm)

        return sorted(project_paths), None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return None, f"git execution failed: {e}"

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

    def under(path, tops):
        return any(path == a or path.startswith(a + "/") for a in tops)

    changed, err = git_changed(root)
    if changed is None:
        findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                         f"{err} — **not checked, and that is not a pass**"))
    else:
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

        # ③ Hidden flags check (V145-E2b: assume-unchanged and skip-worktree)
        flagged, ferr = git_hidden_flags(root)
        if ferr:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{ferr} — **not checked, and that is not a pass**"))
        elif flagged:
            flag_details = [f"{p} ({t})" for p, t in flagged]
            findings.append(("INCOMPLETE", "TRACKED_HIDDEN_FLAGS_PRESENT",
                             f"found {len(flagged)} tracked file(s) with hidden flags (assume-unchanged or skip-worktree): "
                             + ", ".join(flag_details[:8])
                             + ("…" if len(flag_details) > 8 else "")
                             + " — **⛔ hidden flags obscure working-tree changes; review cannot verify modification status, refusing evaluation**"))

        # ④ Configuration conflicts and ignored files check (V145-E2b: .gitignore and excluded_dirs)
        # 4.1 Configuration conflict: deny scope overlaps with excluded_dirs list
        cfg_excluded = set(cfg.get("excluded_dirs", []))
        conflicts = [d for d in denied if (set(pathlib.PurePosixPath(d).parts) & cfg_excluded)] + \
                    [e for e in cfg_excluded if under(e, denied)]
        conflicts = sorted(set(conflicts))
        if conflicts:
            findings.append(("INCOMPLETE", "CONFIGURATION_CONFLICT",
                             f"deny scope path overlaps with excluded_dirs list ({', '.join(conflicts)}) — "
                             "**⛔ deny scope must not be silently swallowed by excluded directories, please fix framework_config.py**"))

        # 4.2 Ignored files check
        ignored_files, ierr = git_ignored(root)
        if ierr:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{ierr} — **not checked, and that is not a pass**"))
        elif ignored_files:
            denied_ignored = []
            out_of_scope_ignored = []
            generated_metadata = []
            allowed = [a.rstrip("/") for v in scopes.values() for a in v] if scopes else []
            for ig in ignored_files:
                # An exact deny entry remains an explicit user instruction.
                # Folder-level deny protects research, not generated OS/report metadata.
                if _is_generated_metadata(ig) and ig not in denied:
                    generated_metadata.append(ig)
                    continue
                ig_path = root / ig
                is_denied = under(ig, denied)
                is_excl = excluded(ig_path, root, cfg)

                # Explicit deny must not be swallowed by exclusion rules
                if is_denied:
                    if is_excl and not conflicts:
                        findings.append(("INCOMPLETE", "CONFIGURATION_CONFLICT",
                                         f"file `{ig}` falls inside both deny scope and excluded_dirs list — "
                                         "**⛔ deny scope must not be silently swallowed by excluded directories, please fix framework_config.py**"))
                    else:
                        denied_ignored.append(ig)
                elif is_excl:
                    # Framework caches and exclusions (non-deny) pass quietly
                    continue
                else:
                    # Regular ignored files outside excluded directories:
                    if scopes:
                        # Multi-agent mode: must be within declared scope
                        if not under(ig, allowed):
                            out_of_scope_ignored.append(ig)
                    else:
                        # Solo mode: regular research attachments pass quietly
                        pass

            stats["ignored generated metadata excluded"] = len(generated_metadata)

            if denied_ignored:
                findings.append(("INCOMPLETE", "IGNORED_DENIED_PATH_PRESENT",
                                 f"found {len(denied_ignored)} .gitignore-ignored file(s) inside deny scope: "
                                 + ", ".join(denied_ignored[:8])
                                 + ("…" if len(denied_ignored) > 8 else "")
                                 + " — **⛔ ignored files inside deny scope cannot be proven to be from this round, review cannot pass**"))

            if out_of_scope_ignored:
                findings.append(("INCOMPLETE", "IGNORED_OUT_OF_SCOPE_PRESENT",
                                 f"found {len(out_of_scope_ignored)} .gitignore-ignored file(s) outside all declared agent scopes: "
                                 + ", ".join(out_of_scope_ignored[:8])
                                 + ("…" if len(out_of_scope_ignored) > 8 else "")
                                 + " — **⛔ ignored files outside declared scopes cannot be proven to be from this round, review cannot pass**"))

    if any(f[1] in ("IGNORED_DENIED_PATH_PRESENT", "IGNORED_OUT_OF_SCOPE_PRESENT") for f in findings):
        findings = [(level, code, message + ' Ask your AI to explain these paths: after your approval, track the protected research files locally (no upload), or move intentionally untracked material outside protected scope and update its references. Do not delete research data or advance reviewed merely to silence this finding.' if code in ("IGNORED_DENIED_PATH_PRESENT", "IGNORED_OUT_OF_SCOPE_PRESENT") else message) for level, code, message in findings]

    return emit("Scope and T0 sensor", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
