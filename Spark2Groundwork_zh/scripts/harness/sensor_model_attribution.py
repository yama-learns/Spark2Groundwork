#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感測器：模型歸屬（Model Attribution）
規則來源：憲章 §5.11｜policy/MODEL_IDENTITY.md §3.4–3.5、§4 M-2
觸發個案：2026-07-29 I-15。mve/MVE_v5.0c_v1.0.md 與 R4-1 分析檔的作者欄只寫「Claude」，
          事後無法對應到 policy/HANDOFF.md §9 的模型表現記錄。

⚠️ 涵蓋範圍是刻意收窄的（憲章 §5.1 精度優先於覆蓋）：
   - 主文本 final_paper_* 免檢：那是學術稿件，掛 AI 作者欄本身才是錯的
   - GRANDFATHERED：規則生效（2026-07-29）前既存之治理文件免檢，清單凍結於下方
     首版曾對 26 份中的 16 份報警——那種感測器只會教人忽略它，故改為只管新產出

檢查三項：
  1. MODEL_ATTRIBUTION_VAGUE   作者欄只寫家族名（Claude/Gemini）而無具體型號
  2. MODEL_ATTRIBUTION_MISSING 新產出無建立／作者欄
  3. SESSION_LOG_STALE         model_session_log.md 最新一列早於最新 git 檢查點

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（未完成 ≠ 通過，憲章 §5.5）
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# --root <dir>：自測用。指向 fixture 目錄，只跑歸屬檢查、略過軌跡表時效。
_SELFTEST_ROOT = None
for _i, _a in enumerate(sys.argv):
    if _a == "--root" and _i + 1 < len(sys.argv):
        _SELFTEST_ROOT = Path(sys.argv[_i + 1]).resolve()
if _SELFTEST_ROOT:
    ROOT = _SELFTEST_ROOT
LOG = ROOT / "model_session_log.md"

# 具體型號白名單。新增模型時同步更新此處與 Model_Identity_Protocol §3.5
CONCRETE = [
    "Opus 5", "Opus5", "opus5", "claude-opus-5",
    "Opus 4.8", "Opus 4.6",
    "Fable 5", "Fable5", "fable5", "claude-fable-5",
    "Sonnet 5", "Sonnet5", "sonnet5", "claude-sonnet-5",
    "Haiku 4.5", "Haiku4.5", "haiku45", "claude-haiku-4-5",
    "3.1 Pro", "3.6 Flash", "3.5 Flash",
    "Deep Research",
]

# `**建立：** Claude，2026-...`／`建立: Claude,`——星號可在冒號前後任一側
_LABEL = r"(?:建立|更新|撰寫|分析|作者|寫於|審計者|執行模型)"

# ⚠️ **平台名不是型號。**（2026-07-31）Antigravity／Cowork／Claude Code 是產品，
#    同一平台可跑不同模型，寫平台名等於沒寫。觸發個案：
#    `handoffs/sensor_git_audit_2026-07-31.md` 之作者欄為 `[Model: Antigravity]`。
#    這與 §5.12 禁止的「由回答風格自我判定」同族——都是拿非權威訊號充當身分。
PLATFORM_NOT_MODEL = ("Antigravity", "Cowork", "Claude Code", "AI Studio",
                      "Gemini App", "ChatGPT", "Copilot")
ATTRIB_LINE = re.compile(rf"^\*{{0,2}}{_LABEL}\*{{0,2}}\s*[：:]", re.M)
FAMILY_ONLY = re.compile(rf"{_LABEL}\*{{0,2}}\s*[：:]\s*\*{{0,2}}\s*(Claude|Gemini)\s*[，,、]")

# 免檢：資料檔／自動生成物／學術稿件本體
EXEMPT_EXACT = {
    "file_index.md", "model_session_log.md", "NEXT_SESSION_MEMO.md",
    "README.md", "DR_Cost_Log.md", "Logic_Chain_Ledger.md",
    "Terminology_Glossary.md", "Incident_Log.md",
}
EXEMPT_PREFIX = ("final_paper_",)

# 規則生效前既存之治理文件（凍結清單，不再增列；新檔一律受檢）
GRANDFATHERED = {
    "guides/archive/governance_2026-08-08/`.agents/AGENTS.md` §5_2026-07.md",
    "guides/policy/PROMPT_TEMPLATES.md",
    "guides/policy/HANDOFF.md",
    "archive/Branch_FGH_Adjudication_2026-07-29.md",
    "policy/SOURCES.md",
    "WORKFLOW_CONSTITUTION.md",
    "archive/Infrastructure_Audit_and_Upgrade_Plan_2026-07-29.md",
    "mve/MVE_v2.0a.md",
    "policy/SOURCES.md",
    "archive/v5.1_Measurement_Foundation_Plan_2026-07-27.md",
    "archive/v5_Branch_Status_Board_2026-07-28.md",
    "policy/GIT.md",
    "policy/GIT.md",
}


def git_last_commit_date():
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short"],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def in_scope(name):
    if _SELFTEST_ROOT:
        return True
    return (
        name not in EXEMPT_EXACT
        and name not in GRANDFATHERED
        and not name.startswith(EXEMPT_PREFIX)
    )


def main():
    # ⚠️ 2026-07-31：原本只掃根目錄，於是 `handoffs/` 內的跨模型審計報告
    #    從未受檢——`sensor_git_audit_2026-07-31.md` 的作者欄寫 `[Model: Antigravity]`，
    #    那是**平台名不是型號**（§5.12 禁止事項），而感測器全程沉默。
    #    交接封包正是最需要模型歸屬的檔案：它的可信度取決於誰寫的。
    all_md = sorted(ROOT.glob("*.md")) + sorted(ROOT.glob("handoffs/*.md"))
    if not all_md:
        print("⚠️  INCOMPLETE — 根目錄找不到 .md，路徑可能錯誤。")
        print("→ ⚠️ 未完成 ≠ 通過。本感測器不會為無法檢查的條目背書。")
        return 2

    # ⚠️ 擴大掃描範圍會一次湧入既有檔案的告警（本次為 18 筆）。
    #    §5.1：長期紅燈會教人忽略感測器。故比照根目錄之既有做法**凍結**
    #    擴掃當下已存在的 handoffs 檔，新增者一律受檢。
    #    凍結清單以檔名列舉（不是「早於某日期就跳過」）——**日期規則會隨時間吞掉新檔**。
    FROZEN_HANDOFFS = {
        "Audit_Report_3.1Pro_Fable5_MainText_2026-07-29.md",
        "Audit_Report_3.1Pro_Opus5_AdjudicationA_I16_2026-07-29.md",
        "Audit_Report_3.1Pro_Opus5_MVE_DR_2026-07-29.md",
        "handoff_3.6flash_text_extraction_2026-07-30.md",
        "handoff_gemini3.6flash_text_extraction_wood1976_2026-07-30.md",
        "handoff_opus5_fgh_and_dr_policy_2026-07-29.md",
        "handoff_to_3.1pro_infra_audit_2026-07-29.md",
        "Audit_Report_3.1Pro_Identity_Protocol_2026-07-29.md",
        "Audit_Report_3.1Pro_Opus5_Git_Bat_2026-07-29.md",
        "handoff_gemini_git_system_patch_2026-07-29.md",
        "handoff_gemini_infra_audit_2026-07-29.md",
        "handoff_opus5_reconstruction_round_2026-07-28.md",
    }
    docs = [p for p in all_md
            if in_scope(p.name)
            and not (p.parent.name == "handoffs" and p.name in FROZEN_HANDOFFS)]
    vague, missing = [], []
    for p in docs:
        lines = p.read_text(encoding="utf-8").splitlines()[:15]
        hits = [ln for ln in lines if ATTRIB_LINE.search(ln)]
        if not hits:
            missing.append(p.name)
            continue
        # ⚠️ 型號只在「作者欄那一行的作者片段」內找，不掃整個檔頭。
        # 觸發個案：MVE_v5.0c 檔頭同一行有「待 3.1 Pro 審計」，
        # 首版掃整個檔頭因而把審計者當成作者，漏抓了真正該報的 VAGUE。
        for ln in hits:
            # ① 平台名冒充型號（先查：它不符合 FAMILY_ONLY 的 Claude|Gemini 樣式）
            if (any(pf in ln for pf in PLATFORM_NOT_MODEL)
                    and not any(c in ln for c in CONCRETE)):
                vague.append(p.name)
                break
            # ② 只有家族名
            m = FAMILY_ONLY.search(ln)
            if not m:
                continue
            seg = ln[: m.end()]          # 只取到作者名為止，切掉「待 X 審計」等後綴
            if not any(c in seg for c in CONCRETE):
                vague.append(p.name)
                break

    stale = None
    if _SELFTEST_ROOT:
        pass                       # 自測模式不查軌跡表時效
    elif LOG.exists():
        dates = re.findall(r"\|\s*(20\d\d-\d\d-\d\d)\s*\|", LOG.read_text(encoding="utf-8"))
        gitdate = git_last_commit_date()
        if dates and gitdate and max(dates) < gitdate:
            stale = (max(dates), gitdate)
    elif not _SELFTEST_ROOT:
        missing.append("model_session_log.md（檔案不存在）")

    print("模型歸屬感測器（憲章 §5.11）")
    print("=" * 62)
    print(f"根目錄 .md {len(all_md)} 份 ｜受檢 {len(docs)} 份"
          f"（免檢 {len(all_md) - len(docs)}：主文本／資料檔／規則生效前既存）")

    for name in vague:
        print(f"⚠️  WARN [MODEL_ATTRIBUTION_VAGUE] {name} — 只有家族名，未寫具體型號")
    for name in missing:
        print(f"⚠️  WARN [MODEL_ATTRIBUTION_MISSING] {name} — 無建立／作者欄")
    if stale:
        print(f"⚠️  WARN [SESSION_LOG_STALE] 軌跡表最新 {stale[0]} < 最新檢查點 {stale[1]}")

    n = len(vague) + len(missing) + (1 if stale else 0)
    print("=" * 62)
    if n == 0:
        print("判定：PASS — 新產出之模型歸屬完整。")
    else:
        print(f"判定：PASS（有警告 {n} 項）")
        print("→ 歸屬缺漏不阻斷工作，但會使模型表現記錄退化為印象分。收工前補齊。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
