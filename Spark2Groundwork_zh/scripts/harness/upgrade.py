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

# ⛔ 輸出編碼必須先固定成 UTF-8，⛔ 否則 Windows 上印到第一個符號就當掉。
#    唯一定義處：`_common._force_utf8`（見該處的實測個案）。
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title": "  框架升級（⛔ 只換框架，不碰你的資料）",
 "usage": """用法：
  python3 scripts/harness/upgrade.py check          我這一版是什麼？最新是什麼？
  python3 scripts/harness/upgrade.py diff           _upgrade/ 裡的新版差在哪？
  python3 scripts/harness/upgrade.py apply <資料夾>  換掉其中一個

⛔ 本工具不下載、不自動覆蓋。下載請自己做，放進 `_upgrade/`。""",
 "wrong_folder": "[FAIL] 這不是專案根目錄（找不到 governance/AGENTS.md）。目前位置：{root}",
 "check_head": "你現在的版本：",
 "check_row": "  {d:<12} {v}",
 "unknown": "（無版本標記）",
 "latest": "GitHub 上最新的發行版本：{tag}",
 "check_offline": """[INCOMPLETE] 查不到 GitHub 上的最新版本（{err}）。
       ⚠️ **這不等於「你已經是最新的」**——是「這一次沒查成」。
       → 可能是沒有網路、或防火牆擋住。手動查：
         https://github.com/yama-learns/Spark2Groundwork/releases""",
 "check_tail": """下一步：把新版下載到 `_upgrade/`，然後跑 `upgrade.py diff`。
⛔ 只替換上面列出的項目。**其餘一切都不碰，包含你自己開的資料夾。**""",
 "no_upgrade_dir": """[FAIL] 找不到 `_upgrade/`。
       → 先把新版下載並解壓到專案裡的 `_upgrade/` 資料夾，再跑一次。""",
 "diff_none": "`_upgrade/` 裡的版本與你現在的完全相同——⛔ 沒有東西需要換。",
 "diff_head": "以下框架項目與你現在的不同：",
 "diff_row": "  {name:<20} 內容不同 {m} 個檔｜新增 {n} 個檔",
 "diff_tail": """要換其中一個：`upgrade.py apply <名稱>`
⚠️ **一次換一個。** ⛔ 沒有「全部換掉」這個選項——
**那會讓你在出問題時分不出是哪一包造成的。**""",
 "never": """[FAIL] 「{t}」是**你的資料**，⛔ 升級工具永遠不會碰它。
       （憲章 §6.3：那一類壞掉之後沒有任何地方可以還原。）""",
 "not_framework": "[FAIL] 「{t}」不是可替換的框架項目。可換的是：{ok}",
 "missing_in_upgrade": "[FAIL] `_upgrade/` 裡沒有「{t}」。來源：{src}",
 "cp_first": "覆蓋前先建立檢查點（⛔ 這一步失敗就不會覆蓋）……\n",
 "cp_failed": """
[FAIL] 檢查點沒有建立（退出碼 {rc}）——⛔ **什麼都沒有被覆蓋。**
       ⚠️ 先把檢查點的問題解決，再回來升級。""",
 "applied": "\n  ✅ 已換掉：{t}",
 "applied_tail": """
下一步：
  1. 按「查看變更」按鈕，看這一包換掉了什麼
  2. 跑 `python3 scripts/harness/run_all_sensors.py` 確認還是綠的
  3. 🔴 **跑 `python3 scripts/harness/tool_my_index.py` 重新產生你的文件索引**
     ⚠️ 升級動了框架檔案，索引因此過期——⛔ 不重跑的話下一輪會看到 MY_INDEX_STALE
  4. ⚠️ **若你之前手動改過這一包裡的檔案，那些改動現在不見了**——
     用「查看變更」把它們找回來（檢查點還在）
  5. ⚠️ **框架若新增了工作守則，`my/MY_RULES.md` 會少幾條**——
     跑 `python3 scripts/harness/tool_sync_my_rules.py` 把原句補進去""",
 "apply_needs_target": "[FAIL] 請指定要換掉哪一個，例如：upgrade.py apply governance",
}


# 🔴 **可整包替換的框架項目。這兩份清單就是保護機制本身。**
#    ⛔ **不在這兩份清單上的任何東西，一律不會被替換**——
#    **包含使用者自己開的資料夾（筆記、圖表、投稿版本……），⛔ 那些名字不可能事先列舉。**
#    ⚠️ 成對樣本見 `run_selftest.py` 的 `upgrade_case()`：
#    **拿一個工具沒聽過的資料夾當目標，必須被拒絕，且內容原封不動。**
# ⚠️ **v1.4.1 補進 `docs` 與六個啟動器。**
#    🔴 **它們一直是框架擁有的東西，⛔ 卻不在可替換清單上——
#    意思是：v1.3.0 修好的七處說明圖跑版，⛔ 送不到任何一個既有專案。**
#    ⚠️ **這一筆是 `tool_my_index.py` 上線後第一次執行就抓到的：
#    它把「框架⛔ 不擁有的東西」列出來，而 `docs/` 與六個按鈕出現在那份清單裡。**
FRAMEWORK_DIRS = ("governance", "policy", "profiles", "prompts", "scripts", "docs")
FRAMEWORK_FILES = ("README.md", "SETUP.md", "INITIALIZE_PROMPT.md", "file_index.md",
                   "查看變更.bat", "查看變更.command",
                   "檢查更新.bat", "檢查更新.command",
                   "記錄快照.bat", "記錄快照.command")
# 🔴 **`.gitignore` 與 `.gitattributes` 刻意⛔ 不列在上面。**
#    ⚠️ **它們是混合所有權：框架給了預設值，⛔ 而使用者會往裡面加自己的規則。**
#    **⇒ 依憲章 §6.4，⛔ 整包替換會刪掉使用者加的那幾行。**
#    ⛔ **已知代價：框架日後若改了預設忽略規則，⛔ 送不到既有專案。⚠️ 寫在這裡，不留白。**
# ⚠️ **這一份⛔ 不是保護機制。** 保護機制是上面那兩份「可替換清單」。
#    **本清單唯一的用途，是在使用者不小心把常見的自有資料當成升級目標時，
#    給他一句看得懂的錯誤訊息**，而不是通用的「這不是可替換項目」。
#    ⛔ **不要把它改成主要防線**——**那會讓沒列在這裡的資料夾看起來像是不受保護的。**
NEVER_TOUCH = ("PROJECT.md", "ledgers", "corpus", "corpus_md", "handoffs",
               "my", "NEXT_SESSION_MEMO.md", "governance_config.json")
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
