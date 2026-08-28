#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具：產生 `my/MY_INDEX.md` —— **這個專案裡屬於你的每一份文件**

## 這支工具為什麼存在

🔴 **實測個案（主持人提供，2026-08-27）：某專案套用本框架之後，
就不再維護自己的檔案索引了——它的 `file_index.md` 裡⛔ 沒有一條跟研究有關。**

⚠️ **機制：`file_index.md` 原本是先行專案用來管「研究計畫版本與輔助文件」的表。
在精煉為框架時，它的內容全部變成框架自己的東西，⛔ 而名字沒有換。**
**於是新使用者看到一份叫「檔案索引」的檔，以為那就是自己的索引——**
🔴 **然後他要嘛把自己的文件登記進去（升級時消失），要嘛就不再登記（實際發生的）。**

**⇒ 框架⛔ 不只是忽略了使用者的索引，它取代掉了一個本來存在的機制。**

## 判準：**列出框架⛔ 不擁有的每一樣東西**

⛔ **⚠️ 這裡刻意⛔ 不列舉「什麼算研究文件」。**
🔴 **一份「要收哪些」的清單就是白名單（`R-21`）：使用者永遠會發明新的資料夾，
而每一個沒被列到的資料夾都會靜靜地不出現在索引裡。**

⚠️ **先行專案的產生器就是這個形狀，而它的作者自己寫下了那句話：
「手寫目錄會漏檔案，⛔ 而產生器會漏目錄。」**

→ **本工具改成：掃全部，⛔ 再扣掉框架擁有的名字。**
**框架擁有哪些名字的唯一定義處是 `upgrade.py` 的可替換清單——⛔ 本檔不另寫一份。**

## 說明欄由 AI 維護，⛔ 不由程式猜

⚠️ **主持人的實務：研究索引的說明過去一直是由研究 AI 維護的。**
**⛔ 而程式對 `.docx`／`.pdf`／`.xlsx` 取不到任何有意義的標題。**

→ **檔案清單由程式產生（⛔ 不可能漂移），說明放在 `my/MY_INDEX_notes.json`（由 AI 維護）。**
🔴 **沒有說明的檔案⛔ 不會被藏起來，它們列在「尚無說明」那一段**——
**⛔ 一份看起來很完整、而漏掉一半檔案的索引，比沒有索引更糟。**

退出碼：0 產生成功｜1 檔案有問題｜2 查不了
"""
import io
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _common import _force_utf8                            # noqa: E402
from framework_config import load, excluded                # noqa: E402
# 🔴 **框架擁有哪些名字：唯一定義處是 `upgrade.py`。**
#    ⚠️ **⛔ 不在這裡重寫一份**——兩份手寫清單一定會分岔（憲章 §3.2、§6.4）。
#    ⛔ **也刻意⛔ 不放進 `governance_config.json`：那是使用者可改的檔，
#    而「升級可以換掉哪些東西」⛔ 不該由使用者的設定決定。**
from upgrade import FRAMEWORK_DIRS, FRAMEWORK_FILES        # noqa: E402

_force_utf8()

HEADER = """# 我的文件索引（**這個專案裡屬於你的東西**）

> 🔴 **⛔ 本檔由程式產生，⛔ 不要手改。** 重新產生：
> `python scripts/harness/tool_my_index.py`
>
> **說明欄寫在 `my/MY_INDEX_notes.json`**（那一份可以手改，也可以請 AI 維護）。
>
> ⚠️ **判準是「框架⛔ 不擁有的每一樣東西」，⛔ 不是一份「要收哪些」的清單**——
> **一份要收哪些的清單就是白名單，而使用者永遠會發明新的資料夾。**
>
> ⛔ **框架自己的檔案索引在 `file_index.md`，⛔ 那一份升級時會被整包換掉。**
"""


def framework_owned(rel):
    """這個相對路徑是不是框架擁有的東西。"""
    top = rel.split("/", 1)[0]
    return top in FRAMEWORK_DIRS or rel in FRAMEWORK_FILES


def collect(root, cfg):
    """回傳相對路徑清單，**依字串排序**。

    🔴 **實測個案（2026-08-27，v1.4.1 發布當下，主持人的機器）：**
    **舊版寫的是 `sorted(root.rglob("*"))`——⛔ 那是把 `Path` 物件拿去排序。**
    **⚠️ `WindowsPath` 的比較會先做 casefold，`PosixPath` ⛔ 不會。**
    **於是 `PROJECT.md` 在 Linux 上排在 `corpus/` 前面，在 Windows 上排在後面。**

    ⛔ **後果：我在 Linux 產生、隨 v1.4.1 一起發布的索引，
    在主持人的 Windows 上跑第一次就報 `MY_INDEX_STALE`——
    而它報的⛔ 不是「索引過期」，是「你的作業系統跟產生它的那台不一樣」。**
    🔴 **一個對正確狀態報警的判準，會教人忽略它（`R-19`）——
    而它已經逼主持人在發布途中手動繞過一次。**

    ⇒ **排序的鍵改成「相對路徑的 posix 字串」。⛔ 不排 `Path` 物件。**
    """
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if excluded(p, root, cfg):
            continue
        rel = p.relative_to(root).as_posix()
        if framework_owned(rel):
            continue
        if rel in (cfg.get("my_index", "my/MY_INDEX.md"),):
            continue                      # ⛔ 索引不列自己
        if any(pathlib.PurePosixPath(rel).match(g)
               for g in cfg.get("my_index_exclude", [])):
            continue                      # ⛔ 框架自己產生的檔案
        files.append(rel)
    # ⛔ **排字串，⛔ 不排 Path。** 見本函式說明。
    return sorted(files)


def render(root, cfg):
    """產生索引全文。回傳 (內文, 統計, 錯誤訊息)。

    🔴 **感測器與本工具共用這一支，⛔ 不各寫一份。**
    ⚠️ **兩份產生邏輯只要有一處不同，「索引是否過期」這個判準就永遠會說過期，
    ⛔ 而真正的原因是兩支程式不一樣。**
    """
    notes_p = root / cfg.get("my_index_notes", "my/MY_INDEX_notes.json")
    notes = {}
    if notes_p.is_file():
        try:
            notes = json.loads(notes_p.read_text(encoding="utf-8"))
        except Exception as e:                              # noqa: BLE001
            # ⛔ R-33 的位置：讀不了說明檔⛔ 不得當成「沒有說明」往下走。
            return None, None, (f"{notes_p.name} 無法解析：{e}"
                                "——**⚠️ 這與「沒有說明」是兩件事**")
    notes = {k: v for k, v in notes.items() if not k.startswith("_")}

    files = collect(root, cfg)
    described = [f for f in files if notes.get(f)]
    plain = [f for f in files if not notes.get(f)]
    # 🔴 說明指向一個不存在的檔案 —— 那是懸空引用，⛔ 必須看得見。
    dangling = sorted(k for k in notes if k not in set(files))

    out = [HEADER, ""]
    out.append(f"**檔案 {len(files)} 份｜有說明 {len(described)} 份｜"
               f"尚無說明 {len(plain)} 份**")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 有說明的")
    out.append("")
    if described:
        out.append("| 檔案 | 說明 |")
        out.append("|---|---|")
        for f in described:
            out.append(f"| `{f}` | {notes[f]} |")
    else:
        out.append("**（尚無。⚠️ 這是盤點的結果——每一份檔案都在下一節。）**")
    out.append("")
    out.append("## ⚠️ 尚無說明的")
    out.append("")
    if plain:
        out.append("🔴 **⛔ 它們⛔ 沒有被藏起來。** "
                   "請 AI 把說明寫進 `my/MY_INDEX_notes.json`，再跑一次本工具。")
        out.append("")
        for f in plain:
            out.append(f"- `{f}`")
    else:
        out.append("**（無。⚠️ 這是盤點的結果，⛔ 不是沒有盤點。）**")
    if dangling:
        out.append("")
        out.append("## 🔴 說明指向不存在的檔案")
        out.append("")
        out.append("⚠️ **檔案被搬走或改名了，⛔ 而說明留在原地。**")
        out.append("")
        for f in dangling:
            out.append(f"- `{f}`")
    out.append("")

    return ("\n".join(out),
            {"檔案": len(files), "有說明": len(described),
             "尚無說明": len(plain), "說明指向不存在的檔案": dangling},
            None)


def main():
    root = HERE.parents[1]
    cfg = load(root)
    idx = root / cfg.get("my_index", "my/MY_INDEX.md")
    text, stats, err = render(root, cfg)
    if err:
        print(f"[FAIL] {err}——**⛔ 沒有產生任何東西。**")
        return 1
    idx.parent.mkdir(parents=True, exist_ok=True)
    io.open(idx, "w", encoding="utf-8", newline="\n").write(text)
    print(f"✅ 已產生 {idx.relative_to(root)}")
    print(f"   檔案 {stats['檔案']} 份｜有說明 {stats['有說明']}｜"
          f"尚無說明 {stats['尚無說明']}")
    if stats["說明指向不存在的檔案"]:
        print(f"   🔴 說明指向不存在的檔案："
              f"{len(stats['說明指向不存在的檔案'])} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
