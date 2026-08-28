#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具：把框架新增的規則原句補進 `my/MY_RULES.md`

**⛔ 這不是感測器，是感測器報 `RULE_MISSING_IN_MY` 之後的那個規定動作。**

## 為什麼要有這支，而不是叫人自己貼

🔴 **「自己貼」那一步，就是「兩份拷貝只更新一份」的來源。**
⚠️ **憑印象打出來的條文，讀起來與原句一模一樣，⛔ 而它們不同**——
**框架自己踩過：條款同步感測器抓到我把 `extremely` 打成 `extremely high`。**

## ⛔ 它只做一件事

**把公版有、`MY_RULES.md` 沒有的條目，逐字附加在 §1 的結尾，並印出補了哪幾條。**

⛔ **它⛔ 不覆寫既有條目**——**若某一條的正文不同，那是 `RULE_TEXT_DRIFT`，
由人決定是要標覆寫還是改回來。⚠️ 一支會自動覆寫的工具，會把使用者刻意的修改靜靜地抹掉。**

退出碼：0 完成（含「0 條要補」）｜1 檔案有問題｜2 查不了
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import _force_utf8                            # noqa: E402
from framework_config import load                          # noqa: E402
from sensor_my_rules import parse                          # noqa: E402

_force_utf8()
MARKER = "<!-- FRAMEWORK_RULES_END"


def main():
    root = HERE.parents[1]
    cfg = load(root)
    fw_p = root / cfg.get("framework_rules", "governance/RULES.md")
    my_p = root / cfg.get("my_rules", "my/MY_RULES.md")

    # ⛔ R-33 的位置：前置條件失敗⛔ 不得走到「沒有事情要做」那條路徑。
    for p in (fw_p, my_p):
        if not p.is_file():
            print(f"[INCOMPLETE] {p} 不存在——**⛔ 沒有補任何東西，而這不等於沒有東西要補**")
            return 2

    fw_text = fw_p.read_text(encoding="utf-8")
    my_text = my_p.read_text(encoding="utf-8")
    if MARKER not in my_text:
        print(f"[FAIL] {my_p.name} 裡找不到插入點 `{MARKER} …`——"
              "**⛔ 那一行被刪掉了。請從框架重新取一份 `MY_RULES.md` 的檔頭**")
        return 1

    fw, my = parse(fw_text), parse(my_text)
    missing = [k for k in sorted(fw) if k.startswith("R-") and k not in my]

    print(f"公版規則：{len([k for k in fw if k.startswith('R-')])} 條")
    print(f"本檔已涵蓋：{len([k for k in my if k.startswith('R-')])} 條")
    if not missing:
        # ⚠️ **「0 條要補」是盤點的結果，⛔ 所以要把分母印出來**（R-35）。
        print("要補：0 條。**⛔ 這是比對過的結果，不是沒有比對。**")
        return 0

    block = "\n\n".join(fw[k] for k in missing)
    i = my_text.index(MARKER)
    my_p.write_text(my_text[:i] + block + "\n\n" + my_text[i:], encoding="utf-8")

    print(f"要補：{len(missing)} 條 → 已逐字附加在 §1 結尾：")
    for k in missing:
        first = fw[k].split("\n", 1)[0]
        print(f"  ＋ {first}")
    print("\n⚠️ **⛔ 請讀過補進來的每一條。** 它們現在會約束你和你的 AI。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
