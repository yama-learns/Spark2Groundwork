#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具：把框架新增的規則原句補進 `my/MY_RULES.md`

**⛔ 這不是感測器，是感測器報 `RULE_MISSING_IN_MY` 之後的那個規定動作。**

## 為什麼要有這支，而不是叫人自己貼

🔴 **「自己貼」那一步，就是「兩份拷貝只更新一份」的來源。**
⚠️ **憑印象打出來的條文，讀起來與原句一模一樣，⛔ 而它們不同**——
**框架自己踩過：條款同步感測器抓到我把 `extremely` 打成 `extremely high`。**

## 它做兩件事，⛔ 而第二件⛔ 不寫檔

**① 把公版有、`MY_RULES.md` 沒有的條目，逐字附加在 §1 的結尾。**

**② 把「正文不同、⛔ 而未標覆寫」的條目逐行列出來，⛔ 而由你自己決定怎麼處理。**

## 🔴 為什麼 ② ⛔ 不由程式代勞（v1.4.4 的裁決）

⚠️ **上一版開發途中曾經做過一個 `--adopt` [已退回]：它會替你把漂移的條目換成公版原句。**
**（那一版原訂 `v1.4.3`，⛔ 而 `v1.4.3` 從未發布——問題就是在發布前的覆核中發現的；
⇒ 退回 `--adopt` 之後，其餘內容改以本版 `v1.4.4` 發布。）**
🔴 **它在覆核中被發現有三個缺陷：先寫檔才印預覽、無條件宣稱「檢查點還在」、
以及在檢查點程式明確失敗時仍然寫入。**
**⇒ 主持人裁決退回整個寫入路徑。**

**⛔ 這一支因此⛔ 不會覆蓋 `MY_RULES.md` 裡任何既有的一個字。**
**⚠️ 它改為印出逐行差異，讓你知道要貼哪幾行**——
🔴 **「一個會自動覆寫使用者文字的工具」與「一份看得懂的差異」，
⛔ 前者的風險⛔ 不值得它省下的那幾秒。**

## 框架修訂了一條既有規則時，你要做什麼

**跑這一支 → 它會印出差異 → 把 `+` 開頭的那幾行逐字貼進 `my/MY_RULES.md` 的該條正文。**
⛔ **⛔ 不要整份取代 `MY_RULES.md`**——那會刪掉你的 `P-xx` 與覆寫紀錄。
⚠️ **或者：如果那是你刻意的修改，在該條正文另起一行標覆寫並寫下理由。**

退出碼：0 完成（含「0 條要補」）｜1 檔案有問題｜2 查不了
"""
import argparse
import difflib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import _force_utf8                            # noqa: E402
from framework_config import load                          # noqa: E402
from sensor_my_rules import parse, is_override                          # noqa: E402

_force_utf8()
MARKER = "<!-- FRAMEWORK_RULES_END"



def preview(rid, old, new, limit=8):
    """印出**實際的變更行**（裁決 `A4a: A`）。

    🔴 **舊版印的是「舊的第一行 → 新的第一行」，⛔ 而 `R-34` 的變更全在第二行以後**——
    **⇒ 在第一個真實使用情境（`R-34`）上，那個預覽印出來的是兩行一模一樣的字。**
    ⚠️ **它⛔ 不只是沒幫上忙，它讓使用者以為「沒改什麼」。**

    回傳實際印出的差異行數；**0 代表判準說有 drift 而 diff 是空的**——
    ⛔ **那是矛盾，呼叫端必須拒絕寫入。**
    """
    o, n = old.split("\n"), new.split("\n")
    rows = [l for l in difflib.unified_diff(o, n, lineterm="", n=0)
            if not l.startswith(("---", "+++", "@@"))]
    print(f"  {rid}　正文 {len(o)} 行 → {len(n)} 行")
    for l in rows[:limit]:
        print(f"    {l}")
    if len(rows) > limit:
        print(f"    …（其餘 {len(rows) - limit} 行未顯示，"
              f"完整內容見公版 `governance/RULES.md` 的 {rid}）")
    return len(rows)


def _skip_note(body, marker):
    """被跳過的那一條，⛔ 要說清楚它是哪一種跳過。

    🔴 **`is_override()` 回傳兩個值：`(有沒有標記, 理由夠不夠長)`。**
    ⚠️ **舊版只取 `[0]`，於是一條「標了覆寫但沒寫理由」的規則，
    在工具這裡被說成「已標覆寫」，⛔ 而 `sensor_my_rules.py` 正在對它報
    `OVERRIDE_WITHOUT_REASON` FAIL。**
    **⇒ 使用者被告知「這一條已經妥當登記了」，而他正處在一個修不掉的 FAIL 裡。**

    ⛔ **行為⛔ 不變（標記存在就不碰，那是對的）；改的是這句話說了什麼。**
    """
    marked, has_reason = is_override(body, marker)
    if marked and has_reason:
        return f"已標 {marker}"
    return (f"標了 {marker}，⛔ 而同一行沒有寫理由——"
            "🔴 **本工具不碰它，⛔ 但感測器會對它報 `OVERRIDE_WITHOUT_REASON` FAIL。**"
            "→ 補上理由，或拿掉標記，再依上方的差異自己把公版原句貼回去")

def main(argv=None):
    # ⚠️ 參數必須在任何讀寫前解析。未知參數仍由 argparse 以 exit 2 拒絕；
    #    退出碼語意的統一已由主持人裁決延至 v1.5.0。
    ap = argparse.ArgumentParser(
        description="把框架新增的規則原句補進指定專案的 my/MY_RULES.md")
    ap.add_argument("--root", default=None,
                    help="專案根目錄；省略時使用本工具所在的專案")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve() if a.root else HERE.parents[1]
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

    marker = cfg.get("override_marker", "[本專案覆寫]")
    fw, my = parse(fw_text), parse(my_text)
    missing = [k for k in sorted(fw) if k.startswith("R-") and k not in my]

    # ⚠️ **三堆，⛔ 而三堆都要印出分母**（`R-35`）。
    drift, protected = [], []
    for k in sorted(fw):
        if not k.startswith("R-") or k not in my or my[k] == fw[k]:
            continue
        (protected if is_override(my[k], marker)[0] else drift).append(k)

    print(f"公版規則：{len([k for k in fw if k.startswith('R-')])} 條")
    print(f"本檔已涵蓋：{len([k for k in my if k.startswith('R-')])} 條")
    print(f"正文不同：{len(drift) + len(protected)} 條"
          f"（其中 {len(protected)} 條已標 {marker}，⛔ 本工具一律不碰）")

    # ⛔ R-33：「沒有事情要做」⛔ 不得是預設分支。
    #    ⚠️ **這個判斷改到 ① 之後**：判準是「算完之後與原文相同」，
    #    ⛔ 不是「missing 與 drift 都空」——**drift 一律要報告，⛔ 即使沒有東西要附加。**

    # ── ① 計算：⛔ 這一支⛔ 不覆蓋任何既有文字 ──────────────────
    text = my_text
    if missing:
        block = "\n\n".join(fw[k] for k in missing)
        i = text.index(MARKER)
        text = text[:i] + block + "\n\n" + text[i:]

    def _report_drift():
        """🔴 唯讀報告：印出差異行，⛔ 而由人決定怎麼處理。"""
        if not drift:
            return
        print(f"\n🔴 **{len(drift)} 條的正文與公版不同，⛔ 而它們沒有標 {marker}：**")
        for k in drift:
            preview(k, my[k], fw[k])
        print(f"\n**⛔ 本工具⛔ 沒有動它們，也永遠不會動。** 兩條路：\n"
              "  ① 這是框架改過的規則 →\n"
              f"     **把上面 `+` 開頭的那幾行，逐字貼進 `my/MY_RULES.md` 裡那一條的正文。**\n"
              "     ⛔ **⛔ 不要整份取代 `MY_RULES.md`**——那會刪掉你的 `P-xx` 與覆寫紀錄。\n"
              f"  ② 這是你刻意的修改 → 在該條正文另起一行標 {marker} 並寫下理由\n"
              "⚠️ **⛔ 放著不管的話，`sensor_my_rules.py` 會一直報 `RULE_TEXT_DRIFT`。**")

    def _report_protected():
        for k in protected:
            print(f"  （跳過）{k} {_skip_note(my[k], marker)}")

    if text == my_text:
        # ⛔ R-33：「沒有事情要做」⛔ 不得是預設分支。
        print("\n**⛔ 沒有東西需要附加**——這是算過的結果，不是沒有算。")
        _report_drift()
        _report_protected()
        return 0

    my_p.write_text(text, encoding="utf-8")
    print(f"\n  ✅ 已附加 {len(missing)} 條。"
          "⛔ **⛔ 沒有任何既有文字被覆蓋**——本工具只在 §1 結尾追加。")
    for k in missing:
        print(f"  ＋ {fw[k].split(chr(10), 1)[0]}")
    _report_drift()
    _report_protected()
    print("\n⚠️ **⛔ 請讀過補進來的每一條。** 它們現在會約束你和你的 AI。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
