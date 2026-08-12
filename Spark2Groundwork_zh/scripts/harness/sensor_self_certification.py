#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感測器：產出物自我背書（失效家族⑦）

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

SELF = re.compile(r"本文件|本檔|本報告|本摘要|本清單|本版|文中所有|文中每|本工作流|"
                  r"本專案已|我已(?:全數|完整|逐一)|this (?:document|file|report|summary)")
SCOPE = re.compile(r"所有|全部|全數|皆[經已無]|均[經已無]|無一|完全|一律|\ball\b|\bevery\b|\bzero\b")
OBJECT = re.compile(r"核實|查證|檢核|核對|驗證|無誤|零捏造|無捏造|確保.{0,6}效度|"
                    r"verified|cross-?checked|no fabricat")
MODAL = re.compile(r"不得|必須|應[當須]?|須要?|禁止|如果|若|除非|建議|should|must|shall|\bif\b")
TOOLPROOF = re.compile(r"`[^`]*\.(py|sh|md|json)`|scripts/|sensor_|run_[a-z_]+|[0-9a-f]{7,40}")
APPRAISAL = re.compile(r"(極高|非常(?:穩健|完善|嚴謹)|已達到.{0,8}(?:水準|品質)|"
                       r"堪稱|無懈可擊|完美|堵死|無漏洞|無待修復)")


def main():
    root, cfg, as_json, name = cli("self_certification")
    files, dead = resolve_globs(cfg["artifact_globs"], root, cfg)
    findings = dead_glob_findings(dead, "artifact_globs")

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
            if APPRAISAL.search(para) and SELF.search(para):
                findings.append(("WARN", "UNSUPPORTED_GLOBAL_APPRAISAL",
                                 f"{p.relative_to(root)}：整體性好評而無可複核憑據"))
                break

    return emit("自我背書感測器", findings, {"掃描產出物": len(files)}, as_json, name)


if __name__ == "__main__":
    sys.exit(main())
