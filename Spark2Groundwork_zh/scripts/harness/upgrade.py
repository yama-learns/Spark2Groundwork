#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升級工具 —— **框架資料夾可以整包換掉，你的資料不會被碰到**

三個步驟，⛔ 每一步都停下來等你決定：

    check    我這一版是什麼？GitHub 上最新的是什麼？
    diff     `_upgrade/` 裡的新版，跟我現在的差在哪？
    apply    把其中**一個**資料夾換掉（⛔ 換之前強制建立檢查點與持久收據）
    receipts 列出升級與復原留下的持久收據
    receipt-diff  以收據查看升級前後差異
    restore       從收據安全取回一個檔案

⛔ **本工具不會下載任何東西，也不會自動覆蓋。**
下載由你做（`git clone` 或在 GitHub 上按 Download ZIP），放進 `_upgrade/`。

⚠️ **為什麼不做成一鍵自動：覆蓋是不可逆的。**
**不可逆的操作只隔一個按鈕，遲早會被誤按。**

退出碼：0 正常｜1 前置條件不成立｜2 我沒能查／沒能做
"""
import argparse
import datetime
import difflib
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
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
  python3 scripts/harness/upgrade.py receipts       列出持久升級還原收據
  python3 scripts/harness/upgrade.py receipt-diff <收據> [路徑]
  python3 scripts/harness/upgrade.py restore <收據> <路徑>

⛔ 本工具不下載、不自動覆蓋。下載請自己做，放進 `_upgrade/`。""",
 "wrong_folder": "[FAIL] 這不是專案根目錄（找不到 governance/AGENTS.md）。目前位置：{root}",
 "check_head": "你現在的版本：",
 "check_row": "  {d:<12} {v}",
 "check_marker_warning": "⚠️ 版本標記只表示資料夾自稱哪一版，⛔ 不證明內容完整；請以 diff 檢查實際內容。",
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
 "diff_row": "  {name:<20} 內容不同 {m} 個檔｜新增 {n} 個檔｜目標端獨有 {o} 個檔",
 "target_only_row": "      ⛔ {path}",
 "diff_tail": """要換其中一個：`upgrade.py apply <名稱>`
⚠️ **一次換一個。** ⛔ 沒有「全部換掉」這個選項——
**那會讓你在出問題時分不出是哪一包造成的。**

若上方列出 `prompts/TEMPLATE_decompose.txt`，先搬到專案根目錄並改名為
`第一個想法.md`；若列出 `scripts/` 內的自建工具，先搬到 `my/tools/`。""",
 "never": """[FAIL] 「{t}」是**你的資料**，⛔ 升級工具永遠不會碰它。
       （憲章 §6.3：那一類壞掉之後沒有任何地方可以還原。）""",
 "not_framework": "[FAIL] 「{t}」不是可替換的框架項目。可換的是：{ok}",
 "retired_target": """[FAIL] 「{t}」已於 {v} 退役，內容併入 `{into}/`——⛔ 升級工具不再替換它。
       ⚠️ **你專案裡那個資料夾⛔ 沒有被刪掉。** 確認 `{into}/` 已有你要的內容之後，它可以自己刪。""",
 "missing_in_upgrade": "[FAIL] `_upgrade/` 裡沒有「{t}」。來源：{src}",
 "target_only_block": """[FAIL] 「{t}」內有新版來源沒有的檔案，⛔ **尚未建立檢查點，也沒有替換任何東西。**
       這些檔案可能屬於專案；請先逐一搬到整包替換範圍外，再重跑：""",
 "retired_head": """
⚠️ **這幾個資料夾已經退役，⛔ 而升級工具⛔ 不會刪掉你的東西：**""",
 "retired_row": "      ⛔ `{d}/`（於 {v} 併入 `{into}/`）——**內容已經在 `{into}/` 了；確認之後這個資料夾可以自己刪掉**",
 "cp_first": "覆蓋前先建立檢查點（⛔ 這一步失敗就不會覆蓋）……\n",
 "cp_failed": """
[FAIL] 檢查點沒有建立（退出碼 {rc}）——⛔ **什麼都沒有被覆蓋。**
       ⚠️ 先把檢查點的問題解決，再回來升級；若是下載包缺檔或版本不相符，
          請重新下載同語言、同版本的完整套件。""",
 "checkpoint_peer_missing": """[FAIL] 找不到與本升級器相符、支援 tool mode 的 `checkpoint.py`。
       ⛔ 尚未建立檢查點、收據，也沒有寫入任何專案檔案。
       → 請重新下載同語言、同版本的完整套件，保持 `upgrade.py` 與
         同目錄的 `checkpoint.py` 一起使用。""",
 "applied": "\n  ✅ 已換掉：{t}",
 "no_receipt": """
[FAIL] 檢查點建立了，⛔ **而我讀不回它的提交編號（退出碼 {rc}）——什麼都沒有被覆蓋。**
       🔴 **理由：那個編號是你日後取回手動改動的唯一入口。**
       **⛔ 一次「存了還原點，卻說不出還原點在哪」的覆蓋，等於沒有還原點。**
       → 先 `git status` 看倉庫狀態，處理完再回來升級。""",
 "receipt_unprotected": """
[FAIL] 檢查點存在，⛔ **但以下檔案無法依 Git 語意從檢查點還原：**
{paths}
       什麼都沒有被覆蓋。只有提交編號不等於有效的還原收據。
       → 請確認這些檔案已由 Git 追蹤，且未被 ignore／assume-unchanged／
          skip-worktree 等規則隱藏，再重新執行升級。""",
 "receipt_create_failed": """
[FAIL] 檢查點存在，⛔ **但無法建立持久升級收據：** {err}
       什麼都沒有被覆蓋；檢查點提交仍然存在。""",
 "receipt": """
🔴 **已在升級前建立專案本地持久還原收據：**
      收據：    {rid}
      提交：    {cp}
      替換目標：{target}
  這次替換會覆蓋的既有非暫存檔案，已逐一依 Git 內容語意與檢查點核對。
  收據由本專案 Git 私有參照固定，可用 `upgrade.py receipts` 列出。
  ⚠️ 它不會隨一般 `git clone` 或檔案備份自動搬到另一個倉庫。""",
 "applied_tail": """
下一步：
  1. 按「查看變更」按鈕，看這一包換掉了什麼
  2. 跑 `python3 scripts/harness/run_all_sensors.py` 確認還是綠的
  3. 🔴 **跑 `python3 scripts/harness/tool_my_index.py` 重新產生你的文件索引**
     ⚠️ 升級動了框架檔案，索引因此過期——⛔ 不重跑的話下一輪會看到 MY_INDEX_STALE
  4. ⚠️ **若你之前手動改過這一包裡的檔案，那些改動現在不見了**——
     🔴 **⛔「查看變更」按鈕看不到它們。**
     ⚠️ **那個按鈕以 `reviewed`（你上次按「我看過了」的位置）為基準，
     ⛔ 而工具建立的還原點刻意不移動那個標籤**——⛔ 於是還原點落在它的視野之外。
     **完整且相符的 v1.4.4 套件可使用內建收據介面，不需要輸入原始 Git 指令：**
       列出收據：      python3 scripts/harness/upgrade.py receipts
       查看單檔差異：  python3 scripts/harness/upgrade.py receipt-diff {rid} <檔案路徑>
       還原一個檔案：  python3 scripts/harness/upgrade.py restore {rid} <檔案路徑>
  5. ⚠️ **框架若新增了工作守則，`my/MY_RULES.md` 會少幾條**——
     跑 `python3 scripts/harness/tool_sync_my_rules.py` 把原句補進去\n  6. ⚠️ **框架若修訂了一條既有規則，`my/MY_RULES.md` 的副本會停在舊文字**——\n     那支工具會印出逐行差異，⛔ **而它不會替你寫檔**：\n     把 `+` 開頭的那幾行逐字貼進該條正文。\n     ⛔ **標了覆寫的條目它一律不碰**""",
 "apply_needs_target": "[FAIL] 請指定要換掉哪一個，例如：upgrade.py apply governance",
 "receipts_empty": "這個專案目前沒有持久升級收據。",
 "receipts_head": "持久升級還原收據（新到舊）：",
 "receipts_row": "  {rid}  {created}  {operation:<14}  {target}",
 "receipts_bad": "  [WARN] 已略過無法讀取的收據檔：{name}（{err}）",
 "receipt_needs_id": "[FAIL] 請提供收據編號（或 `latest`）。可先執行 `upgrade.py receipts`。",
 "receipt_unknown": "[FAIL] 找不到有效收據 `{rid}`。請執行 `upgrade.py receipts` 查看。",
 "receipt_invalid": "[FAIL] 收據 `{rid}` 未通過完整性檢查：{err}",
 "receipt_path_bad": "[FAIL] `{path}` 不在此收據的替換目標 `{target}` 內。",
 "receipt_path_not_saved": "[FAIL] 收據 `{rid}` 沒有保存 `{path}` 的升級前檔案。",
 "receipt_diff_head": "收據 `{rid}` 之後 `{path}` 的變更：",
 "receipt_no_diff": "  （與此收據相比，沒有 Git 追蹤內容差異）",
 "receipt_new_head": "  收據建立時不存在、目前新增的路徑：",
 "receipt_new_row": "      + {path}",
 "restore_needs_path": "[FAIL] 請指定收據內恰好一個檔案路徑。",
 "restore_current_missing": "[FAIL] `{path}` 目前不存在或不是一般檔案；因無法先建立復原前的反向收據，未執行還原。",
 "restore_noop": "`{path}` 已與收據 `{rid}` 相同；沒有變更。",
 "restore_cp_first": "還原前先建立反向檢查點……",
 "restore_cp_failed": """[FAIL] 反向檢查點失敗（退出碼 {rc}）；沒有還原任何檔案。
       若是下載包缺檔或版本不相符，請重新下載同語言、同版本的完整套件。""",
 "edition_guard_failed": """[FAIL] 無法證明升級來源與目前專案是同一語言版本。
       升級來源：{source}；目前專案：{project}。
       ⛔ 尚未建立檢查點、收據，也沒有替換任何檔案。
       ⚠️ 判定只讀下列十二個框架啟動器檔名，⛔ 不看是誰放的。實際看到的是：
         升級來源：{src_found}
         目前專案：{root_found}
       → 請使用同語言版本的完整套件；三個中文或英文啟動器須形成完整的
         Windows（.bat）、macOS（.command）或雙平台組合，不能缺漏或混用。
       🔴 → 若上面某個檔案⛔ 不是框架放的，只是剛好同名，⇒ 那就是原因：
         先把它改名（或搬進 `my/`），再跑一次。""",
 "edition_found_none": "⛔ 一個也沒有（⇒ 這是盤點的結果，不是沒有盤點）",
 "edition_found_item": "{name}［{tag}］",
 "edition_found_join": "、",
 "edition_tag_zh": "中",
 "edition_tag_en": "英",
 "restore_receipt_failed": "[FAIL] 反向檢查點存在，但持久反向收據建立失敗：{err}。沒有還原任何檔案。",
 "restore_git_failed": "[FAIL] Git 無法還原 `{path}`（退出碼 {rc}）。反向收據為 `{undo}`。",
 "restore_verify_failed": "[FAIL] `{path}` 已寫入，但讀回內容不符合收據 `{rid}`；請用反向收據 `{undo}` 並停止操作。",
 "restore_done": "✅ 已從 `{rid}` 還原 `{path}`，且未移動 `reviewed`。反向收據：`{undo}`",
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
FRAMEWORK_DIRS = ("governance", "profiles", "prompts", "scripts", "docs")
# 🔴 **已退役的套件：曾經在可替換清單上，現在不在了。**
#    ⚠️ **為什麼需要這份清單：一個被移出 `FRAMEWORK_DIRS` 的資料夾，
#    在既有專案裡會變成孤兒——⛔ 內容永遠停在退役那一版，而⛔ 沒有任何東西會再碰它。**
#    🔴 **⛔ 升級工具不刪使用者的東西（憲章 §6.3），⚠️ 但它一定要說出來**——
#    **⛔ 一個沒有人知道的孤兒資料夾，與一個過期的框架文件完全一樣。**
#    格式：`目錄名: (退役版本, 內容去了哪裡)`。
RETIRED_DIRS = {"policy": ("v1.4.4", "governance")}
FRAMEWORK_FILES = ("儲存進度.bat", "儲存進度.command", "同步規則.bat", "同步規則.command", "檢查專案.bat", "檢查專案.command", "README.md", "SETUP.md", "INITIALIZE_PROMPT.md", "file_index.md",
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
NEVER_TOUCH = ("PROJECT.md", "第一個想法.md", "ledgers", "corpus", "corpus_md", "handoffs",
               "my", "NEXT_SESSION_MEMO.md", "governance_config.json")
VERSION_FILE = "_VERSION"
TRANSIENT_NAMES = {".DS_Store", "Thumbs.db"}
TRANSIENT_SUFFIXES = {".pyc", ".pyo"}
# 🔴 只有這一個「套件＋相對路徑」是框架產生的狀態檔。
#    ⛔ 不能只按檔名排除；專案可以在任何別處擁有同名檔案。
TRANSIENT_PACKAGE_PATHS = {("scripts", "harness/harness_status.json")}

RECEIPT_SCHEMA = 1
RECEIPT_REF_PREFIX = "refs/spark2groundwork/restore"
RECEIPT_GIT_PATH = "spark2groundwork/receipts"
RECEIPT_ID_RE = re.compile(r"^upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]{0,39}-[0-9a-f]{8}$")
CHECKPOINT_TOOL_API = "spark2groundwork-checkpoint-tool-v1"
EDITION_LAUNCHERS = {
    "zh": {
        "bat": ("查看變更.bat", "檢查更新.bat", "記錄快照.bat"),
        "command": ("查看變更.command", "檢查更新.command", "記錄快照.command"),
    },
    "en": {
        "bat": ("review_changes.bat", "check_update.bat", "snapshot.bat"),
        "command": ("review_changes.command", "check_update.command", "snapshot.command"),
    },
}


class ReceiptError(RuntimeError):
    """A durable receipt could not be created or did not pass integrity checks."""


class PreimageError(ReceiptError):
    """One or more files about to be overwritten are absent from the checkpoint."""

    def __init__(self, paths):
        self.paths = sorted(set(paths))
        super().__init__(", ".join(self.paths))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def _git(root, args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _checkpoint_program(root):
    """Select a compatible peer without executing candidates during the probe."""
    candidates = (pathlib.Path(__file__).resolve().with_name("checkpoint.py"),
                  root / "scripts/harness/checkpoint.py")
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not candidate.is_file():
            continue
        seen.add(resolved)
        try:
            if CHECKPOINT_TOOL_API in candidate.read_text(encoding="utf-8", errors="replace"):
                return candidate
        except OSError:
            continue
    return None


def _edition_fingerprint(root):
    """Return one proven edition, or a fail-closed diagnostic state."""
    present = {}
    complete = {}
    for edition, layouts in EDITION_LAUNCHERS.items():
        known = tuple(name for names in layouts.values() for name in names)
        present[edition] = any((root / name).is_file() for name in known)
        complete[edition] = any(all((root / name).is_file() for name in names)
                                for names in layouts.values())
    seen = [edition for edition, yes in present.items() if yes]
    proven = [edition for edition, yes in complete.items() if yes]
    if len(seen) > 1:
        return None, "mixed"
    if len(proven) == 1 and seen == proven:
        return proven[0], proven[0]
    return None, "missing/incomplete"


def _edition_launchers_found(root):
    """⛔ 只給失敗訊息用：這個目錄實際看得到哪幾個框架啟動器，各屬哪一版。

    ⚠️ **它⛔ 不參與判定**——判定仍然只在 `_edition_fingerprint` 裡。
    🔴 **⇒ 分開的理由：改「怎麼說明」⛔ 不得動到「怎麼決定」。**
    ⚠️ 名字順序照 `EDITION_LAUNCHERS` 的定義序，⇒ 兩個平台輸出相同。

    **觸發個案（發布前覆核，2026-09-03）：** 一個合法的中文專案自己有一個叫
    `snapshot.bat` 的檔案 ⇒ 被判 `mixed` 而整次拒絕，⛔ 而訊息只說「無法證明是
    同一語言版本」並要求重新下載套件——**⚠️ 而下載包從來不是原因。**
    """
    found = []
    for edition, layouts in EDITION_LAUNCHERS.items():
        for names in layouts.values():
            for name in names:
                if (root / name).is_file():
                    found.append((name, edition))
    return found


def _edition_found_text(root, MSG):
    found = _edition_launchers_found(root)
    if not found:
        return MSG["edition_found_none"]
    return MSG["edition_found_join"].join(
        MSG["edition_found_item"].format(name=name, tag=MSG["edition_tag_" + edition])
        for name, edition in found)


def _same_edition(root, src, MSG):
    project_edition, project_state = _edition_fingerprint(root)
    source_edition, source_state = _edition_fingerprint(src)
    if project_edition and project_edition == source_edition:
        return True
    print(MSG["edition_guard_failed"].format(
        source=source_state, project=project_state,
        src_found=_edition_found_text(src, MSG),
        root_found=_edition_found_text(root, MSG)))
    return False


def _git_input(root, args, value):
    # Binary stdin avoids Windows text-mode LF->CRLF translation. `git mktag`
    # strictly rejects CR bytes in object headers.
    p = subprocess.run(["git", "-C", str(root), *args], input=value.encode("utf-8"),
                       capture_output=True)
    p.stdout = (p.stdout or b"").decode("utf-8", errors="replace")
    p.stderr = (p.stderr or b"").decode("utf-8", errors="replace")
    return p


def _safe_rel(value):
    """Return a canonical repository-relative POSIX path, or reject it."""
    raw = str(value).replace("\\", "/")
    p = pathlib.PurePosixPath(raw)
    if (not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw)
            or any(ord(char) < 32 for char in raw)
            or any(part in ("", ".", "..") for part in p.parts)
            or raw != p.as_posix()):
        raise ReceiptError(f"unsafe repository-relative path: {value!r}")
    return p.as_posix()


def _under_target(path, target):
    return path == target or path.startswith(target.rstrip("/") + "/")


def _is_transient(package, rel, path=None):
    parts = pathlib.PurePosixPath(rel).parts
    name = parts[-1] if parts else ""
    suffix = pathlib.PurePosixPath(name).suffix
    return ("__pycache__" in parts or name in TRANSIENT_NAMES
            or suffix in TRANSIENT_SUFFIXES
            or (package, rel) in TRANSIENT_PACKAGE_PATHS)


def _receipt_store(root, create=False):
    p = _git(root, ["rev-parse", "--git-path", RECEIPT_GIT_PATH])
    if p.returncode != 0 or not (p.stdout or "").strip():
        raise ReceiptError((p.stderr or p.stdout or "cannot locate Git receipt store").strip())
    store = pathlib.Path(p.stdout.strip())
    if not store.is_absolute():
        store = root / store
    store = store.resolve()
    if create:
        store.mkdir(parents=True, exist_ok=True)
    return store


def _tree_entry(root, commit, rel):
    p = _git(root, ["ls-tree", "-z", commit, "--", rel])
    if p.returncode != 0:
        raise ReceiptError((p.stderr or "git ls-tree failed").strip())
    raw = p.stdout.rstrip("\0")
    if not raw:
        return None
    first = raw.split("\0", 1)[0]
    try:
        meta, found = first.split("\t", 1)
        mode, kind, blob = meta.split(" ", 2)
    except ValueError as e:
        raise ReceiptError(f"unreadable tree entry for {rel}") from e
    if found != rel:
        raise ReceiptError(f"tree path mismatch for {rel}")
    return {"mode": mode, "type": kind, "blob": blob}


def _index_entry(root, rel):
    p = _git(root, ["ls-files", "--stage", "-z", "--", rel])
    if p.returncode != 0:
        raise ReceiptError((p.stderr or "git ls-files failed").strip())
    rows = [row for row in p.stdout.split("\0") if row]
    if len(rows) != 1:
        return None
    try:
        meta, found = rows[0].split("\t", 1)
        mode, blob, stage = meta.split(" ", 2)
    except ValueError as e:
        raise ReceiptError(f"unreadable index entry for {rel}") from e
    if found != rel or stage != "0":
        return None
    return {"mode": mode, "blob": blob}


def _hash_worktree(root, path, rel):
    p = _git(root, ["hash-object", f"--path={rel}", "--", str(path)])
    if p.returncode != 0 or not (p.stdout or "").strip():
        raise ReceiptError((p.stderr or f"cannot hash {rel}").strip())
    return p.stdout.strip()


def _worktree_mode(root, path, checkpoint_mode):
    if path.is_symlink() or not path.is_file():
        return None
    # On Windows, or when core.filemode is false, executable bits are outside Git's
    # working-tree semantics. On POSIX with core.filemode enabled they must agree.
    p = _git(root, ["config", "--bool", "core.filemode"])
    filemode = p.returncode == 0 and (p.stdout or "").strip().lower() == "true"
    if os.name != "nt" and filemode:
        return "100755" if os.access(path, os.X_OK) else "100644"
    return checkpoint_mode


def _verified_entries(root, commit, paths):
    entries = []
    bad = []
    for rel in sorted(set(paths)):
        try:
            rel = _safe_rel(rel)
            path = root / pathlib.PurePosixPath(rel)
            if path.is_symlink() or not path.is_file():
                bad.append(rel)
                continue
            tracked = _git(root, ["ls-files", "--error-unmatch", "--", rel])
            tree = _tree_entry(root, commit, rel)
            index = _index_entry(root, rel)
            if (tracked.returncode != 0 or tree is None or tree["type"] != "blob"
                    or tree["mode"] not in ("100644", "100755") or index is None
                    or index["mode"] != tree["mode"] or index["blob"] != tree["blob"]
                    or _hash_worktree(root, path, rel) != tree["blob"]
                    or _worktree_mode(root, path, tree["mode"]) != tree["mode"]):
                bad.append(rel)
                continue
            entries.append({"path": rel, "blob": tree["blob"], "mode": tree["mode"]})
        except (OSError, ReceiptError):
            bad.append(rel)
    if bad:
        raise PreimageError(bad)
    return entries


def _preimage_paths(root, dst, source, target):
    """Return existing files that replacement will overwrite and transient omissions."""
    target = _safe_rel(target)
    if source.is_symlink() or (not source.is_file() and not source.is_dir()):
        raise PreimageError([target])
    if dst.is_symlink():
        raise PreimageError([target])
    if source.is_file():
        if dst.exists() and not dst.is_file():
            raise PreimageError([target])
        return ([target] if dst.is_file() else []), []
    if dst.exists() and not dst.is_dir():
        raise PreimageError([target])

    paths = []
    omitted = []
    if dst.is_dir():
        for p in sorted(dst.rglob("*"), key=lambda value: value.as_posix()):
            rel = p.relative_to(dst).as_posix()
            full_rel = f"{target}/{rel}"
            if _is_transient(target, rel, p):
                if p.is_file() or p.is_symlink():
                    omitted.append(full_rel)
                continue
            if p.is_symlink() or (not p.is_file() and not p.is_dir()):
                raise PreimageError([full_rel])
    for p in sorted(source.rglob("*"), key=lambda value: value.as_posix()):
        rel = p.relative_to(source).as_posix()
        full_rel = f"{target}/{rel}"
        if _is_transient(target, rel, p):
            continue
        if p.is_symlink() or (not p.is_file() and not p.is_dir()):
            raise PreimageError([full_rel])
        old = dst / pathlib.PurePosixPath(rel)
        if p.is_file() and old.exists():
            if old.is_symlink() or not old.is_file():
                raise PreimageError([full_rel])
            paths.append(full_rel)
        elif p.is_dir() and old.exists() and not old.is_dir():
            raise PreimageError([full_rel])
    return paths, sorted(set(omitted))


def _atomic_json(path, data):
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".receipt-",
                                         suffix=".tmp", delete=False) as f:
            tmp_name = f.name
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except OSError as e:
        if tmp_name:
            try:
                pathlib.Path(tmp_name).unlink()
            except OSError:
                pass
        raise ReceiptError(str(e)) from e


def _load_receipt(root, rid):
    if not RECEIPT_ID_RE.fullmatch(rid or ""):
        raise ReceiptError("invalid receipt id")
    expected_ref = f"{RECEIPT_REF_PREFIX}/{rid}"
    tagged = _git(root, ["cat-file", "-p", expected_ref])
    if tagged.returncode != 0:
        raise ReceiptError("durable ref is missing")
    try:
        header, message = tagged.stdout.split("\n\n", 1)
        tag_fields = dict(line.split(" ", 1) for line in header.splitlines()
                          if " " in line and not line.startswith("tagger "))
        authoritative = json.loads(message)
    except (ValueError, TypeError) as e:
        raise ReceiptError("private ref does not contain a receipt tag") from e
    if tag_fields.get("type") != "commit":
        raise ReceiptError("receipt tag does not point to a commit")
    path = _receipt_store(root) / f"{rid}.json"
    if path.exists():
        try:
            mirror = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise ReceiptError(str(e)) from e
        if mirror != authoritative:
            raise ReceiptError("manifest mirror differs from the Git-pinned receipt")
    data = authoritative
    if data.get("schema") != RECEIPT_SCHEMA or data.get("receipt_id") != rid:
        raise ReceiptError("schema or receipt id mismatch")
    ref = data.get("ref")
    commit = data.get("commit")
    if ref != expected_ref or not isinstance(commit, str):
        raise ReceiptError("invalid receipt ref or commit")
    if tag_fields.get("object") != commit:
        raise ReceiptError("receipt tag object and manifest commit differ")
    resolved = _git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if resolved.returncode != 0 or resolved.stdout.strip() != commit:
        raise ReceiptError("durable ref is missing or no longer matches")
    target = _safe_rel(data.get("target", ""))
    files = data.get("files")
    if not isinstance(files, list):
        raise ReceiptError("files is not a list")
    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ReceiptError("invalid file entry")
        rel = _safe_rel(entry.get("path", ""))
        if rel in seen or not _under_target(rel, target):
            raise ReceiptError(f"invalid or duplicate receipt path: {rel}")
        seen.add(rel)
        tree = _tree_entry(root, commit, rel)
        if (tree is None or tree["type"] != "blob"
                or entry.get("mode") != tree["mode"]
                or entry.get("blob") != tree["blob"]):
            raise ReceiptError(f"checkpoint tree mismatch: {rel}")
    omitted = data.get("omitted_transient", [])
    if not isinstance(omitted, list):
        raise ReceiptError("omitted_transient is not a list")
    for rel in omitted:
        rel = _safe_rel(rel)
        if not _under_target(rel, target):
            raise ReceiptError(f"transient path is outside target: {rel}")
        inner = rel[len(target):].lstrip("/")
        if not inner or not _is_transient(target, inner):
            raise ReceiptError(f"path is not an allowed transient: {rel}")
    return data


def _create_receipt(root, commit, target, paths, omitted, operation, target_existed):
    target = _safe_rel(target)
    entries = _verified_entries(root, commit, paths)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-")[:40] or "target"
    rid = f"upg-{stamp}-{slug}-{uuid.uuid4().hex[:8]}"
    ref = f"{RECEIPT_REF_PREFIX}/{rid}"
    reviewed = _git(root, ["rev-parse", "--verify", "refs/tags/reviewed^{commit}"])
    data = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": rid,
        "created_utc": now.isoformat().replace("+00:00", "Z"),
        "operation": operation,
        "target": target,
        "target_existed": bool(target_existed),
        "commit": commit,
        "ref": ref,
        "reviewed_before": reviewed.stdout.strip() if reviewed.returncode == 0 else None,
        "files": entries,
        "omitted_transient": sorted(set(_safe_rel(p) for p in omitted)),
    }
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    tag_text = (f"object {commit}\ntype commit\ntag {rid}\n"
                f"tagger Spark2Groundwork <receipt@local> {int(now.timestamp())} +0000\n\n"
                f"{canonical}\n")
    made_tag = _git_input(root, ["mktag"], tag_text)
    tag_oid = (made_tag.stdout or "").strip()
    if made_tag.returncode != 0 or not tag_oid:
        raise ReceiptError((made_tag.stderr or "could not pin receipt manifest").strip())
    made_ref = _git(root, ["update-ref", ref, tag_oid, ""])
    if made_ref.returncode != 0:
        raise ReceiptError((made_ref.stderr or "could not create durable ref").strip())
    path = None
    try:
        store = _receipt_store(root, create=True)
        path = store / f"{rid}.json"
        if path.exists():
            raise ReceiptError("receipt manifest already exists")
        _atomic_json(path, data)
        checked = _load_receipt(root, rid)
        if checked.get("receipt_id") != rid:
            raise ReceiptError("receipt read-back failed")
    except Exception as e:  # noqa: BLE001 -- rollback must cover filesystem failures too
        if path is not None and path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        _git(root, ["update-ref", "-d", ref, tag_oid])
        if isinstance(e, ReceiptError):
            raise
        raise ReceiptError(str(e)) from e
    return data


def _receipt_files(data):
    return {entry["path"]: entry for entry in data["files"]}


def _receipt_rows(root):
    try:
        store = _receipt_store(root)
    except ReceiptError:
        return [], []
    good, bad = [], []
    ids = set()
    if store.is_dir():
        for path in sorted(store.glob("*.json"), key=lambda value: value.as_posix()):
            if RECEIPT_ID_RE.fullmatch(path.stem):
                ids.add(path.stem)
            else:
                bad.append((path.name, "invalid receipt id"))
    refs = _git(root, ["for-each-ref", "--format=%(refname)", RECEIPT_REF_PREFIX + "/"])
    if refs.returncode == 0:
        for ref in refs.stdout.splitlines():
            rid = ref[len(RECEIPT_REF_PREFIX) + 1:] if ref.startswith(RECEIPT_REF_PREFIX + "/") else ""
            if RECEIPT_ID_RE.fullmatch(rid):
                ids.add(rid)
            else:
                bad.append((ref or "(empty ref)", "invalid receipt ref name"))
    for rid in sorted(ids):
        try:
            good.append(_load_receipt(root, rid))
        except ReceiptError as e:
            bad.append((f"{rid}.json", str(e)))
    good.sort(key=lambda row: (row.get("created_utc", ""), row["receipt_id"]), reverse=True)
    return good, bad


def _resolve_receipt(root, token):
    if token == "latest":
        rows, _ = _receipt_rows(root)
        return rows[0] if rows else None
    if not RECEIPT_ID_RE.fullmatch(token or ""):
        return None
    path = _receipt_store(root) / f"{token}.json"
    exists = _git(root, ["show-ref", "--verify", "--quiet",
                         f"{RECEIPT_REF_PREFIX}/{token}"])
    if exists.returncode != 0 and not path.is_file():
        return None
    return _load_receipt(root, token)


def _worktree_matches(root, entry):
    rel = entry["path"]
    path = root / pathlib.PurePosixPath(rel)
    if path.is_symlink() or not path.is_file():
        return False
    try:
        return (_hash_worktree(root, path, rel) == entry["blob"]
                and _worktree_mode(root, path, entry["mode"]) == entry["mode"])
    except ReceiptError:
        return False


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
    print(MSG["check_marker_warning"])
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
    print_retired(root, MSG)
    print(MSG["check_tail"])
    return 0



def retired_present(root):
    """回傳這個專案裡仍然存在的已退役資料夾。

    ⚠️ **判準是「資料夾存在」，⛔ 不是「裡面有沒有東西」**——
    🔴 **一個空的孤兒資料夾仍然會讓人以為框架還在維護它。**
    """
    return [(d, v, into) for d, (v, into) in sorted(RETIRED_DIRS.items())
            if (root / d).is_dir()]


def print_retired(root, MSG):
    """⛔ `check` 與 `diff` 都要印。⚠️ 只印在其中一條路徑上，另一條就是靜默的。"""
    rows = retired_present(root)
    if not rows:
        return
    print(MSG["retired_head"])
    for d, v, into in rows:
        print(MSG["retired_row"].format(d=d, v=v, into=into))
    print()

def pairs(root, src):
    for d in FRAMEWORK_DIRS:
        if (src / d).is_dir():
            yield d, root / d, src / d
    for f in FRAMEWORK_FILES:
        if (src / f).is_file():
            suffix = pathlib.PurePosixPath(f).suffix
            native = ".bat" if sys.platform == "win32" else (".command" if sys.platform == "darwin" else None)
            # 例行 diff 不把「目前不存在的外平台啟動器」列為待補項目；
            # 但 explicit apply 仍刻意接受 FRAMEWORK_FILES 裡的精確名稱，方便跨平台打包。
            if suffix in (".bat", ".command") and not (root / f).exists() and suffix != native:
                continue
            yield f, root / f, src / f


def target_only_files(cur, new, package):
    """列出會被整包替換刪除或改變類型的非暫存項目。"""
    if not cur.is_dir() or not new.is_dir():
        return []
    out = []
    for p in sorted(cur.rglob("*"), key=lambda value: value.as_posix()):
        rel = p.relative_to(cur)
        rel_text = rel.as_posix()
        if _is_transient(package, rel_text, p):
            continue
        peer = new / rel
        if p.is_symlink():
            out.append(rel_text)
        elif p.is_file() and (not peer.is_file() or peer.is_symlink()):
            out.append(rel_text)
        elif p.is_dir() and (not peer.is_dir() or peer.is_symlink()):
            out.append(rel_text.rstrip("/") + "/")
        elif not p.is_file() and not p.is_dir():
            out.append(rel_text)
    return sorted(out)


def cmd_diff(root, src, MSG):
    changed = []
    for name, cur, new in pairs(root, src):
        if new.is_file():
            same = cur.is_file() and sha(cur) == sha(new)
            if not same:
                changed.append((name, 1, 0 if cur.is_file() else 1, 0, []))
            continue
        n_mod = n_new = 0
        for np in sorted(new.rglob("*"), key=lambda p: p.as_posix()):
            if not np.is_file() or VERSION_FILE == np.name:
                continue
            rel = np.relative_to(new)
            cp = cur / rel
            if not cp.is_file():
                n_new += 1
            elif sha(cp) != sha(np):
                n_mod += 1
        only = target_only_files(cur, new, name)
        if n_mod or n_new or only:
            changed.append((name, n_mod, n_new, len(only), only))
    if not changed:
        print(MSG["diff_none"])
        print_retired(root, MSG)
        return 0
    print(MSG["diff_head"])
    for name, m, n, o, only in changed:
        print(MSG["diff_row"].format(name=name, m=m, n=n, o=o))
        for path in only:
            print(MSG["target_only_row"].format(path=f"{name}/{path}"))
    print()
    print_retired(root, MSG)
    print(MSG["diff_tail"])
    return 0


def cmd_receipts(root, MSG):
    rows, bad = _receipt_rows(root)
    if rows:
        print(MSG["receipts_head"])
        for row in rows:
            print(MSG["receipts_row"].format(
                rid=row["receipt_id"], created=row.get("created_utc", "?"),
                operation=row.get("operation", "?"), target=row["target"]))
    else:
        print(MSG["receipts_empty"])
    for name, err in bad:
        print(MSG["receipts_bad"].format(name=name, err=err))
    return 0


def _current_paths(root, target):
    base = root / pathlib.PurePosixPath(target)
    if base.is_symlink():
        return [target]
    if base.is_file():
        return [target]
    if not base.is_dir():
        return []
    out = []
    for path in sorted(base.rglob("*"), key=lambda value: value.as_posix()):
        rel = path.relative_to(base).as_posix()
        if _is_transient(target, rel, path):
            continue
        if path.is_file() or path.is_symlink():
            out.append(f"{target}/{rel}")
    return out


def cmd_receipt_diff(root, token, path_arg, MSG):
    if not token:
        print(MSG["receipt_needs_id"]); return 1
    try:
        data = _resolve_receipt(root, token)
    except ReceiptError as e:
        print(MSG["receipt_invalid"].format(rid=token, err=e)); return 2
    if data is None:
        print(MSG["receipt_unknown"].format(rid=token)); return 1
    rid = data["receipt_id"]
    target = data["target"]
    files = _receipt_files(data)
    try:
        shown = _safe_rel(path_arg) if path_arg else target
    except ReceiptError:
        print(MSG["receipt_path_bad"].format(path=path_arg, target=target)); return 1
    if not _under_target(shown, target):
        print(MSG["receipt_path_bad"].format(path=shown, target=target)); return 1
    if path_arg and shown not in files:
        print(MSG["receipt_path_not_saved"].format(path=shown, rid=rid)); return 1

    p = _git(root, ["diff", "--no-ext-diff", "--no-renames", "--no-color",
                    data["ref"], "--", shown])
    if p.returncode != 0:
        print(MSG["receipt_invalid"].format(
            rid=rid, err=(p.stderr or "git diff failed").strip())); return 2
    print(MSG["receipt_diff_head"].format(rid=rid, path=shown))
    if p.stdout:
        print(p.stdout, end="" if p.stdout.endswith("\n") else "\n")
    saved = set(files)
    new_paths = [] if path_arg else sorted(set(_current_paths(root, target)) - saved)
    if new_paths:
        print(MSG["receipt_new_head"])
        for rel in new_paths:
            print(MSG["receipt_new_row"].format(path=rel))
    if not p.stdout and not new_paths:
        print(MSG["receipt_no_diff"])
    return 0


def cmd_restore(root, token, path_arg, MSG):
    if not token:
        print(MSG["receipt_needs_id"]); return 1
    if not path_arg:
        print(MSG["restore_needs_path"]); return 1
    try:
        data = _resolve_receipt(root, token)
    except ReceiptError as e:
        print(MSG["receipt_invalid"].format(rid=token, err=e)); return 2
    if data is None:
        print(MSG["receipt_unknown"].format(rid=token)); return 1
    rid = data["receipt_id"]
    try:
        rel = _safe_rel(path_arg)
    except ReceiptError:
        print(MSG["receipt_path_bad"].format(path=path_arg, target=data["target"])); return 1
    if not _under_target(rel, data["target"]):
        print(MSG["receipt_path_bad"].format(path=rel, target=data["target"])); return 1
    entry = _receipt_files(data).get(rel)
    if entry is None:
        print(MSG["receipt_path_not_saved"].format(path=rel, rid=rid)); return 1
    current = root / pathlib.PurePosixPath(rel)
    if current.is_symlink() or not current.is_file():
        print(MSG["restore_current_missing"].format(path=rel)); return 1
    if _worktree_matches(root, entry):
        print(MSG["restore_noop"].format(path=rel, rid=rid)); return 0

    print(MSG["restore_cp_first"])
    checkpoint_program = _checkpoint_program(root)
    if checkpoint_program is None:
        print(MSG["checkpoint_peer_missing"]); return 2
    rc = subprocess.run([sys.executable, "-B", str(checkpoint_program),
                         "--root", str(root), "--mode", "tool",
                         "--tool-id", "upgrade",
                         "--operation", f"restore-{pathlib.PurePosixPath(rel).name}"]).returncode
    if rc != 0:
        print(MSG["restore_cp_failed"].format(rc=rc)); return 2
    p = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    undo_commit = (p.stdout or "").strip()
    if p.returncode != 0 or len(undo_commit) < 7:
        print(MSG["restore_receipt_failed"].format(err="cannot read undo checkpoint")); return 2
    try:
        undo = _create_receipt(root, undo_commit, rel, [rel], [],
                               "restore-undo", True)
    except ReceiptError as e:
        print(MSG["restore_receipt_failed"].format(err=e)); return 2
    undo_id = undo["receipt_id"]

    restored = _git(root, ["restore", f"--source={data['ref']}", "--worktree", "--", rel])
    if restored.returncode != 0:
        print(MSG["restore_git_failed"].format(path=rel, rc=restored.returncode,
                                                undo=undo_id)); return 2
    if not _worktree_matches(root, entry):
        print(MSG["restore_verify_failed"].format(path=rel, rid=rid, undo=undo_id)); return 2
    print(MSG["restore_done"].format(path=rel, rid=rid, undo=undo_id))
    return 0

def cmd_apply(root, src, target, MSG):
    if target in RETIRED_DIRS:
        v, into = RETIRED_DIRS[target]
        print(MSG["retired_target"].format(t=target, v=v, into=into)); return 1
    if target in NEVER_TOUCH:
        print(MSG["never"].format(t=target)); return 1
    if target not in FRAMEWORK_DIRS and target not in FRAMEWORK_FILES:
        print(MSG["not_framework"].format(t=target,
              ok=" ".join(FRAMEWORK_DIRS + FRAMEWORK_FILES))); return 1
    s = src / target
    if not s.exists():
        print(MSG["missing_in_upgrade"].format(t=target, src=src)); return 1
    if not _same_edition(root, src, MSG):
        return 1

    dst = root / target
    only = target_only_files(dst, s, target)
    if only:
        print(MSG["target_only_block"].format(t=target))
        for path in only:
            print(MSG["target_only_row"].format(path=f"{target}/{path}"))
        return 1

    # ⛔ R-33 的位置：檢查點失敗 ⛔ 不得往下覆蓋。
    print(MSG["cp_first"])
    # 🔴 **必須明確傳 `--mode tool`。**
    #    ⚠️ **v1.4.1 與 v1.4.2 這裡沒有傳，於是走 human 預設——
    #    一次升級就把 `reviewed` 標籤移到升級前的提交並印「我看過了」。**
    #    **⇒ 使用者「還沒審閱」的 AI 工作，因為升級而從待審清單消失。**
    # 執行中升級器的同目錄 peer 優先；只有相容的專案內版本才可後備。
    # 相容性只讀精確 API 標記，不執行候選程式，避免探測本身先寫入。
    checkpoint_program = _checkpoint_program(root)
    if checkpoint_program is None:
        print(MSG["checkpoint_peer_missing"]); return 2
    rc = subprocess.run([sys.executable, "-B", str(checkpoint_program),
                         "--root", str(root), "--mode", "tool",
                         "--tool-id", "upgrade",
                         "--operation", f"apply-{target}"]).returncode
    if rc != 0:
        print(MSG["cp_failed"].format(rc=rc)); return 2

    # 🔴 **收據：檢查點存在哪一個提交上，⛔ 必須在覆蓋之前就拿到手。**
    #    ⚠️ **反例（Codex，2026-09-02，Windows）：升級確實建立了 tool 檢查點，
    #    ⛔ 而完成訊息叫使用者用「查看變更」把手動改動找回來——
    #    那支工具固定以 `reviewed` 為基準，而 tool 模式刻意不動 `reviewed`。**
    #    🔴 **⇒ 手動改動的 pre-image 明明還在，卻落在官方復原介面的視野之外。**
    #    **`git diff reviewed` 是 0 行，`git diff HEAD` 是 193 行——同一個檔案。**
    #
    #    ⚠️ **為什麼讀 `HEAD` 就夠：`checkpoint.py` 剛剛 `git add -A` 並提交，
    #    所以 `HEAD` 的樹就是覆蓋前的工作區。**
    #    **⛔ 而若剛好「沒有事情要做」（工作區本來就乾淨），`HEAD` 仍然是同一份內容。**
    #
    #    🔴 **⛔ 讀不到就不覆蓋**——**一個說不出還原點在哪的還原點，不是還原點。**
    p = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    cp = (p.stdout or "").strip()
    if p.returncode != 0 or len(cp) < 7:
        print(MSG["no_receipt"].format(rc=p.returncode)); return 2
    try:
        paths, omitted = _preimage_paths(root, dst, s, target)
        receipt = _create_receipt(root, cp, target, paths, omitted,
                                  f"apply-{target}", dst.exists() or dst.is_symlink())
    except PreimageError as e:
        rows = "\n".join(f"       ⛔ {path}" for path in e.paths)
        print(MSG["receipt_unprotected"].format(paths=rows)); return 2
    except ReceiptError as e:
        print(MSG["receipt_create_failed"].format(err=e)); return 2

    # 關閉「檢查後、使用前」的時間縫隙：收據建立後到替換前，不得有檔案改變或出現。
    try:
        paths_now, omitted_now = _preimage_paths(root, dst, s, target)
        if (sorted(paths_now) != sorted(entry["path"] for entry in receipt["files"])
                or sorted(omitted_now) != sorted(receipt["omitted_transient"])
                or target_only_files(dst, s, target)):
            raise PreimageError(sorted(set(paths_now) ^
                                       {entry["path"] for entry in receipt["files"]})
                                or [target])
        _verified_entries(root, cp, paths_now)
    except PreimageError as e:
        rows = "\n".join(f"       ⛔ {path}" for path in e.paths)
        print(MSG["receipt_unprotected"].format(paths=rows)); return 2
    except ReceiptError as e:
        print(MSG["receipt_create_failed"].format(err=e)); return 2

    if s.is_dir():
        if dst.is_dir():
            shutil.rmtree(dst)
        shutil.copytree(s, dst)
    else:
        shutil.copy2(s, dst)
    print(MSG["applied"].format(t=target))
    print(MSG["receipt"].format(rid=receipt["receipt_id"], cp=cp, target=target))
    print(MSG["applied_tail"].format(rid=receipt["receipt_id"]))
    # ⚠️ **也印在這裡，⛔ 而不是只印在 `check`／`diff`。**
    #    🔴 **理由：退役提示只存在於新版程式裡，而使用者是用舊版程式跑 `diff` 的**——
    #    **⇒ 他能看到這則訊息的最早時機，就是換完 `scripts` 的這一刻。**
    print_retired(root, MSG)
    return 0


def main(MSG):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("action", nargs="?", default="check",
                    choices=("check", "diff", "apply", "receipts", "receipt-diff", "restore"))
    ap.add_argument("target", nargs="?", default=None)
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(MSG["usage"]); return 0
    if ((a.action in ("check", "diff", "receipts") and (a.target or a.path))
            or (a.action == "apply" and a.path)):
        ap.error("too many arguments for this action")
    root = pathlib.Path(a.root).resolve() if a.root else \
        pathlib.Path(__file__).resolve().parents[2]
    if not (root / "governance/AGENTS.md").is_file():
        print(MSG["wrong_folder"].format(root=root)); return 1

    print("=" * 46); print(MSG["title"]); print("=" * 46); print()
    if a.action == "check":
        return cmd_check(root, MSG)
    if a.action == "receipts":
        return cmd_receipts(root, MSG)
    if a.action == "receipt-diff":
        return cmd_receipt_diff(root, a.target, a.path, MSG)
    if a.action == "restore":
        return cmd_restore(root, a.target, a.path, MSG)

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
