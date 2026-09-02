#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：`my/MY_RULES.md` 是否涵蓋框架的每一條規則

## 這支感測器為什麼存在

**框架的規則住在 `governance/RULES.md`，⛔ 而那個資料夾在升級時整包替換。**
🔴 **在 v1.4.0 以前，一個專案往 `RULES.md` 累積自己的規則，
升級時那些累積會被刪掉——⚠️ 而 `profiles/PROFILE_solo.md` 正在鼓勵使用者那樣做。**

→ **v1.4.1 起，專案的規則住在 `my/MY_RULES.md`（升級永不替換），
而框架規則以逐字副本存在該檔的 §1。**

## ⚠️ 這個設計刻意製造了兩份拷貝

🔴 **「同一個事實有兩份拷貝，而只有一份會被更新」是本框架失效家族的軸二本身。**
**⛔ 所以副本⛔ 不能沒有守望者——這支就是。**

⚠️ **前例：`R-24`（prompt 必須自足）也逼出過副本，
而框架當時的答案⛔ 不是禁止副本，是加一支 `sensor_clause_sync.py`。**
**本支是同一個做法，對象從「一份單行詞彙清單」擴大到「整套規則」。**

## 三項檢查

    RULE_MISSING_IN_MY        公版有、`MY_RULES.md` 沒有                    FAIL
    RULE_TEXT_DRIFT           兩邊都有，但正文不同（且未標覆寫）             FAIL
    OVERRIDE_WITHOUT_REASON   標了覆寫，⛔ 而同一行沒有寫理由                FAIL

⚠️ **⛔ 比對以「編號」為鍵，⛔ 不是整檔逐字比對。**
**理由：框架修一個錯字，整檔比對就報警，而規定動作是「把公版原句貼進去」——
⛔ 若不是以編號為鍵，貼進去會變成同一條規則在 `MY_RULES.md` 裡有兩份。**

## ⛔ 這支感測器不宣稱的事

⛔ **它⛔ 不檢查 `P-xx` 的內容品質。** ⚠️ 一條寫不成具體動作的規則它看不出來。
⛔ **它⛔ 不檢查覆寫的理由是否合理**——只檢查那一行有沒有字。
**⚠️ 判準是結構性的：⛔ 一個「一句讀起來合理的話」型的判準，
會讓感測器對一筆真問題永久靜默（見 `framework_config.py` 提案豁免的註解）。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402

ITEM = re.compile(r"^\*\*((?:R|P)-\d\d)\*\*")


def parse(text):
    """以 `**R-xx**` 或 `**P-xx**` 開頭的行為界，切出每一條的正文。

    ⚠️ **條目的結束界是：下一個條目、一個 `## ` 標題、或一條 `---`。**
    ⛔ 不能只用空行分界——`R-34` 的正文裡有空行。
    """
    items, cur, buf = {}, None, []
    for line in text.split("\n"):
        m = ITEM.match(line)
        if m:
            if cur:
                items[cur] = "\n".join(buf).rstrip()
            cur, buf = m.group(1), [line]
        elif cur is not None:
            # ⚠️ `<!--` 也是界：`MY_RULES.md` 的 §1 結尾有一行插入點註解，
            #    ⛔ 不把它算成界，最後一條規則的正文就會多出那一行而報 `RULE_TEXT_DRIFT`。
            #    🔴 **這一筆是本感測器上線後抓到的第一筆，而它抓的是它自己。**
            if (line.startswith("## ") or line.strip() == "---"
                    or line.lstrip().startswith("<!--")):
                items[cur] = "\n".join(buf).rstrip()
                cur, buf = None, []
            else:
                buf.append(line)
    if cur:
        items[cur] = "\n".join(buf).rstrip()
    return items



def is_override(body_text, marker):
    """回傳 `(有沒有標記, 理由夠不夠長)`。🔴 **覆寫判準的唯一定義處。**

    ⚠️ **標記必須自成一行（`i > 0`），⛔ 不得寫在條文那一行。**
    🔴 **實測（本感測器的成對樣本）：** 允許寫在同一行時，
    「`**R-19** [本專案覆寫] <原本的條文>`」會通過——**因為標記後面確實有字，
    而那些字是條文本身，不是理由。⛔ 判準因此形同虛設。**

    ⛔ **`tool_sync_my_rules.py` 讀的是同一個函式**——
    ⚠️ **兩份判準只要有一處不同，就會出現「感測器說是覆寫、工具卻把它列成待處理」。**
    ⚠️ **（v1.4.3 開發途中那支工具有過一個會自動覆寫的 `--adopt` [已退回]，
    ⛔ 已於 v1.4.4 整條退回；⇒ 現在兩邊都不寫檔，⛔ 而共用判準的理由不變。）**
    """
    body = body_text.split("\n")
    line = next((l for i, l in enumerate(body) if marker in l and i > 0), None)
    if line is None:
        return False, False
    return True, len(line.split(marker, 1)[1].strip()) >= 6

def main():
    root, cfg, as_json, name = cli("my_rules")
    findings, stats = [], {}

    fw_p = root / cfg.get("framework_rules", "governance/RULES.md")
    my_p = root / cfg.get("my_rules", "my/MY_RULES.md")
    marker = cfg.get("override_marker", "[本專案覆寫]")

    if not fw_p.is_file():
        findings.append(("INCOMPLETE", "FRAMEWORK_RULES_MISSING",
                         f"{fw_p.name} 不存在——**本項未檢查，⛔ 這不等於通過**"))
        return emit("我的規則感測器", findings, stats, as_json, name)
    if not my_p.is_file():
        findings.append(("INCOMPLETE", "MY_RULES_MISSING",
                         f"{cfg.get('my_rules', 'my/MY_RULES.md')} 不存在——"
                         "**框架規則因此沒有任何副本可比對。⛔ 未檢查 ≠ 通過**"))
        return emit("我的規則感測器", findings, stats, as_json, name)

    fw = parse(fw_p.read_text(encoding="utf-8"))
    my = parse(my_p.read_text(encoding="utf-8"))

    fw_ids = {k for k in fw if k.startswith("R-")}
    my_r = {k for k in my if k.startswith("R-")}
    my_p_ids = {k for k in my if k.startswith("P-")}

    overrides = []
    for rid in sorted(fw_ids):
        if rid not in my:
            findings.append(("FAIL", "RULE_MISSING_IN_MY",
                             f"{rid} 在公版有、在 {my_p.name} 沒有——"
                             "**跑 `python scripts/harness/tool_sync_my_rules.py` "
                             "把原句補進去，⛔ 不要憑印象打**"))
            continue
        if my[rid] == fw[rid]:
            continue
        # ⚠️ **覆寫標記必須自成一行，⛔ 不得寫在條文那一行。**
        #    🔴 **實測（本感測器的成對樣本）：** 允許寫在同一行時，
        #    「`**R-19** [本專案覆寫] <原本的條文>`」會通過——**因為標記後面確實有字，
        #    而那些字是條文本身，不是理由。⛔ 判準因此形同虛設。**
        marked, has_reason = is_override(my[rid], marker)
        if not marked:
            findings.append(("FAIL", "RULE_TEXT_DRIFT",
                             f"{rid} 兩邊正文不同，且未標 {marker}——"
                             "**框架的版本才是定義處。⛔ 要改請新增一條 `P-xx` 收緊它**"))
            continue
        if not has_reason:
            findings.append(("FAIL", "OVERRIDE_WITHOUT_REASON",
                             f"{rid} 標了 {marker}，⛔ 而同一行沒有寫理由——"
                             "**豁免是可以的，⛔ 但豁免要看得見**"))
            continue
        overrides.append(rid)

    for rid in sorted(my_r - fw_ids):
        findings.append(("WARN", "RULE_NOT_IN_FRAMEWORK",
                         f"{rid} 在 {my_p.name} 有、公版沒有——"
                         "**⚠️ 若這是你自己新增的規則，⛔ 編號要用 `P-xx`："
                         "框架下一版可能用掉同一個 `R-xx`**"))

    stats["公版規則"] = len(fw_ids)
    stats["本檔涵蓋"] = f"{len(fw_ids & my_r)} / {len(fw_ids)}"
    stats["本專案自訂"] = f"{len(my_p_ids)} 條（`P-xx`）"
    stats["覆寫"] = (f"{len(overrides)} 條：{'、'.join(overrides)}"
                     if overrides else "0 條")
    return emit("我的規則感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
