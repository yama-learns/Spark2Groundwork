#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升級工具 —— **框架資料夾可以整包換掉，你的資料不會被碰到**

三個步驟，⛔ 每一步都停下來等你決定：

    check    我這一版是什麼？GitHub 上最新的是什麼？
    diff     `_upgrade/` 裡的新版，跟我現在的差在哪？
    apply    把其中**一個**資料夾換掉（⛔ 換之前強制建立檢查點）

⛔ **本工具不會下載任何東西，也不會自動覆蓋。**
下載由你做（`git clone` 或在 GitHub 上按 Download ZIP），放進 `_upgrade/`。

⚠️ **為什麼不做成一鍵自動：覆蓋是不可逆的。**
**不可逆的操作只隔一個按鈕，遲早會被誤按。**

退出碼：0 正常｜1 前置條件不成立｜2 我沒能查／沒能做
"""
import argparse
import difflib
import hashlib
import pathlib
import shutil
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title": "  Framework upgrade (⛔ framework only; your data is never touched)",
 "usage": """Usage:
  python3 scripts/harness/upgrade.py check         what version am I on? what is latest?
  python3 scripts/harness/upgrade.py diff          what differs in `_upgrade/`?
  python3 scripts/harness/upgrade.py apply <name>  replace one of them

⛔ This tool never downloads and never overwrites on its own.
Download it yourself and put it in `_upgrade/`.""",
 "wrong_folder": "[FAIL] Not the project root (no governance/AGENTS.md). Current location: {root}",
 "check_head": "Your current versions:",
 "check_row": "  {d:<12} {v}",
 "unknown": "(no version marker)",
 "latest": "Latest release on GitHub: {tag}",
 "check_offline": """[INCOMPLETE] Could not reach GitHub to read the latest version ({err}).
       ⚠️ **This does not mean you are up to date** — it means this check did not run.
       -> Possibly no network, or a firewall. Check by hand:
         https://github.com/yama-learns/Spark2Groundwork/releases""",
 "check_tail": """Next: download the new version into `_upgrade/`, then run `upgrade.py diff`.
⛔ Your PROJECT.md, ledgers, corpus, handoffs and incidents/ are never touched.""",
 "no_upgrade_dir": """[FAIL] No `_upgrade/` folder found.
       -> Download and unpack the new version into `_upgrade/` inside this project, then re-run.""",
 "diff_none": "What is in `_upgrade/` is identical to what you have — ⛔ nothing to replace.",
 "diff_head": "These framework items differ from yours:",
 "diff_row": "  {name:<20} {m} file(s) changed | {n} new",
 "diff_tail": """To replace one: `upgrade.py apply <name>`
⚠️ **One at a time.** ⛔ There is no "replace everything" option —
**it would leave you unable to tell which package caused a problem.**""",
 "never": """[FAIL] "{t}" is **your data**; ⛔ the upgrade tool never touches it.
       (Constitution §6.3: that class can be restored from nowhere.)""",
 "not_framework": "[FAIL] \"{t}\" is not a replaceable framework item. Replaceable: {ok}",
 "missing_in_upgrade": "[FAIL] `_upgrade/` does not contain \"{t}\". Source: {src}",
 "cp_first": "Making a checkpoint before overwriting (⛔ if this fails, nothing is overwritten)...\n",
 "cp_failed": """
[FAIL] No checkpoint was made (exit {rc}) — ⛔ **nothing was overwritten.**
       ⚠️ Fix the checkpoint problem first, then come back.""",
 "applied": "\n  ✅ Replaced: {t}",
 "applied_tail": """
Next:
  1. Press the review-changes button to see what this package changed
  2. Run `python3 scripts/harness/run_all_sensors.py` and confirm it is still green
  3. ⚠️ **If you had hand-edited files in this package, those edits are gone now** —
     recover them with review-changes (the checkpoint is still there)""",
 "apply_needs_target": "[FAIL] Say which one, e.g.: upgrade.py apply governance",
}


# 🔴 可整包替換的框架資料夾。⛔ 不在此列者一律不碰（憲章 §6.3 的「不可還原」那一類）。
FRAMEWORK_DIRS = ("governance", "policy", "profiles", "prompts", "scripts")
FRAMEWORK_FILES = ("README.md", "SETUP.md", "INITIALIZE_PROMPT.md", "file_index.md")
# ⛔ 這些是你的東西，升級⛔ 永遠不碰它們。
NEVER_TOUCH = ("PROJECT.md", "ledgers", "corpus", "corpus_md", "handoffs",
               "incidents", "NEXT_SESSION_MEMO.md", "governance_config.json")
VERSION_FILE = "_VERSION"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def read_version(p):
    """只取第一個非註解、非空的行。

    ⚠️ 首版直接 `.strip()` 整個檔案，**於是把說明註解一起當成版本號印出來**——
    ⛔ 一個把三行註解顯示成「版本」的畫面，讀者無法判斷自己是哪一版。
    """
    if not p.is_file():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return None


def local_versions(root):
    return {d: read_version(root / d / VERSION_FILE) for d in FRAMEWORK_DIRS}


def cmd_check(root, MSG):
    print(MSG["check_head"])
    for d, v in local_versions(root).items():
        print(MSG["check_row"].format(d=d, v=v or MSG["unknown"]))
    print()
    try:
        import urllib.request, json
        url = "https://api.github.com/repos/yama-learns/Spark2Groundwork/releases/latest"
        with urllib.request.urlopen(url, timeout=10) as r:
            tag = json.load(r).get("tag_name", "")
        print(MSG["latest"].format(tag=tag or MSG["unknown"]))
    except Exception as e:                                  # noqa: BLE001
        # ⛔ 查不到就說查不到。**「查不到」與「已是最新」⛔ 不得共用一個輸出。**
        print(MSG["check_offline"].format(err=type(e).__name__))
        return 2
    print(MSG["check_tail"])
    return 0


def pairs(root, src):
    for d in FRAMEWORK_DIRS:
        if (src / d).is_dir():
            yield d, root / d, src / d
    for f in FRAMEWORK_FILES:
        if (src / f).is_file():
            yield f, root / f, src / f


def cmd_diff(root, src, MSG):
    changed = []
    for name, cur, new in pairs(root, src):
        if new.is_file():
            same = cur.is_file() and sha(cur) == sha(new)
            if not same:
                changed.append((name, 1, 0 if cur.is_file() else 1))
            continue
        n_mod = n_new = 0
        for np in sorted(new.rglob("*")):
            if not np.is_file() or VERSION_FILE == np.name:
                continue
            rel = np.relative_to(new)
            cp = cur / rel
            if not cp.is_file():
                n_new += 1
            elif sha(cp) != sha(np):
                n_mod += 1
        if n_mod or n_new:
            changed.append((name, n_mod, n_new))
    if not changed:
        print(MSG["diff_none"]); return 0
    print(MSG["diff_head"])
    for name, m, n in changed:
        print(MSG["diff_row"].format(name=name, m=m, n=n))
    print()
    print(MSG["diff_tail"])
    return 0


def cmd_apply(root, src, target, MSG):
    if target in NEVER_TOUCH:
        print(MSG["never"].format(t=target)); return 1
    if target not in FRAMEWORK_DIRS and target not in FRAMEWORK_FILES:
        print(MSG["not_framework"].format(t=target,
              ok=" ".join(FRAMEWORK_DIRS + FRAMEWORK_FILES))); return 1
    s = src / target
    if not s.exists():
        print(MSG["missing_in_upgrade"].format(t=target, src=src)); return 1

    # ⛔ R-33 的位置：檢查點失敗 ⛔ 不得往下覆蓋。
    print(MSG["cp_first"])
    rc = subprocess.run([sys.executable, str(root / "scripts/harness/checkpoint.py"),
                         "--root", str(root)]).returncode
    if rc != 0:
        print(MSG["cp_failed"].format(rc=rc)); return 2

    dst = root / target
    if dst.is_dir():
        shutil.rmtree(dst); shutil.copytree(s, dst)
    else:
        shutil.copy2(s, dst)
    print(MSG["applied"].format(t=target))
    print(MSG["applied_tail"])
    return 0


def main(MSG):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("action", nargs="?", default="check",
                    choices=("check", "diff", "apply"))
    ap.add_argument("target", nargs="?", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(MSG["usage"]); return 0
    root = pathlib.Path(a.root).resolve() if a.root else \
        pathlib.Path(__file__).resolve().parents[2]
    if not (root / "governance/AGENTS.md").is_file():
        print(MSG["wrong_folder"].format(root=root)); return 1

    print("=" * 46); print(MSG["title"]); print("=" * 46); print()
    if a.action == "check":
        return cmd_check(root, MSG)

    src = root / "_upgrade"
    if not src.is_dir():
        print(MSG["no_upgrade_dir"]); return 1
    # 允許 _upgrade/ 底下多包一層（下載 zip 常會如此）
    inner = [p for p in src.iterdir() if p.is_dir() and (p / "governance").is_dir()]
    if (not (src / "governance").is_dir()) and len(inner) == 1:
        src = inner[0]

    if a.action == "diff":
        return cmd_diff(root, src, MSG)
    if not a.target:
        print(MSG["apply_needs_target"]); return 1
    return cmd_apply(root, src, a.target, MSG)


if __name__ == "__main__":
    raise SystemExit(main(MSG))
