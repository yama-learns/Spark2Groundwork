#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：T0 唯一性與寫入範圍

## 兩項檢查

    T0_DUPLICATE_IN_SUBDIR          子資料夾出現與 T0 同名的檔案            FAIL
    WRITE_TO_DENIED_PATH            變更落在 deny 禁區內                    FAIL
    WRITE_OUT_OF_SCOPE              變更落在宣告範圍之外                    FAIL
    DENIED_PATH_TOUCHED_UNATTRIBUTED 單人專案變更落在 deny 禁區             WARN
    TRACKED_HIDDEN_FLAGS_PRESENT    已追蹤檔案帶有 assume-unchanged/skip-worktree INCOMPLETE
    CONFIGURATION_CONFLICT          deny 與 excluded_dirs 配置衝突          INCOMPLETE
    IGNORED_DENIED_PATH_PRESENT     .gitignore 忽略檔案落在 deny 禁區       INCOMPLETE
    IGNORED_OUT_OF_SCOPE_PRESENT    .gitignore 忽略檔案落在宣告範圍外       INCOMPLETE
    SCOPE_UNCHECKABLE               git 查核失敗或輸出不完整                INCOMPLETE

⚠️ **T0 唯一性為什麼是 FAIL 而非 WARN：**
**改一份漏其餘，而每一份單獨讀起來都正常。** 這是「修一層漏另一層」家族最難察覺的形態。

⚠️ **單 agent 專案請把 `write_scopes` 留空**——感測器會明說「本項不適用」，
**而不是靜默通過**。

## 五個踩過的坑（**都寫在這裡是因為它們會再發生**）

1. `git rev-parse --show-toplevel` 必須等於專案根目錄。
   否則當專案位於另一個 repo 之內時，**會對著錯誤的 repo 回報，而且語氣非常肯定**。
2. `git -c core.quotepath=false`。否則非 ASCII 路徑會印成八進位轉義，
   **「哪個檔案改了」這個唯一需要讀的欄位會變成一串數字。**
3. 基準必須以 `reviewed` 標籤為唯一錨點，走訪 `reviewed..HEAD` 逐次 commit 之觸及聯集，
   加上工作樹變更。不能只看工作樹 status 或淨差（否則提交後或改後還原即失去紀錄）。
   若缺 `reviewed` 或非祖先，fail-closed 報 INCOMPLETE，絕不退回 HEAD 或假造 PASS。
4. 路徑解析必須依 Git `-z` NUL 格式，rename/copy 兩端均納入觸及集合；
   子目錄專案只將屬於本子樹的前綴路徑納入，跨邊界改名仍正確處理界內端點。
5. 隱藏旗標（assume-unchanged/skip-worktree）與 .gitignore 忽略檔案遮蔽改動時，
   無法證明是否本輪改動，一律 fail-closed 報 INCOMPLETE，絕不靜默 PASS。

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
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
    """取子行程的 stdout，⛔ 保證回傳字串。

    🔴 **實測個案（2026-08-27，繁體中文 Windows、Python 3.14.2，主持人的機器）：**
    `_run_git(..., capture_output=True, text=True)` 回傳 `returncode == 0`
    **而 `stdout` 是 `None`。**

    ## 原因（**主持人跑了一行診斷才確定的，⛔ 不是推測**）

    ```
    UnicodeDecodeError: 'cp950' codec can't decode byte 0x94 in position 16
      File ".../subprocess.py", line 1613, in _readerthread
        buffer.append(fh.read())
    ```

    **`text=True` 而⛔ 沒有指定 `encoding`，Python 就用系統地區編碼解子行程的輸出。**
    **繁體中文 Windows 的地區編碼是 `cp950`，而 git 印的路徑是 UTF-8——
    `輔` 的第三個位元組是 `0x94`，cp950 解不了。**

    🔴 **⛔ 最糟的不是它會失敗，是它失敗的方式：**
    **解碼發生在 `subprocess` 的讀取執行緒裡。⚠️ 那個執行緒死掉，例外⛔ 不會傳到主執行緒，
    `communicate()` 回傳 `None`——於是主程式看到的是「exit 0，而且沒有輸出」。**
    **⛔ 「成功但沒東西」與「成功且真的沒東西」在這裡長得一模一樣。**

    ## ⚠️ 這是同一個修法只做了一半

    **`checkpoint.py` 與 `review_changes.py` 的 `run()` 逐字寫著
    `encoding="utf-8", errors="replace"`——⛔ 而本檔沒有。**
    🔴 **修法早就存在於同一個資料夾裡的兩支程式中，只是沒有被套到第三支。**

    ⚠️ **也是 `R-34` 的形狀：`_common._force_utf8()` 修的是「我們自己的輸出」，
    ⛔ 而它被當成「編碼問題都處理過了」。⛔ 一個為真的修正，效力範圍不涵蓋這一條通道。**

    ## 本函式的職責

    **即使加了 `encoding`，⛔ 仍然保留這個防線：**
    **⛔ 任何時候 `stdout` 不是字串，都要變成一個可讀的 INCOMPLETE，⛔ 不是崩潰、⛔ 不是通過。**

    ⚠️ **這個缺陷從 v1.0.0 起就在，⛔ 而它到 v1.4.1 才第一次現形**——
    🔴 **因為舊版在 `write_scopes` 為空時整段跳過，而單人專案一律留空。
    ⛔ 那段程式碼在任何真實使用者的機器上從來沒有執行過。**
    **⇒ D2 ⛔ 不是造成這個崩潰的原因，它是讓它現形的原因。**
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
    """檢查專案子樹內的已追蹤檔案是否帶有 assume-unchanged (h) 或 skip-worktree (S/s) 隱藏旗標。

    回傳 (flagged_list, error_message)。
    flagged_list 為 [("路徑", "旗標類型"), ...]
    """
    try:
        proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                         "ls-files", "-v", "-z", "--", "."],
                        capture_output=True, timeout=20)
        if proc.returncode != 0:
            return None, ("`git ls-files -v` 執行失敗"
                          f"（exit {proc.returncode}；stderr {(_text_err(proc) or '空')[:120]}）"
                          "——**⛔ 未檢查 ≠ 通過**")
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
        return None, f"git 旗標檢查無法執行：{e}"


def git_ignored(root):
    """取得專案子樹內被 .gitignore 忽略之所有未追蹤檔案清單。

    回傳 (ignored_paths_list, error_message)。
    """
    try:
        proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                         "ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--", "."],
                        capture_output=True, timeout=20)
        if proc.returncode != 0:
            return None, ("`git ls-files --ignored` 執行失敗"
                          f"（exit {proc.returncode}；stderr {(_text_err(proc) or '空')[:120]}）"
                          "——**⛔ 未檢查 ≠ 通過**")
        tokens = _nul_tokens(proc.stdout)
        paths = [_git_path(t) for t in tokens if t]
        return paths, None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return None, f"git 忽略檔案檢查無法執行：{e}"


def git_changed(root):
    """取得自 reviewed 基準至 HEAD 的歷史觸及檔案與工作樹變更之聯集。

    回傳 (paths_list, error_message)。
    若查核失敗或無法確定，paths_list 為 None，error_message 包含明確說明。
    """
    try:
        top = _run_git(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20)
        if top.returncode != 0:
            return None, "尚未建立版本控制"
        out = _text(top).strip()
        if not out:
            # ⛔ 「git 說成功但沒給我東西」⛔ 不得往下走。
            #    ⚠️ 往下走的話 `pathlib.Path("")` 會變成當前目錄，
            #    **於是它會回報「專案位於另一個 repo 之內」——一個看起來合理、而且是錯的診斷。**
            return None, ("git 回報成功（exit 0），⛔ 而它沒有輸出任何東西"
                          f"——**⛔ 這不是通過，是查不了。**"
                          f"（stdout 型別 {type(top.stdout).__name__}；"
                          f"stderr {(_text_err(top) or '空')[:120]}）")
        # 🔴 **專案位於 repo 的子目錄時，限縮到本專案子樹（v1.4.1）。**
        top_path, root_r = pathlib.Path(out).resolve(), root.resolve()
        prefix = ""
        if top_path != root_r:
            try:
                prefix = root_r.relative_to(top_path).as_posix()
            except ValueError:
                # ⛔ git 說的 repo 根目錄不包含本專案——這才是真的該拒絕回報。
                return None, ("git 回報的 repo 根目錄⛔ 不包含本專案"
                              "——**拒絕回報，以免對著錯誤的 repo 下判定**")

        # 1. 驗證 reviewed 標籤存在（V145-E2）
        rev_tag = _run_git(["git", "-C", str(root), "rev-parse", "--verify", "reviewed^{commit}"],
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=20)
        if rev_tag.returncode != 0:
            return None, ("reviewed 基準不存在（未建立已閱標籤）"
                          "——**⛔ 未檢查 ≠ 通過**")

        # 2. 驗證 reviewed 標籤為 HEAD 的祖先（V145-E2）
        anc = _run_git(["git", "-C", str(root), "merge-base", "--is-ancestor", "reviewed", "HEAD"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20)
        if anc.returncode != 0:
            return None, ("reviewed 基準不是 HEAD 的祖先（歷史分歧或未閱）"
                          "——**⛔ 未檢查 ≠ 通過**")

        candidate_paths = []

        # 3. 走訪 reviewed..HEAD 之逐次 commit 觸及（歷史聯集，非淨差；含 merge commit）
        rev_list = _run_git(["git", "-C", str(root), "rev-list", "reviewed..HEAD"],
                                  capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=30)
        if rev_list.returncode != 0:
            return None, ("git rev-list 執行失敗"
                          f"（exit {rev_list.returncode}；stderr {(_text_err(rev_list) or '空')[:120]}）"
                          "——**⛔ 未檢查 ≠ 通過**")
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
                return None, ("git diff-tree 執行失敗"
                              f"（exit {diff_tree.returncode}；stderr {(_text_err(diff_tree) or '空')[:120]}）"
                              "——**⛔ 未檢查 ≠ 通過**")
            candidate_paths.extend(_parse_history(diff_tree.stdout))

        # 4. 走訪工作樹變更（staged、unstaged、untracked）
        status_proc = _run_git(["git", "-C", str(root), "-c", "core.quotepath=false",
                                      "status", "--porcelain", "-z", "-uall"],
                                     capture_output=True, timeout=20)
        if status_proc.returncode != 0:
            return None, ("`git status` 沒有給出可讀的輸出"
                          f"（exit {status_proc.returncode}；stderr {(_text_err(status_proc) or '空')[:120]}）"
                          "——**⛔ 未檢查 ≠ 通過**")
        candidate_paths.extend(_parse_status(status_proc.stdout))

        # 5. 子目錄邊界前綴篩選
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
        return None, f"git 無法執行：{e}"


def main():
    root, cfg, as_json, name = cli("scope_and_t0")
    findings = []

    # ① T0 唯一性
    t0_names = {pathlib.Path(t).name for t in cfg["t0_docs"]}
    t0_paths = {(root / t).resolve() for t in cfg["t0_docs"]}
    for p in root.rglob("*.md"):
        if excluded(p, root, cfg) or p.resolve() in t0_paths:
            continue
        if p.name in t0_names:
            findings.append(("FAIL", "T0_DUPLICATE_IN_SUBDIR",
                             f"{p.relative_to(root)} — T0 全專案各只有一份。"
                             "**改一份漏其餘，而每一份單獨讀起來都正常**"))

    # ② 寫入範圍
    #
    # 🔴 **v1.4.1 起，本項⛔ 不再取決於 `write_scopes` 有沒有設。**
    # ⚠️ **舊版：`write_scopes` 為空就整段跳過，⛔ 連 `deny` 一起跳過。**
    #    **而 `profiles/PROFILE_solo.md` §6 要求單人專案把它留空——
    #    🔴 於是每一個單人專案的 `deny` 都不生效，而單人是預設情境。**
    #    ⛔ **後果：憲章 §6.3 的「清空 `deny` 就是完整授權」，在單人專案裡
    #    清空前後都一樣**——**那句話描述的是一個沒有在運作的機制。**
    scopes = cfg.get("write_scopes") or {}
    stats = {"T0 份數": len(cfg["t0_docs"])}

    # 🔴 **`deny` 就是 `deny`，⛔ 不在這裡追加任何東西（v1.4.1）。**
    # ⚠️ **舊版把 `t0_docs` 無條件併進來，於是設定關不掉 T0 的保護——
    #    而 `framework_config.py` 的註解同時寫著「T0 刻意不列在 deny，治理 Agent 可以維護它們」。**
    #    🔴 **同一個人寫的兩段註解，意圖相反：`deny` 裡「沒有 T0」是一個空缺，
    #    而空缺本身不帶意圖，於是兩處各自賦予了它相反的意思。**
    # ✅ **現在 T0 逐字列在 `deny` 的預設值裡。⚠️ 那⛔ 不是「同一條規則寫兩遍」——
    #    `t0_docs` 講的是「T0 全專案只有一份」，`deny` 講的是「誰可以寫」。⛔ 兩個不同的事實。**
    denied = [d.rstrip("/") for d in cfg.get("deny", [])]

    def under(path, tops):
        return any(path == a or path.startswith(a + "/") for a in tops)

    changed, err = git_changed(root)
    if changed is None:
        findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                         f"{err}——**本項未檢查，這不等於通過**"))
    else:
        stats["本輪變更"] = len(changed)
        stats["deny 範圍"] = len(denied)
        hits = [c for c in changed if under(c, denied)]

        if scopes:
            allowed = [a.rstrip("/") for v in scopes.values() for a in v]
            # ⚠️ `_human` 不是角色，是例外。**⛔ 被豁免的筆數必須被印出來。**
            #    ⚠️ **它在 v1.6.0 的權限表裡會被移除，改為「歸屬不明」而非靜默豁免。**
            human = [h.rstrip("/") for h in scopes.get("_human", [])]
            exempted = 0
            for c in changed:
                if under(c, denied):
                    if under(c, human):
                        exempted += 1
                        continue
                    findings.append(("FAIL", "WRITE_TO_DENIED_PATH",
                                     f"{c} 落在 deny 範圍內——**⛔ 任何 AI 角色皆不得寫**"
                                     f"（憲章 §6 通則 2）"))
                    continue
                if not under(c, allowed):
                    findings.append(("FAIL", "WRITE_OUT_OF_SCOPE",
                                     f"{c} 不在任何角色的宣告範圍內"))
            if exempted:
                stats["⚠️ 經 _human 豁免的 deny 命中"] = (
                    f"{exempted} 筆——**豁免不是沒有發生，只是判定為人做的**")
        else:
            # 🔴 **單人專案：沒有角色宣告，`git status` 也分不出人與 AI。**
            # ⛔ **⛔ 不判 FAIL**：主持人本人改台帳是完全正常的，
            #    **而一個對正確行為報警的判準會教人關掉整套感測器（`R-19`）。**
            # ⛔ **也⛔ 不靜默**：那是「靜默過濾」家族（`R-22`）。
            # → **列出來，讓人自己認領。**
            stats["寫入範圍"] = ("未設定 write_scopes（單人情境）："
                                 "⛔ 本輪不判越界，只列出落在 deny 範圍內的變更")
            if hits:
                findings.append(("WARN", "DENIED_PATH_TOUCHED_UNATTRIBUTED",
                                 f"本輪有 {len(hits)} 筆變更落在 AI 的預設禁區："
                                 + "、".join(hits[:8])
                                 + ("…" if len(hits) > 8 else "")
                                 + "——**⚠️ 若那是你自己改的，這是正常的；"
                                   "若不是，請看這份清單**"))

        # ③ 隱藏旗標檢查（V145-E2b：assume-unchanged 與 skip-worktree）
        flagged, ferr = git_hidden_flags(root)
        if ferr:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{ferr}——**本項未檢查，這不等於通過**"))
        elif flagged:
            flag_details = [f"{p} ({t})" for p, t in flagged]
            findings.append(("INCOMPLETE", "TRACKED_HIDDEN_FLAGS_PRESENT",
                             f"發現 {len(flagged)} 個已追蹤檔案帶有隱藏旗標（assume-unchanged 或 skip-worktree）："
                             + "、".join(flag_details[:8])
                             + ("…" if len(flag_details) > 8 else "")
                             + "——**⛔ 隱藏旗標會遮蔽工作樹改動，審核無法驗證改動狀態，拒絕評估**"))

        # ④ 配置衝突與忽略檔案檢查（V145-E2b：.gitignore 與 excluded_dirs）
        # 4.1 配置衝突：deny 禁區與 excluded_dirs 排除清單重疊
        cfg_excluded = set(cfg.get("excluded_dirs", []))
        conflicts = [d for d in denied if (set(pathlib.PurePosixPath(d).parts) & cfg_excluded)] + \
                    [e for e in cfg_excluded if under(e, denied)]
        conflicts = sorted(set(conflicts))
        if conflicts:
            findings.append(("INCOMPLETE", "CONFIGURATION_CONFLICT",
                             f"deny 禁區路徑與 excluded_dirs 排除清單發生衝突（{', '.join(conflicts)}）——"
                             "**⛔ 禁區不可被排除目錄靜默吞掉，請修正 framework_config.py**"))

        # 4.2 忽略檔案檢查
        ignored_files, ierr = git_ignored(root)
        if ierr:
            findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                             f"{ierr}——**本項未檢查，這不等於通過**"))
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

                # 明確 deny 與排除重疊時不得用排除規則吞掉 deny
                if is_denied:
                    if is_excl and not conflicts:
                        findings.append(("INCOMPLETE", "CONFIGURATION_CONFLICT",
                                         f"檔案 `{ig}` 同時落在 deny 禁區與 excluded_dirs 排除範圍內——"
                                         "**⛔ 禁區不可被排除目錄靜默吞掉，請修正 framework_config.py**"))
                    else:
                        denied_ignored.append(ig)
                elif is_excl:
                    # 既有快取與框架排除項（非 deny）維持安靜放行
                    continue
                else:
                    # 非排除目錄之普通 ignored 檔案：
                    if scopes:
                        # 多角色模式：落在宣告範圍外則不放行
                        if not under(ig, allowed):
                            out_of_scope_ignored.append(ig)
                    else:
                        # 單人模式：普通研究附件放行（不誤報）
                        pass

            stats["ignored generated metadata excluded"] = len(generated_metadata)

            if denied_ignored:
                findings.append(("INCOMPLETE", "IGNORED_DENIED_PATH_PRESENT",
                                 f"發現 {len(denied_ignored)} 個被 .gitignore 忽略的檔案落在 deny 禁區內："
                                 + "、".join(denied_ignored[:8])
                                 + ("…" if len(denied_ignored) > 8 else "")
                                 + "——**⛔ 禁區內存在忽略檔案，無法證明是否本輪改動，審核無法放行**"))

            if out_of_scope_ignored:
                findings.append(("INCOMPLETE", "IGNORED_OUT_OF_SCOPE_PRESENT",
                                 f"發現 {len(out_of_scope_ignored)} 個被 .gitignore 忽略的檔案落在所有角色宣告範圍之外："
                                 + "、".join(out_of_scope_ignored[:8])
                                 + ("…" if len(out_of_scope_ignored) > 8 else "")
                                 + "——**⛔ 範圍外存在忽略檔案，無法證明是否本輪改動，審核無法放行**"))

    if any(f[1] in ("IGNORED_DENIED_PATH_PRESENT", "IGNORED_OUT_OF_SCOPE_PRESENT") for f in findings):
        findings = [(level, code, message + ' 請AI先列出這些路徑並說明；經你同意後，將受保護的研究檔案納入本機版本追蹤（不會因此上傳），或把刻意不追蹤的資料移至保護範圍外並更新引用。不要刪除研究資料或只推進reviewed來消除提示。' if code in ("IGNORED_DENIED_PATH_PRESENT", "IGNORED_OUT_OF_SCOPE_PRESENT") else message) for level, code, message in findings]

    return emit("範圍與 T0 感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
