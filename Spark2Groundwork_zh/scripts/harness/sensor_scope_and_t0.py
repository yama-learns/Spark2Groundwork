#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：T0 唯一性與寫入範圍

## 兩項檢查

    T0_DUPLICATE_IN_SUBDIR   子資料夾出現與 T0 同名的檔案            FAIL
    WRITE_OUT_OF_SCOPE       本輪變更落在宣告範圍之外                FAIL

⚠️ **T0 唯一性為什麼是 FAIL 而非 WARN：**
**改一份漏其餘，而每一份單獨讀起來都正常。** 這是「修一層漏另一層」家族最難察覺的形態。

⚠️ **單 agent 專案請把 `write_scopes` 留空**——感測器會明說「本項不適用」，
**而不是靜默通過**。

## 兩個踩過的坑（**都寫在這裡是因為它們會再發生**）

1. `git rev-parse --show-toplevel` 必須等於專案根目錄。
   否則當專案位於另一個 repo 之內時，**會對著錯誤的 repo 回報，而且語氣非常肯定**。
2. `git -c core.quotepath=false`。否則非 ASCII 路徑會印成八進位轉義，
   **「哪個檔案改了」這個唯一需要讀的欄位會變成一串數字。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from framework_config import excluded                      # noqa: E402


def _text(cp):
    """取子行程的 stdout，⛔ 保證回傳字串。

    🔴 **實測個案（2026-08-27，繁體中文 Windows、Python 3.14.2，主持人的機器）：**
    `subprocess.run(..., capture_output=True, text=True)` 回傳 `returncode == 0`
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


def git_changed(root):
    """本輪變更清單。回傳 (清單, 錯誤訊息)。"""
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
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
        # 🔴 **專案位於 repo 的子目錄時，⛔ 不再拒絕回報（v1.4.1）。**
        #
        # ⚠️ **舊版一律回傳「位於另一個 repo 之內」並判 INCOMPLETE。**
        #    **⛔ 那個顧慮是對的（⛔ 不得對著錯誤的 repo 下判定），⛔ 但處置過重：**
        #    🔴 **本框架自己的倉庫就是這個形狀（兩個版本各是一個子目錄），
        #    使用者把專案放進一個既有的筆記 repo 裡也是。**
        #    **⇒ 那會是一盞永遠亮著的燈，而常態性紅燈會教人忽略整套系統（`R-19`）。**
        #
        # ✅ **正確作法：把回報範圍限縮到本專案的子樹，⛔ 而不是拒絕回報。**
        #    `git status --porcelain` 的路徑一律相對於 **repo 根目錄**，
        #    ⛔ 不是相對於 `-C` 指的目錄——**所以要自己去掉前綴，⛔ 不能假設。**
        top_path, root_r = pathlib.Path(out).resolve(), root.resolve()
        prefix = ""
        if top_path != root_r:
            try:
                prefix = root_r.relative_to(top_path).as_posix()
            except ValueError:
                # ⛔ git 說的 repo 根目錄不包含本專案——這才是真的該拒絕回報。
                return None, ("git 回報的 repo 根目錄⛔ 不包含本專案"
                              "——**拒絕回報，以免對著錯誤的 repo 下判定**")
        r = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false",
                            "status", "--porcelain", "--", "."],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20)
        if r.returncode != 0 or not isinstance(r.stdout, str):
            return None, ("`git status` 沒有給出可讀的輸出"
                          f"（exit {r.returncode}；stdout 型別 {type(r.stdout).__name__}）"
                          "——**⛔ 未檢查 ≠ 通過**")
        paths = [ln[3:].strip().strip('"') for ln in r.stdout.splitlines() if ln.strip()]
        if prefix:
            # ⛔ **子樹之外的變更一律丟掉。** ⚠️ `-- .` 已經限縮過一次，
            #    **本行是第二道**——⛔ 因為「以為限縮過了」與「真的限縮過」是兩件事。
            paths = [p[len(prefix) + 1:] for p in paths if p.startswith(prefix + "/")]
        return paths, None
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git 無法執行：{e}"


def _text_err(cp):
    return cp.stderr if isinstance(cp.stderr, str) else ""


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

    changed, err = git_changed(root)
    if changed is None:
        findings.append(("INCOMPLETE", "SCOPE_UNCHECKABLE",
                         f"{err}——**本項未檢查，這不等於通過**"))
    else:
        def under(path, tops):
            return any(path == a or path.startswith(a + "/") for a in tops)

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

    return emit("範圍與 T0 感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
