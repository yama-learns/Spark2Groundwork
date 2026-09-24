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
**那不是壞掉，但人工已閱比較尚未完成。** 應顯示 INCOMPLETE 與下一步。

退出碼：0 有效已閱基準且比較完成｜1 專案位置不對｜2 基準缺失或查詢未完成
"""
import argparse
import os
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
 "no_git": """[INCOMPLETE] 找不到可執行的 Git；這次沒有可信差異結果。
       請開啟 docs/START_HERE.html，依圖形安裝說明處理後再查看變更。""",
 "no_repo": """[INCOMPLETE] 這個資料夾尚無版本控制與人工已閱基準。
       請先閱讀初始內容，確認後親按「記錄快照」；AI 不得代按。""",
 "wrong_repo": "[FAIL] 這個資料夾位於另一個 git 倉庫之內。",
 "no_head": """[INCOMPLETE] 尚無第一個檢查點，無法比較人類已閱後的變更。
       請先閱讀初始內容，確認後親按「記錄快照」；AI 不得代按。""",
 "no_reviewed": """[INCOMPLETE] 找不到人工已閱基準 reviewed。AI 的「儲存進度」不代表你已閱讀。
       請先盤點並親自閱讀現有內容；確實看過後再親按「記錄快照」。此時不能宣稱沒有未讀變更。""",
 "invalid_reviewed": """[INCOMPLETE] reviewed 標籤不是目前 HEAD 歷史中的有效提交基準。
       保留現有資料及標籤，請具本機執行能力的 AI 協助查明；親自核對內容後才決定新的已閱基準。""",
 "git_error": """[INCOMPLETE] Git 查詢未完成；這次沒有可信差異結果。
       保留現有資料，請具本機執行能力的 AI 檢查後重試；不要把空白當成已閱。""",
 "base_is": "比較基準：{base}",
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
