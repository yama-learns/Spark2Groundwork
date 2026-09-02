#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：引用完整性——**被引用的檔案存不存在**

## 檢查

    DANGLING_FILE_REF        引用了一個專案裡不存在的檔案                  FAIL
    REF_EXEMPTED_NOT_SHIPPED 同一行明示「未隨附／須自建」而豁免            WARN
    SCAN_GLOB_MATCHES_NOTHING 掃描範圍命中 0 個檔案                        WARN

## 為什麼需要它（**四筆實測個案，全部發生在框架自己身上**）

既有的 `sensor_governance_text.py` 只查 `` `<檔>.md` §N `` 的**章節**能不能解析，
**而且只掃 `.md`。** 於是兩個缺口一直開著：

| 缺口 | 實測個案 |
|---|---|
| **`.py` 檔頭從未被掃過** | 一支感測器的檔頭帶著 5 筆指向另一個專案的懸空章節引用，與 2 筆懸空檔案引用 |
| **「檔案存不存在」從未被查過** | 一份 policy 文件承諾了一個機械防線，而**那個檔案不存在於框架中** |

⚠️ **第三筆個案是本感測器自己引起的：** 我在重寫上述感測器時，
**把舊白名單的檔名當例子寫進註解**，於是那些檔名立刻成為新的懸空引用。
**「描述缺陷時不要實例化它」——先行專案在同一個機制上撞過三次，這是第四次。**

## ⚠️ 兩種**不是**缺陷的引用，以及它們的處理

| 形態 | 例 | 處理 |
|---|---|---|
| **格式佔位符** | `` `<檔名>.md` §N `` | ⛔ 不檢查。**判準是尖括號**——一個一眼可辨的佔位符 |
| **明示未隨附** | 「建議檔名 `x.md` … ⚠️ 本框架未隨附此檔，須自建」 | ✅ 豁免，**但必須印出來** |

🔴 **豁免的判準刻意是「同一行有顯式標記」，⛔ 不是一份豁免清單。**
⚠️ 先行專案的教訓：字串比對分不出「這個名字是誰在說」，
而前兩次都靠**改寫措辭**迴避，第三次那個字串是實質內容、無法迴避——
**於是他們改用顯式標記，並要求標記本身必須被列印。** 本感測器沿用該做法。

⛔ **靜默豁免與沒有豁免，在畫面上長得一樣。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（**⛔ 未完成 ≠ 通過**）
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import (resolve_globs, excluded,
                              active_launcher_globs)         # noqa: E402

# 只認「看起來是專案檔案」的引用：有副檔名、無空白開頭
REF = re.compile(r"`([\w/.一-鿿-]+\.(?:md|py|sh))`")
# ⛔ 尖括號＝佔位符，不是引用
PLACEHOLDER = re.compile(r"[<>]")
# ✅ 顯式的「未隨附」標記（同一行）
NOT_SHIPPED = re.compile(r"未隨附|須自建|建議檔名|尚未建立|"
                         r"not shipped|create your own|suggested filename")


# ── 自足性：本資料夾必須能被單獨複製出去使用 ────────────────────────
# 🔴 **實測個案：** 框架說明圖第一版放在**倉庫根目錄**的 `docs/`，
#    而 README 以 `../docs/framework.svg` 引用它。
#    **在倉庫裡看起來完全正常**——但使用者的用法是把本資料夾整包複製到自己的專案，
#    ⛔ **複製出去之後那張圖就不存在了，而 README 仍然理直氣壯地引用它。**
# ⚠️ **這一類依賴在原地永遠不會報錯**，只在別人手上壞掉。
ESCAPE = re.compile(r"(?:\]\(|src=[\"']|href=[\"'])\s*(\.\./[^\)\"'\s]+)")


def escapes_root(text):
    """回傳所有「往上跳出本資料夾」的引用。⛔ 判準是路徑，不是意圖。"""
    return [m.group(1) for m in ESCAPE.finditer(text)]


def main():
    root, cfg, as_json, name = cli("reference_integrity")
    launchers = active_launcher_globs(cfg.get("launcher_globs", []), root)
    globs = (cfg.get("code_globs", ["scripts/**/*.py", "scripts/**/*.sh"])
             + launchers
             + cfg.get("governance_globs", []))
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "code_globs ＋ launcher_globs ＋ governance_globs", root)

    # 專案內實際存在的檔名（含子目錄），供「只寫檔名」的引用比對
    present = {p.name for p in root.rglob("*") if p.is_file()}
    exempted, checked = [], 0

    for p in files:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} 非 UTF-8，本檔未檢查——**不等於通過**"))
            continue
        for esc in escapes_root("\n".join(lines)):
            findings.append(("FAIL", "REF_ESCAPES_EDITION",
                             f"{p.relative_to(root)}：引用 `{esc}` **跳出了本資料夾**——"
                             "⚠️ 本資料夾必須能被單獨複製出去使用，"
                             "⛔ 在倉庫裡看得到，不代表使用者複製走之後看得到"))
        for lineno, line in enumerate(lines, 1):
            for m in REF.finditer(line):
                ref = m.group(1).strip()
                if PLACEHOLDER.search(ref):
                    continue                      # 格式佔位符，不是引用
                checked += 1
                if (root / ref).exists() or ref.split("/")[-1] in present:
                    continue
                if NOT_SHIPPED.search(line):
                    exempted.append(f"{p.relative_to(root)}:{lineno} `{ref}`")
                    continue
                findings.append(("FAIL", "DANGLING_FILE_REF",
                                 f"{p.relative_to(root)}:{lineno} 引用 `{ref}`，"
                                 "但專案中找不到這個檔案"))

    if exempted:
        # ⛔ 豁免必須看得見（「靜默過濾」家族）
        findings.append(("WARN", "REF_EXEMPTED_NOT_SHIPPED",
                         f"{len(exempted)} 筆引用因同一行明示「未隨附／須自建」而豁免："
                         f"{'；'.join(exempted[:4])}"
                         f"{'…' if len(exempted) > 4 else ''}"
                         "——**豁免不是沒有發生**"))

    return emit("引用完整性感測器", findings,
                {"掃描檔案": len(files), "檢查的引用": checked,
                 "顯式豁免": len(exempted)}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
