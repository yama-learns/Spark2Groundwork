#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查點工具 —— **人工檢查點與 AI 檢查點的唯一定義處**

## 為什麼這支存在（**它取代了四份拷貝**）

同一套邏輯曾經有四份實作：`記錄快照.bat`（246 行）、`human_checkpoint.sh`（17 行）、
`ai_checkpoint.sh`，再乘以兩個語言版本。⛔ **那在結構上就是「修一層漏另一層」家族。**

**而它已經發作過兩次：**

| 實測 | 後果 |
|---|---|
| `R-33` 的修正只做在 `ai_checkpoint.sh`，`human_checkpoint.sh` 沒做 | **使用者按下去說「我看過了」的那一支，在鎖檔卡住時印假的成功** |
| `.bat` 的錯誤處理在「移植」成 `.sh` 時被簡化掉 | 246 行 → 17 行，**少掉的全部是錯誤處理** |

→ **邏輯收斂成這一支；`.bat` 與 `.command` 只負責雙擊時把它叫起來。**

## ⛔ 退出碼（憲章 §7.4）

    0  檢查點已建立，或**確認**沒有事情要做
    1  前置條件不成立（不是專案根目錄、找不到 git、參數錯誤）
    2  **我沒能做**（鎖檔卡住、git 指令失敗）——⛔ 這不等於「沒有事情要做」

⚠️ **1 與 2 的分界就是 `R-33`。** 「我沒能做」與「沒有事情要做」⛔ 不得共用一條退出路徑。

## ⚠️ 兩個版本的差異只在 MSG 表

**本檔的程式碼在中英文版逐字相同，⛔ 只有最上方的 `MSG` 不同。**
這是刻意的：兩版的行為差異變成可以用 `diff` 一眼看出來的東西。
"""
import argparse
import datetime
import pathlib
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title_human": "  SNAPSHOT [human review point: I have looked at this]",
 "title_ai":    "  SNAPSHOT [AI auto checkpoint, ⛔ NOT human-reviewed]",
 "usage": """Usage:
  Human checkpoint: python3 scripts/harness/checkpoint.py
  AI checkpoint:    python3 scripts/harness/checkpoint.py --mode ai \\
                        --role <role> --model <model> --topic <topic>

  <role>   single AI: agent | multi-role: governance | research | audit
           ⛔ Do not invent values. Defined in policy/HANDOFF.md §2
  <model>  a concrete model; ⛔ never a platform or family name
           Defined in policy/MODEL_IDENTITY.md
  <topic>  one word: what this round did""",
 "wrong_folder": """[FAIL] This is not the project root; ⛔ nothing was written.
       Missing: {missing}
       Current location: {root}
       -> Move this file back to the project root and run it again.""",
 "no_git": """[FAIL] git was not found.
       -> Windows: https://git-scm.com/download/win
       -> macOS: run `xcode-select --install`, or `brew install git`""",
 "need_args": "[FAIL] Missing arguments — ⛔ role, model and topic are all required.",
 "bad_role": """[FAIL] Role "{role}" is not in the value domain ({valid}).
       ⚠️ Inventing a category name is the entry point of the
          "required fields induce fabrication" family.""",
 "bad_model": """[FAIL] "{model}" is a platform or family name, not a model.
       ⚠️ A platform name is worse than a blank — it reads like an answer
          and stops the next reader from asking.""",
 "lock_stuck": """[FAIL] These lock files could be neither deleted nor moved:
       {locks}
       ⚠️ This environment grants neither unlink nor rename on .git.
       -> Remove them by hand and re-run. ⛔ Do not treat this as fine —
          no checkpoint was made.""",
 "init_repo": "No repository here yet — creating one...",
 "init_failed": "[FAIL] git init failed — see {log}",
 "init_done": "Done. This folder is now tracked.\n",
 "wrong_repo": """[FAIL] This folder sits **inside another git repository**; ⛔ nothing was written.
       -> Proceeding would commit the parent project's files as well.""",
 "no_gitignore": "[WARNING] No .gitignore found — large scratch files may get committed.",
 "changes_header": "\nChanges since the last checkpoint:",
 "new_files": "\nNew files not yet under version control:",
 "add_failed": """[FAIL] git add failed — **no checkpoint was made, the reviewed tag was not moved**.
       ⛔ "I could not do it" and "there was nothing to do" must not share an exit path.
       See {log}""",
 "commit_failed": """[FAIL] git commit failed — **no checkpoint was made, the reviewed tag was not moved**.
       ⚠️ The staged work is intact; ⛔ nothing was lost. See {log}""",
 "nothing_to_commit": "No changes (⚠️ git add confirmed successful first, so this may be read as \"nothing to do\")",
 "committed_human": "  ✅ New checkpoint created.",
 "committed_ai": "  ✅ AI checkpoint created: [{role}/{model}-{topic}]",
 "tag_moved": "  ✅ Done. Reviewed baseline moved to the latest checkpoint.",
 "tag_not_moved": "  ⛔ The reviewed tag was **not moved** — a file the AI saved is not a file you reviewed.",
 "recent": "\nLast 5 checkpoints:",
}


VALID_ROLES = ("governance", "research", "audit", "agent")
# ⚠️ 白名單在這裡是正確用法：它定義**取值域**，不是掃描範圍（`R-21` 管的是後者）。
PLATFORM_NAMES = ("claude", "gemini", "gpt", "openai", "antigravity",
                  "cowork", "codex", "copilot", "ai", "agent", "llm")
SENTINELS = ("governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md")


def utcstamp(fmt):
    return datetime.datetime.now(datetime.timezone.utc).strftime(fmt)


def run(args, cwd, log):
    """跑一個 git 指令，回傳 (returncode, stdout+stderr)。⛔ 一律記進日誌。"""
    p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{utcstamp('%Y-%m-%dT%H:%M:%SZ')}] $ {' '.join(args)}\n")
        f.write(f"    rc={p.returncode}\n")
        if out.strip():
            f.write("".join("    " + ln + "\n" for ln in out.strip().splitlines()))
    return p.returncode, out


def sweep_locks(root, log):
    """清 `.git` 內所有鎖檔。刪不掉改用 rename，兩者都失敗才回報。

    ⚠️ **掃全樹，⛔ 不列舉檔名。** 實測個案：一次提交卡在
    `.git/refs/heads/master.lock`，而當時的腳本只清三個寫死的名字，
    **於是它既沒清掉也沒檢查，只印出「commit failed」而沒有任何可用線索。**

    ⚠️ **rename 後備的理由：** 部分掛載環境對 `.git` 拒絕 unlink，**但允許 rename。**
    """
    stuck, stamp = [], utcstamp("%Y%m%dT%H%M%SZ")
    gitdir = root / ".git"
    if not gitdir.exists():
        return stuck
    for lock in gitdir.rglob("*.lock"):
        if not lock.exists():
            continue
        try:
            lock.unlink()
            continue
        except OSError:
            pass
        try:
            lock.rename(lock.with_suffix(lock.suffix + f".stale.{stamp}"))
            continue
        except OSError:
            stuck.append(str(lock.relative_to(root)))
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{utcstamp('%Y-%m-%dT%H:%M:%SZ')}] lock sweep: stuck={stuck}\n")
    return stuck


def main(MSG):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--mode", choices=("human", "ai"), default="human")
    ap.add_argument("--role", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--topic", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(MSG["usage"]); return 0

    root = pathlib.Path(a.root).resolve() if a.root else \
        pathlib.Path(__file__).resolve().parents[2]
    log = root / "git-checkpoint.log"

    print("=" * 46)
    print(MSG["title_ai"] if a.mode == "ai" else MSG["title_human"])
    print("=" * 46)

    # ── 前置 1：這是不是專案根目錄 ─────────────────────────────────
    # ⚠️ 哨兵檔證明身分。改治理檔名時要改這裡，⛔ 但不得移除這項檢查。
    missing = [s for s in SENTINELS if not (root / s).is_file()]
    if missing:
        print(MSG["wrong_folder"].format(missing=", ".join(missing), root=root))
        return 1

    # ── 前置 2：git 在不在 ────────────────────────────────────────
    try:
        subprocess.run(["git", "--version"], cwd=str(root),
                       capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print(MSG["no_git"]); return 1

    # ── 前置 3：AI 模式的三個必填參數 ──────────────────────────────
    if a.mode == "ai":
        if not (a.role and a.model and a.topic):
            print(MSG["need_args"]); print(MSG["usage"]); return 1
        if a.role not in VALID_ROLES:
            print(MSG["bad_role"].format(role=a.role,
                                         valid=" ".join(VALID_ROLES)))
            return 1
        if a.model.lower() in PLATFORM_NAMES:
            print(MSG["bad_model"].format(model=a.model)); return 1

    with log.open("a", encoding="utf-8") as f:
        f.write(f"\n[{utcstamp('%Y-%m-%dT%H:%M:%SZ')}] ---- start mode={a.mode} ----\n")

    # ── 清鎖（⛔ 必須在 rev-parse 之前，否則守衛本身跑不動）──────────
    stuck = sweep_locks(root, log)
    if stuck:
        print(MSG["lock_stuck"].format(locks="\n       ".join(stuck)))
        return 2

    # ── 前置 4：repo 存在，且它的根就在這裡 ────────────────────────
    rc, _ = run(["git", "rev-parse", "--is-inside-work-tree"], root, log)
    if rc != 0:
        print(MSG["init_repo"])
        rc, out = run(["git", "init", "-q"], root, log)
        if rc != 0:
            print(MSG["init_failed"].format(log=log.name)); return 2
        print(MSG["init_done"])
    else:
        rc, prefix = run(["git", "rev-parse", "--show-prefix"], root, log)
        if prefix.strip():
            print(MSG["wrong_repo"]); return 1

    if not (root / ".gitignore").is_file():
        print(MSG["no_gitignore"])

    # ── 顯示這一輪動了什麼 ────────────────────────────────────────
    G = ["git", "-c", "core.quotepath=false"]
    print(MSG["changes_header"])
    print("-" * 46)
    _, out = run(G + ["--no-pager", "diff", "--stat", "--summary", "HEAD"], root, log)
    if out.strip():
        print(out.rstrip())
    _, untracked = run(G + ["ls-files", "--others", "--exclude-standard"], root, log)
    if untracked.strip():
        print(MSG["new_files"])
        print(untracked.rstrip())
    print("-" * 46)

    # ── 🔴 R-33 的位置：add 失敗 ⛔ 不得往下走到「無變更」分支 ────────
    rc, out = run(G + ["add", "-A"], root, log)
    if rc != 0:
        print(MSG["add_failed"].format(log=log.name)); return 2

    rc, _ = run(["git", "diff", "--cached", "--quiet"], root, log)
    if rc == 0:
        # ⚠️ 只有在 add 已確認成功之後，這裡才可以解讀為「沒有事情要做」。
        print(MSG["nothing_to_commit"])
    else:
        if a.mode == "ai":
            msg = (f"auto: {utcstamp('%Y-%m-%d %H:%MZ')} "
                   f"[{a.role}/{a.model}-{a.topic}] -- AI auto checkpoint, NOT human-reviewed")
            ident = ["-c", "user.name=AI agent", "-c", "user.email=agent@local"]
        else:
            msg = f"snapshot {utcstamp('%Y-%m-%d %H:%MZ')}"
            ident = ["-c", "user.name=researcher", "-c", "user.email=me@local"]
        rc, out = run(["git"] + ident + ["commit", "-q", "-m", msg], root, log)
        if rc != 0:
            print(MSG["commit_failed"].format(log=log.name)); return 2
        print(MSG["committed_ai"].format(role=a.role, model=a.model, topic=a.topic)
              if a.mode == "ai" else MSG["committed_human"])

    # ── reviewed 標籤 ────────────────────────────────────────────
    # ⚠️ AI 模式 ⛔ 不移動標籤——「AI 自己存的檔不算你看過」，這個區分是刻意的。
    # ⚠️ 人工模式即使「無變更」也要移動——AI 可能已經自己提交過那些工作，
    #    而人按下這一支的意思就是「我看過了」。
    if a.mode == "ai":
        print(MSG["tag_not_moved"])
    else:
        run(["git", "tag", "-f", "reviewed"], root, log)
        print(MSG["tag_moved"])

    _, recent = run(["git", "--no-pager", "log", "--oneline", "-5"], root, log)
    if recent.strip():
        print(MSG["recent"])
        print(recent.rstrip())
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{utcstamp('%Y-%m-%dT%H:%M:%SZ')}] ---- end rc=0 ----\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(MSG))
