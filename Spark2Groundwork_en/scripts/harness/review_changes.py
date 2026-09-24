#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看變更 —— **AI 上次之後動了什麼，逐項攤開**

## 這支在做什麼

比較**你上次按下人工檢查點的那一刻**（`reviewed` 標籤）與現在，分四節列出：

    [1] 哪些檔案被動了，各動了幾行
    [2] 還沒納入版本控制的新檔案
    [3] 這段期間建立了哪些檢查點（`auto:` 開頭的是 AI 自己存的）
    [4] （可選）指定某個檔案，逐行看它改了什麼

## ⛔ 這支**只讀不寫**

⚠️ **刻意不做的事：** ⛔ 不 commit、⛔ 不 checkout、⛔ 不 reset、⛔ 不清鎖檔。
**理由：這是你用來「看」的工具，而一個會順手改東西的檢視工具，
會讓「我看到的」與「我按下去之前的狀態」不是同一個東西。**

## ⚠️ 一個沒有 HEAD 的倉庫是正常狀態，不是錯誤

剛 `git init` 而還沒有任何提交時，`git diff HEAD` 會以 fatal 中止。
**That is not corruption, but a human-reviewed comparison is incomplete.** Show the next step.

Exit codes: 0 valid human baseline and completed comparison | 1 wrong project location | 2 missing baseline or incomplete query
"""
import argparse
import os
import pathlib
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title": "  WHAT CHANGED since your last \"I have looked at this\"",
 "usage": """Usage:
  python3 scripts/harness/review_changes.py            overview
  python3 scripts/harness/review_changes.py <path>     then line-by-line for one file

⛔ Read-only: no commit, no checkout, no reset, no clearing of lock files.""",
 "wrong_folder": """[FAIL] This is not the project root.
       Missing: {missing}
       Current location: {root}""",
 "no_git": """[INCOMPLETE] Git could not run; this is not a reliable comparison.
       Open docs/START_HERE.html and use its graphical installation guidance, then review again.""",
 "no_repo": """[INCOMPLETE] This folder has no Git history or human-reviewed baseline.
       Read the starting contents first, then personally press Snapshot after confirming them. An AI must not press it for you.""",
 "wrong_repo": "[FAIL] This folder sits inside another git repository.",
 "no_head": """[INCOMPLETE] There is no first checkpoint yet, so changes since human review cannot be compared.
       Read the starting contents first, then personally press Snapshot after confirming them. An AI must not press it for you.""",
 "no_reviewed": """[INCOMPLETE] The human-reviewed baseline tag is missing. Save Progress does not mean you read the work.
       Inventory and read the current contents yourself; only then personally press Snapshot. No unread-change conclusion is available yet.""",
 "invalid_reviewed": """[INCOMPLETE] The reviewed tag is not a valid commit baseline in the current HEAD history.
       Preserve the files and tag. Ask an AI with local execution access to investigate; decide on a new baseline only after your own review.""",
 "git_error": """[INCOMPLETE] A Git query did not finish; this is not a reliable comparison.
       Preserve the files and ask an AI with local execution access to investigate, then retry. Do not treat blank output as reviewed.""",
 "base_is": "Comparing against: {base}",
 "s1": "[1] Files touched, and how many lines",
 "s1_empty": "(blank means: no tracked file differs from {base})",
 "s2": "[2] New files not yet under version control",
 "s2_empty": "(blank means: no new files)",
 "s3": "[3] Checkpoints made in this period (⚠️ lines starting `auto:` are the AI's own, ⛔ not reviewed by you)",
 "s3_empty": "(blank means: no new checkpoints since you last reviewed)",
 "s4": "[4] Line-by-line diff: {f}",
 "s4_empty": "(blank means: {f} is unchanged since {base})",
 "f_untracked": """This file is not tracked by git yet, **so there is nothing to compare it against.**
It appears in section [2] above. It will be tracked after one snapshot.""",
 "f_ignored": """This file is deliberately EXCLUDED from version control by `.gitignore`.
For what those directories are, see constitution section 6.2.
⛔ Nothing is recorded about it, so no comparison is possible.""",
 "footer": "When you are done: if you accept these changes, press snapshot once — that tells the framework \"I have looked at this\".",
}


SENTINELS = ("governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md")


def run(args, cwd):
    try:
        p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30,
                           env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.TimeoutExpired):
        return -1, "", "Git did not finish"
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def section(title, body, empty_note):
    print(title)
    print("-" * 46)
    if body.strip():
        print(body.rstrip())
    print("-" * 46)
    if not body.strip():
        print(empty_note)
    print()


def main(MSG):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("file", nargs="?", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(MSG["usage"]); return 0

    root = pathlib.Path(a.root).resolve() if a.root else pathlib.Path(__file__).resolve().parents[2]
    print("=" * 46); print(MSG["title"]); print("=" * 46); print()

    missing = [s for s in SENTINELS if not (root / s).is_file()]
    if missing:
        print(MSG["wrong_folder"].format(missing=", ".join(missing), root=root)); return 1

    rc, version, _ = run(["git", "--version"], root)
    if rc != 0 or not version.startswith("git version "):
        print(MSG["no_git"]); return 2
    rc, inside, _ = run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if rc != 0 or inside.strip() != "true":
        print(MSG["no_repo"]); return 2
    rc, prefix, _ = run(["git", "rev-parse", "--show-prefix"], root)
    if rc != 0:
        print(MSG["git_error"]); return 2
    if prefix.strip():
        print(MSG["wrong_repo"]); return 1

    rc, head, _ = run(["git", "rev-parse", "--verify", "--quiet", "HEAD^{commit}"], root)
    if rc != 0:
        print(MSG["no_head"]); return 2
    head = head.strip()
    rc, base, _ = run(["git", "rev-parse", "--verify", "--quiet",
                       "refs/tags/reviewed^{commit}"], root)
    if rc != 0:
        tag_rc, _, _ = run(["git", "show-ref", "--verify", "--quiet",
                            "refs/tags/reviewed"], root)
        if tag_rc == 1:
            print(MSG["no_reviewed"]); return 2
        if tag_rc == 0:
            print(MSG["invalid_reviewed"]); return 2
        print(MSG["git_error"]); return 2
    base = base.strip()
    rc, _, _ = run(["git", "merge-base", "--is-ancestor", base, head], root)
    if rc == 1:
        print(MSG["invalid_reviewed"]); return 2
    if rc != 0:
        print(MSG["git_error"]); return 2

    G = ["git", "-c", "core.quotepath=false", "--no-pager"]
    rc, stat, _ = run(G + ["diff", "--stat", base], root)
    if rc != 0:
        print(MSG["git_error"]); return 2
    rc, others, _ = run(G + ["ls-files", "--others", "--exclude-standard"], root)
    if rc != 0:
        print(MSG["git_error"]); return 2
    rc, log, _ = run(G + ["log", "--oneline", base + ".." + head], root)
    if rc != 0:
        print(MSG["git_error"]); return 2

    file_kind = None
    file_diff = ""
    if a.file:
        rc, _, _ = run(G + ["check-ignore", "-q", "--", a.file], root)
        if rc == 0:
            file_kind = "ignored"
        elif rc != 1:
            print(MSG["git_error"]); return 2
        else:
            rc, tracked, _ = run(G + ["ls-files", "--", a.file], root)
            if rc != 0:
                print(MSG["git_error"]); return 2
            if not tracked.strip():
                file_kind = "untracked"
            else:
                rc, file_diff, _ = run(G + ["diff", base, "--", a.file], root)
                if rc != 0:
                    print(MSG["git_error"]); return 2
                file_kind = "tracked"

    # A concurrent tag/HEAD change invalidates the comparison just collected.
    rc_h, final_head, _ = run(["git", "rev-parse", "--verify", "--quiet", "HEAD^{commit}"], root)
    rc_b, final_base, _ = run(["git", "rev-parse", "--verify", "--quiet",
                               "refs/tags/reviewed^{commit}"], root)
    if rc_h != 0 or rc_b != 0 or final_head.strip() != head or final_base.strip() != base:
        print(MSG["git_error"]); return 2

    print(MSG["base_is"].format(base="reviewed")); print()
    section(MSG["s1"], stat, MSG["s1_empty"].format(base="reviewed"))
    section(MSG["s2"], others, MSG["s2_empty"])
    section(MSG["s3"], log, MSG["s3_empty"])
    if a.file:
        print(MSG["s4"].format(f=a.file))
        print("-" * 46)
        if file_kind == "ignored":
            print(MSG["f_ignored"])
        elif file_kind == "untracked":
            print(MSG["f_untracked"])
        elif file_diff.strip():
            print(file_diff.rstrip())
        else:
            print(MSG["s4_empty"].format(f=a.file, base="reviewed"))
        print("-" * 46); print()

    print(MSG["footer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(MSG))
