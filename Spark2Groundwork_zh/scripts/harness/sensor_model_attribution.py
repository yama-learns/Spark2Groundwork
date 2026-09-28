#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型歸屬感測器：檢查紀錄是否一致，⛔ 不驗證後端身份。

契約：governance/MODEL_IDENTITY.md §3.4 與 governance/HANDOFF.md §3。
掃描範圍仍是 attribution_globs（預設 handoffs/*.md）；沒有型號白名單。
新格式以來源／狀態配對型號名稱或明示 unknown。帶版本數字的舊格式仍可讀，
但會提示未記來源；數字不能認證型號。如實宣告未知或衝突不算文件不合格，
提示也不要求使用者反覆確認。
退出碼：0 無失敗，1 紀錄無效，2 檢查未完成。WARN 保持可見。
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import cli, emit, dead_glob_findings  # noqa: E402
from framework_config import resolve_globs  # noqa: E402

FIELD = re.compile(r"^\s*\[Model(?P<kind> source| status)?:\s*(?P<value>[^\]\r\n]*)\]\s*$", re.I)
AUTHOR_FIELD = re.compile(r"^\*{0,2}(?:建立|作者|撰寫|執行模型|Created|Author|Model)"
                          r"\*{0,2}\s*[:：]\s*\*{0,2}\s*([^\n，,]+)", re.I)
UNREADABLE = re.compile(r"^(?:unknown|未知|無法讀取|cannot read|unreadable|not in the visible context)(?:$|\s|[—–:：-])", re.I)
PLATFORMS = {"antigravity", "cowork", "claude code", "ai studio", "gemini app",
             "chatgpt", "copilot", "openai", "anthropic", "google"}
PAIRS = {"environment": "read", "user": "reported", "ui": "reported",
         "unknown": "unknown", "conflict": "conflict"}
HEAD_LINES = 15


def header_fields(text):
    """只讀整行檔頭欄位；忽略檔頭內的程式碼示例。"""
    values = {"model": [], "source": [], "status": []}
    fence = None
    for line in text.splitlines()[:HEAD_LINES]:
        mark = re.match(r"^\s*(`{3,}|~{3,})", line)
        if mark:
            token = mark[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        m = FIELD.fullmatch(line)
        if m:
            key = (m['kind'] or 'model').strip().lower()
            values[key].append(m['value'].strip())
        else:
            m = AUTHOR_FIELD.match(line)
            if m:
                values['model'].append(m[1].strip())
    return values


def inspect_record(text):
    fields = header_fields(text)
    if not fields['model'] or any(not v or v == '...' for items in fields.values() for v in items):
        return 'FAIL', 'MODEL_ATTRIBUTION_MISSING', '必要的型號值缺漏或仍是模板省略號。'
    if any(len({v.casefold() for v in items}) > 1 for items in fields.values()):
        return 'FAIL', 'MODEL_ATTRIBUTION_CONFLICT', '檔頭欄位值互相矛盾；請保留各來源並釐清。'
    who = fields['model'][0]
    source = fields['source'][0].lower() if fields['source'] else None
    status = fields['status'][0].lower() if fields['status'] else None
    unknown = bool(UNREADABLE.search(who))
    if source is not None or status is not None:
        if source not in PAIRS or PAIRS[source] != status:
            return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', '來源／狀態缺漏、不在取值表內或彼此不相容。'
        if source in ('unknown', 'conflict'):
            if not unknown:
                return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', '未知／衝突狀態不得同時寫出已確認的型號。'
            if source == 'conflict':
                return 'WARN', 'MODEL_IDENTITY_CONFLICT_DECLARED', '已如實宣告來源衝突；只有任務資格需要時才釐清。'
            return 'WARN', 'MODEL_UNREADABLE_DECLARED', '型號未知；普通工作可繼續，不必反覆詢問。'
        if unknown:
            return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', '未知值不能標為 read 或 reported 的型號。'
        if who.casefold() in PLATFORMS:
            return 'FAIL', 'MODEL_ATTRIBUTION_VAGUE', '平台名不是型號；請記已知型號或 unknown。'
        return None
    # 舊格式相容：明示不是來源或後端證據。
    if unknown:
        return 'WARN', 'MODEL_UNREADABLE_DECLARED', '舊格式的未知宣告；不需要反覆確認。'
    if who.casefold() in PLATFORMS or not re.search(r'\d', who):
        return 'FAIL', 'MODEL_ATTRIBUTION_VAGUE', '舊格式只有名稱而無版本，請補記實際來源／狀態。'
    return 'WARN', 'MODEL_SOURCE_UNRECORDED', '舊格式歸屬可讀，但未記來源，也未經認證。'


def human_findings(findings):
    """Summarise only legacy source notices after the complete scan."""
    count = sum(level == 'WARN' and code == 'MODEL_SOURCE_UNRECORDED'
                for level, code, _ in findings)
    if not count:
        return findings
    result, shown = [], False
    for item in findings:
        if item[:2] == ('WARN', 'MODEL_SOURCE_UNRECORDED'):
            if not shown:
                message = ('{count} 份歷史紀錄未載來源；這不是新增錯誤，不需逐份追補。' '使用 --json 查看完整路徑與逐筆明細。').format(count=count)
                result.append(('WARN', 'MODEL_SOURCE_UNRECORDED_SUMMARY', message))
                shown = True
        else:
            result.append(item)
    return result


def main():
    root, cfg, as_json, name = cli('model_attribution')
    files, dead = resolve_globs(cfg.get('attribution_globs', ['handoffs/*.md']), root, cfg)
    findings = dead_glob_findings(dead, 'attribution_globs', root)
    checked = 0
    for p in files:
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            findings.append(('INCOMPLETE', 'FILE_NOT_DECODABLE', f'{p.relative_to(root)}：無法以 UTF-8 讀取，⛔ 未檢查 ≠ 通過。'))
            continue
        checked += 1
        result = inspect_record(text)
        if result:
            level, code, message = result
            findings.append((level, code, f'{p.relative_to(root)}：{message}'))
    display = findings if as_json else human_findings(findings)
    return emit('模型歸屬感測器', display, {'掃描產出物': len(files), '已檢查': checked}, as_json, name)


if __name__ == '__main__':
    sys.exit(main())
