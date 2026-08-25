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

# ⛔ 輸出編碼必須先固定成 UTF-8，⛔ 否則 Windows 上印到第一個符號就當掉。
#    唯一定義處：`_common._force_utf8`（見該處的實測個案）。
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title": "  上次「我看過了」之後，動了什麼",
 "usage": """用法：
  python3 scripts/harness/review_changes.py              看總覽
  python3 scripts/harness/review_changes.py <檔案路徑>   再看某個檔案的逐行差異

⛔ 這支只讀不寫：不 commit、不 checkout、不 reset、不清鎖檔。""",
 "wrong_folder": """[FAIL] 這不是專案根目錄。
       找不到：{missing}
       目前位置：{root}""",
 "no_git": """[FAIL] 找不到 git。
       → Windows：https://git-scm.com/download/win
       → macOS：終端機執行 `xcode-select --install`，或 `brew install git`""",
 "no_repo": """[FAIL] 這個資料夾還沒有版本控制。
       → 先按一次「記錄快照」按鈕，它會幫你建立。""",
 "wrong_repo": "[FAIL] 這個資料夾位於另一個 git 倉庫之內。",
 "no_head": """還沒有任何檢查點——**沒有東西可以比較。**
⚠️ 這是正常狀態，⛔ 不是錯誤。按一次「記錄快照」就會有第一個檢查點。""",
 "base_is": "比較基準：{base}",
 "base_none": "HEAD（⚠️ 還沒有 reviewed 標籤，代表你還沒按過人工檢查點）",
 "s1": "[1] 哪些檔案被動了，各動了幾行",
 "s1_empty": "（空白代表：沒有任何已納入版本控制的檔案與 {base} 不同）",
 "s2": "[2] 還沒納入版本控制的新檔案",
 "s2_empty": "（空白代表：沒有新檔案）",
 "s3": "[3] 這段期間建立的檢查點（⚠️ `auto:` 開頭的是 AI 自己存的，⛔ 不代表你看過）",
 "s3_empty": "（空白代表：你上次看過之後沒有新的檢查點）",
 "s4": "[4] 逐行差異：{f}",
 "s4_empty": "（空白代表：{f} 自 {base} 以來沒有變動）",
 "f_untracked": """這個檔案還沒有被 git 追蹤，**所以沒有東西可以拿來比較。**
它會出現在上面的 [2] 區。按一次「記錄快照」之後就會開始被追蹤。""",
 "f_ignored": """這個檔案被 `.gitignore` **刻意排除**在版本控制之外。
關於那些目錄是什麼，見憲章 §6.2。
⛔ 它沒有留下任何紀錄，所以無法比較。""",
 "footer": "看完之後：若你認可這些變更，按一次「記錄快照」＝ 告訴框架「我看過了」。",
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
