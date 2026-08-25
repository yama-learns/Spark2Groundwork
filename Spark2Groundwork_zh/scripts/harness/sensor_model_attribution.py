#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：模型歸屬（隨選）

**規則來源：** `policy/MODEL_IDENTITY.md` §3.4（產出物之作者欄須寫具體型號）
與 §3.6 規則 2（平台名不是型號）；`policy/HANDOFF.md` §3（封包必備五項第一項）。

## 檢查

    MODEL_ATTRIBUTION_MISSING     產出物檔頭沒有型號欄                    FAIL
    MODEL_ATTRIBUTION_VAGUE       只寫家族名或平台名，無具體型號          FAIL
    MODEL_UNREADABLE_DECLARED     正確地宣告「無法讀取」                  WARN
    SCAN_GLOB_MATCHES_NOTHING     掃描範圍命中 0 個檔案                   WARN

## 🔴 這支感測器整個重寫過，理由值得記在這裡

**舊版帶著兩份硬編白名單**（`GRANDFATHERED` 13 筆、`FROZEN_HANDOFFS` 12 筆），
列的全是**另一個專案的檔名**——一個 `mve/` 底下的檔、一個 `policy/` 底下的 git 政策檔等等，
**在本框架中沒有一個存在。**
⚠️ **此處刻意不逐字寫出那些檔名**——寫出來，它們就成為本檔的懸空引用。
**「描述缺陷時不要實例化它」**（先行專案在同一個機制上撞過三次）。它還帶著 5 筆懸空章節引用（⚠️ **理由同上，此處刻意不寫出那些章節編號**——
它們在本框架的憲章中都不存在，寫出來就成為本檔自己的懸空引用），並且**在一個全新的乾淨模板上第一次執行就報三筆 WARN**。

> ⛔ `R-21`：白名單／硬編清單**不得**作為掃描範圍的定義方式。
> ⛔ `R-19`：一支會對正確文本報警的感測器，會教人忽略它。

### 🔴 但真正的根因不是白名單，是**掃描範圍錯了**

舊版掃「根目錄所有 `.md`」。**而根目錄的 `.md` 是框架提供的模板
（`README.md`、`SETUP.md`、`file_index.md` …），不是 AI 的產出物——它們本來就不該有作者欄。**
於是它必須靠一張愈長愈好的豁免清單來壓住自己製造的告警。

> **那張白名單是為了補償一個錯的掃描範圍而存在的。**
> **範圍改對，白名單就不需要了——這一版一筆硬編檔名都沒有。**

**現在的範圍：`framework_config.py` 的 `attribution_globs`（發現式，預設 `handoffs/*.md`）
——只掃 AI 實際產出的東西。**

## ⚠️ 「具體型號」怎麼機械判定

⛔ **不列舉型號清單**——那是另一種白名單，而且一定會過期。
**判準是結構性的：具體型號幾乎必然帶版本數字**
（`opus-5`、`sonnet-5`、`gemini-3.7-flash`、`o4-mini`、`haiku-4.5`），
**而家族名與平台名不帶**（`Claude`、`Gemini`、`Antigravity`、`Cowork`）。

⚠️ 平台名另以一份**取值域**清單輔助（⛔ 這是取值域，不是掃描範圍，故不違反 `R-21`
——同 `ai_checkpoint.sh` 的角色白名單）。

## ✅ 「無法讀取」是正確答案，⛔ 不得判為缺陷

`policy/MODEL_IDENTITY.md` §3.6.3 規則 1 逐字：標記不在可見上下文內時，
**唯一正確的輸出**是 `[Model: 無法讀取——…]`。
⛔ **判它 FAIL 會逼下一個模型退回寫平台名，而 §3.6 規則 2 說那比留空更糟。**
→ 判 WARN，並提醒依 §3.6 規則 3 請使用者補填。

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（**⛔ 未完成 ≠ 通過**）
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings            # noqa: E402
from framework_config import resolve_globs                   # noqa: E402

# 型號欄的兩種寫法：`[Model: X]` 與 `**建立：** X，日期`
MODEL_TAG = re.compile(r"\[Model:\s*([^\]]+)\]", re.I)
AUTHOR_FIELD = re.compile(r"^\*{0,2}(?:建立|作者|撰寫|執行模型|Created|Author|Model)"
                          r"\*{0,2}\s*[:：]\s*\*{0,2}\s*([^\n，,]+)", re.M)
# ✅ 正確的「讀不到」宣告——⛔ 不是缺陷
UNREADABLE = re.compile(r"無法讀取|cannot read|unreadable|not in the visible context")
# ⚠️ 取值域，不是掃描範圍（故不違反 R-21）。平台名可跑不同模型，寫它等於沒寫。
PLATFORMS = ("antigravity", "cowork", "claude code", "ai studio", "gemini app",
             "chatgpt", "copilot", "openai", "anthropic", "google")
# 具體型號幾乎必然帶版本數字；家族名與平台名不帶。
HAS_VERSION = re.compile(r"\d")
HEAD_LINES = 15


def attribution(text):
    """回傳檔頭宣告的型號字串，找不到時回傳 None。"""
    head = "\n".join(text.splitlines()[:HEAD_LINES])
    m = MODEL_TAG.search(head)
    if m:
        return m.group(1).strip()
    m = AUTHOR_FIELD.search(head)
    return m.group(1).strip() if m else None


def main():
    root, cfg, as_json, name = cli("model_attribution")
    globs = cfg.get("attribution_globs", ["handoffs/*.md"])
    files, dead = resolve_globs(globs, root, cfg)
    findings = dead_glob_findings(dead, "attribution_globs", root)
    vague = missing = unread = 0

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} 非 UTF-8，本檔未檢查——**不等於通過**"))
            continue
        who = attribution(text)
        if who is None:
            missing += 1
            findings.append(("FAIL", "MODEL_ATTRIBUTION_MISSING",
                             f"{p.relative_to(root)} 檔頭無型號欄"
                             "——`policy/HANDOFF.md` §3：缺一即視為未交付"))
            continue
        if UNREADABLE.search(who):
            # ✅ 這是 MODEL_IDENTITY §3.6.3 規則 1 指定的唯一正確輸出
            unread += 1
            findings.append(("WARN", "MODEL_UNREADABLE_DECLARED",
                             f"{p.relative_to(root)} 正確地宣告了「無法讀取」"
                             "——⛔ 這不是缺陷。依 §3.6 規則 3，請使用者補填"))
            continue
        low = who.lower()
        if any(pf in low for pf in PLATFORMS) or not HAS_VERSION.search(who):
            vague += 1
            findings.append(("FAIL", "MODEL_ATTRIBUTION_VAGUE",
                             f"{p.relative_to(root)}：「{who[:40]}」不是具體型號"
                             "——**寫平台名或家族名比留空更糟，它讀起來像有答案，"
                             "會讓下游停止追問**（`policy/MODEL_IDENTITY.md` §3.6.3 規則 2）"))

    stats = {"掃描產出物": len(files), "無型號欄": missing,
             "只有家族名／平台名": vague, "已宣告無法讀取": unread}
    return emit("模型歸屬感測器", findings, stats, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
