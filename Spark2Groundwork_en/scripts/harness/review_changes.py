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
**那不是壞掉，是還沒有東西可以比。** ⛔ 不得把它當成錯誤丟給使用者。

退出碼：0 正常（**包含「沒有變更」**）｜1 前置條件不成立｜2 我沒能查
"""
import argparse
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
 "no_git": """[FAIL] git was not found.
       -> Windows: https://git-scm.com/download/win
       -> macOS: run `xcode-select --install`, or `brew install git`""",
 "no_repo": """[FAIL] This folder is not under version control yet.
       -> Press the snapshot button once; it will set that up.""",
 "wrong_repo": "[FAIL] This folder sits inside another git repository.",
 "no_head": """No checkpoints yet — **there is nothing to compare against.**
⚠️ This is a normal state, ⛔ not an error. Press snapshot once to make the first one.""",
 "base_is": "Comparing against: {base}",
 "base_none": "HEAD (⚠️ no reviewed tag yet — you have not made a human checkpoint)",
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
    p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
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

    root = pathlib.Path(a.root).resolve() if a.root else \
        pathlib.Path(__file__).resolve().parents[2]

    print("=" * 46); print(MSG["title"]); print("=" * 46); print()

    missing = [s for s in SENTINELS if not (root / s).is_file()]
    if missing:
        print(MSG["wrong_folder"].format(missing=", ".join(missing), root=root)); return 1
    try:
        subprocess.run(["git", "--version"], cwd=str(root), capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print(MSG["no_git"]); return 1

    rc, _, _ = run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if rc != 0:
        print(MSG["no_repo"]); return 1
    rc, prefix, _ = run(["git", "rev-parse", "--show-prefix"], root)
    if prefix.strip():
        print(MSG["wrong_repo"]); return 1

    rc, _, _ = run(["git", "rev-parse", "--verify", "HEAD"], root)
    if rc != 0:
        # ⚠️ 還沒有任何提交。**這是正常狀態**，⛔ 不是錯誤。
        print(MSG["no_head"]); return 0

    rc, _, _ = run(["git", "rev-parse", "--verify", "reviewed"], root)
    base = "reviewed" if rc == 0 else "HEAD"
    print(MSG["base_is"].format(base=base if rc == 0 else MSG["base_none"]))
    print()

    G = ["git", "-c", "core.quotepath=false", "--no-pager"]
    _, stat, _ = run(G + ["diff", "--stat", base], root)
    section(MSG["s1"], stat, MSG["s1_empty"].format(base=base))

    _, others, _ = run(G + ["ls-files", "--others", "--exclude-standard"], root)
    section(MSG["s2"], others, MSG["s2_empty"])

    _, log, _ = run(G + ["log", "--oneline", f"{base}..HEAD"], root) if base == "reviewed" \
        else (0, "", "")
    section(MSG["s3"], log, MSG["s3_empty"])

    if a.file:
        rel = a.file
        rc_i, _, _ = run(["git", "check-ignore", "-q", rel], root)
        if rc_i == 0:
            print(MSG["s4"].format(f=rel)); print("-" * 46)
            print(MSG["f_ignored"]); print("-" * 46); print(); return 0
        rc_t, tracked, _ = run(["git", "ls-files", "--error-unmatch", rel], root)
        if rc_t != 0:
            print(MSG["s4"].format(f=rel)); print("-" * 46)
            print(MSG["f_untracked"]); print("-" * 46); print(); return 0
        _, d, _ = run(G + ["diff", base, "--", rel], root)
        section(MSG["s4"].format(f=rel), d, MSG["s4_empty"].format(f=rel, base=base))

    print(MSG["footer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(MSG))
