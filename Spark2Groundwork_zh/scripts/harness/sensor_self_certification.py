#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：產出物自我背書（「產出物自我背書」家族）

## 觸發個案

某專案 64 份檔案的檔尾皆自述：
> 「文中所有樣本數、統計檢定量及引用皆經原著全文核實，嚴謹確保零捏造。」

而同一批檔案中查出捏造樣本數。**該宣告不只無法查證，而是可證明為假。**

## 為什麼它是獨立的失效型態

**「索引當權威」是把弱證據當強證據；「自我背書」是把「我說我做過」當成「做過」——
證據根本不存在。** 它比前者更難擋，因為讀者看到的是一段語氣嚴謹、
術語正確、看不出破綻的宣告。

## 判準（**結構性，非關鍵字獵巫。四項全中才判 FAIL**）

    (a) 自我指涉   主詞指向本文件自身
    (b) 全稱範圍   所有／全部／全數／皆／均／無一
    (c) 正確性對象 核實／查證／驗證／無誤／零捏造
    (d) 完成語氣   ⛔ 含「不得／必須／應／須／若」者豁免
                   ——「每一項未通過即不得提交」是**閘門**，正是我們要的東西，不是背書

    另有豁免：(e) 指名可獨立重跑的工具、指令或檔案

⚠️ **本感測器刻意不判斷宣告真偽**——那需要讀原文。它只判斷「這句話有沒有把自己當證據」。
⛔ **修法是刪除宣告或改為指向工具，不是把「所有」改成「大部分」來規避字串比對。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings          # noqa: E402
from framework_config import resolve_globs                 # noqa: E402

# ⚠️ **`SELF` 曾漏掉審計報告最常用的自我指涉詞。** `[實測個案]`
#    一份真實的跨模型審計報告，結論寫「本專案目前的 Git 封裝腳本具備**極高的強健性**」、
#    「目前的腳本設計已經**堵死**了多數邊緣失效」、「**無待修復**的重大漏洞」——
#    **三個詞都在 `governance/Audit_Protocol.md` §3 的禁用清單裡，而本感測器判 PASS。**
#    根因不是 APPRAISAL 沒抓到（極高／堵死／無待修復三個都在裡面），
#    是 **SELF 不含「本輪」「本次」「本專案」（無「已」）**，於是共現條件不成立。
#    ⛔ **少報比誤報危險**——一個誤報會被追查，一個少報不會。
SELF = re.compile(r"本文件|本檔|本報告|本摘要|本清單|本版|文中所有|文中每|本工作流|"
                  r"本專案已|我已(?:全數|完整|逐一)|this (?:document|file|report|summary)")

# 🔴 **兩個自我指涉的範圍刻意不同，⛔ 不要把它們合併。**
#
#    `SELF`（窄）給 **FAIL 分支**用：判定「這份文件宣稱自己已查證無誤」。
#    ⚠️ 放寬它會誤報——實測：「本輪未完成的項目**全部**列在 §3，其中兩項尚未**查證**」
#    會同時命中 SELF(本輪)＋SCOPE(全部)＋OBJECT(查證)，**而那是一句誠實的揭露，不是背書。**
#    ⛔ 誤報一條誠實揭露，正是 `R-19` 要擋的：它會教人不要寫「我沒做完什麼」。
#
#    `SELF_WIDE`（寬）只給 **WARN 分支**用：判定「這份文件在稱讚它所談的東西」。
#    那種句子本來就會用「本輪」「本專案」「本次審計」當主詞。
SELF_WIDE = re.compile(SELF.pattern + r"|本輪|本次|本審計|本專案|"
                       r"this (?:round|audit|project)|the audit")
SCOPE = re.compile(r"所有|全部|全數|皆[經已無]|均[經已無]|無一|完全|一律|\ball\b|\bevery\b|\bzero\b")
OBJECT = re.compile(r"核實|查證|檢核|核對|驗證|無誤|零捏造|無捏造|確保.{0,6}效度|"
                    r"verified|cross-?checked|no fabricat")
MODAL = re.compile(r"不得|必須|應[當須]?|須要?|禁止|如果|若|除非|建議|should|must|shall|\bif\b")
TOOLPROOF = re.compile(r"`[^`]*\.(py|sh|md|json)`|scripts/|sensor_|run_[a-z_]+|[0-9a-f]{7,40}")
# ⚠️ **本清單的單一定義處是 `governance/Audit_Protocol.md` §3**（禁用：極高／完美／
#    非常強健／堵死／無漏洞／無待修復）。⛔ 本處只得「涵蓋它並可再多」，不得少於它。
#    實測個案：舊版寫 `非常(?:穩健|完善|嚴謹)`，**獨漏 §3 明文列出的「非常強健」**。
APPRAISAL = re.compile(r"(極高|非常(?:穩健|完善|嚴謹|強健)|已達到.{0,8}(?:水準|品質)|"
                       r"堪稱|無懈可擊|完美|堵死|無漏洞|無待修復)")


def main():
    root, cfg, as_json, name = cli("self_certification")
    files, dead = resolve_globs(cfg["artifact_globs"], root, cfg)
    findings = dead_glob_findings(dead, "artifact_globs", root)

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # ⛔ 不得靜默略過：讀不到 ≠ 沒問題
            findings.append(("INCOMPLETE", "FILE_NOT_DECODABLE",
                             f"{p.relative_to(root)} 非 UTF-8，本檔未檢查——**不等於通過**"))
            continue
        for para in text.split("\n\n"):
            if MODAL.search(para) or TOOLPROOF.search(para):
                continue                       # 閘門或可複核 → 豁免
            if SELF.search(para) and SCOPE.search(para) and OBJECT.search(para):
                findings.append(("FAIL", "UNVERIFIABLE_SELF_CERT",
                                 f"{p.relative_to(root)}：「{para.strip()[:52]}…」"
                                 "——產出物不得宣稱自己已查證無誤"))
                break
        for para in text.split("\n\n"):
            if TOOLPROOF.search(para):
                continue
            if APPRAISAL.search(para) and SELF_WIDE.search(para):
                findings.append(("WARN", "UNSUPPORTED_GLOBAL_APPRAISAL",
                                 f"{p.relative_to(root)}：整體性好評而無可複核憑據"))
                break

    return emit("自我背書感測器", findings, {"掃描產出物": len(files)}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
