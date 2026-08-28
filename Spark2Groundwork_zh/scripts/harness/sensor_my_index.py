#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：`my/MY_INDEX.md` 是不是過期的

## 為什麼一份自動產生的索引也需要守望者

⚠️ **產生器只有在有人跑它的時候才會產生。**
🔴 **一份三個月沒重跑的索引，與一份手寫而忘記更新的索引，⛔ 完全一樣**——
**它們都是「看起來完整、而實際上漏了一半」。**

⛔ **所以本感測器⛔ 不重寫產生邏輯：它呼叫 `tool_my_index.render()`，
把結果與檔案內容逐字比對。**
⚠️ **兩份產生邏輯只要有一處不同，這個判準就會永遠說過期，
⛔ 而真正的原因是兩支程式不一樣（憲章 §3.2）。**

## 三項檢查

    MY_INDEX_MISSING        索引還沒產生過                      INCOMPLETE
    MY_INDEX_STALE          重新產生的結果與檔案不同             FAIL
    INDEX_NOTE_DANGLING     說明指向一個不存在的檔案             FAIL

⚠️ **`INDEX_NOTE_DANGLING` 是懸空引用**——**檔案被搬走或改名，⛔ 而說明留在原地。**
**它與 `sensor_reference_integrity.py` 擋的是同一種東西，⛔ 只是對象不同。**

## ⛔ 本感測器不宣稱的事

⛔ **它⛔ 不檢查說明寫得對不對。** ⚠️ 一句與檔案內容無關的說明，它看不出來。
⛔ **它⛔ 不檢查「該有的檔案在不在」**——**索引是從磁碟掃出來的，
⚠️ 一個根本沒被建立的檔案，⛔ 不會因為它不在索引裡而被發現。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit                              # noqa: E402
from tool_my_index import render                           # noqa: E402


def main():
    root, cfg, as_json, name = cli("my_index")
    findings, stats = [], {}
    idx = root / cfg.get("my_index", "my/MY_INDEX.md")

    text, st, err = render(root, cfg)
    if err:
        findings.append(("INCOMPLETE", "INDEX_NOTES_UNREADABLE",
                         f"{err}——**⛔ 本項未檢查，這不等於通過**"))
        return emit("我的索引感測器", findings, stats, as_json, name)

    stats["你的檔案"] = st["檔案"]
    stats["有說明"] = st["有說明"]
    stats["尚無說明"] = st["尚無說明"]

    if not idx.is_file():
        findings.append(("INCOMPLETE", "MY_INDEX_MISSING",
                         f"{cfg.get('my_index', 'my/MY_INDEX.md')} 還沒產生過"
                         "——**跑 `python scripts/harness/tool_my_index.py`。"
                         "⛔ 未產生 ≠ 沒有東西要索引**"))
        return emit("我的索引感測器", findings, stats, as_json, name)

    if idx.read_text(encoding="utf-8") != text:
        findings.append(("FAIL", "MY_INDEX_STALE",
                         "索引與現在的檔案不一致——**重跑 "
                         "`python scripts/harness/tool_my_index.py`。"
                         "⚠️ 一份過期的索引與一份手寫而忘記更新的索引⛔ 是同一件事**"))

    dangling = st["說明指向不存在的檔案"]
    for d in dangling:
        findings.append(("FAIL", "INDEX_NOTE_DANGLING",
                         f"`{d}` 有說明，⛔ 而那個檔案不存在"
                         "——**檔案被搬走或改名了，而說明留在原地**"))
    if dangling:
        stats["🔴 說明指向不存在的檔案"] = len(dangling)

    if st["檔案"] == 0:
        findings.append(("WARN", "MY_INDEX_EMPTY",
                         "這個專案裡目前⛔ 沒有任何屬於你的檔案"
                         "——**⚠️ 這是盤點的結果，⛔ 不是沒有盤點**"))
    return emit("我的索引感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
