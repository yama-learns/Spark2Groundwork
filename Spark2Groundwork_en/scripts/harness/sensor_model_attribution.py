#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Model attribution: record consistency, not backend authentication.

Contract: governance/MODEL_IDENTITY.md §3.4 and governance/HANDOFF.md §3.
Scope remains attribution_globs (default handoffs/*.md). No model allowlist.
New records pair source/status with a model name or explicit unknown. Legacy
version-bearing headers remain readable with a missing-source notice; a digit
does not authenticate a model. Unknown and honestly declared conflicts are
not document failures. Notices do not require repeated user confirmation.
Exit: 0 no failure, 1 invalid record, 2 incomplete check. Warnings remain visible.
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
    """Read whole-line headers only; ignore code examples within the header."""
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
        return 'FAIL', 'MODEL_ATTRIBUTION_MISSING', 'A required model value is absent or a placeholder.'
    if any(len({v.casefold() for v in items}) > 1 for items in fields.values()):
        return 'FAIL', 'MODEL_ATTRIBUTION_CONFLICT', 'Header values disagree; retain and clarify the sources.'
    who = fields['model'][0]
    source = fields['source'][0].lower() if fields['source'] else None
    status = fields['status'][0].lower() if fields['status'] else None
    unknown = bool(UNREADABLE.search(who))
    if source is not None or status is not None:
        if source not in PAIRS or PAIRS[source] != status:
            return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', 'Source/status is missing, unsupported or incompatible.'
        if source in ('unknown', 'conflict'):
            if not unknown:
                return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', 'Unknown/conflicting identity must not name a confirmed model.'
            if source == 'conflict':
                return 'WARN', 'MODEL_IDENTITY_CONFLICT_DECLARED', 'Conflicting sources declared; clarify only where task eligibility requires it.'
            return 'WARN', 'MODEL_UNREADABLE_DECLARED', 'Identity is unknown; ordinary work may continue without repeated questions.'
        if unknown:
            return 'FAIL', 'MODEL_ATTRIBUTION_STATE_INVALID', 'An unknown value cannot be marked read or reported as a model.'
        if who.casefold() in PLATFORMS:
            return 'FAIL', 'MODEL_ATTRIBUTION_VAGUE', 'A platform name is not a model; record the known model or unknown.'
        return None
    # Historical compatibility, explicitly not evidence of a source or backend.
    if unknown:
        return 'WARN', 'MODEL_UNREADABLE_DECLARED', 'Legacy unknown declaration; no repeated confirmation is required.'
    if who.casefold() in PLATFORMS or not re.search(r'\d', who):
        return 'FAIL', 'MODEL_ATTRIBUTION_VAGUE', 'A legacy name without a version needs its actual source/status recorded.'
    return 'WARN', 'MODEL_SOURCE_UNRECORDED', 'Legacy attribution is readable; its source was not recorded or authenticated.'


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
                message = ('{count} historical records have no recorded source; this is not a new error. ' 'No per-file backfill is required. Use --json for the full path/detail list.').format(count=count)
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
            findings.append(('INCOMPLETE', 'FILE_NOT_DECODABLE', f'{p.relative_to(root)}: cannot read UTF-8; not checked.'))
            continue
        checked += 1
        result = inspect_record(text)
        if result:
            level, code, message = result
            findings.append((level, code, f'{p.relative_to(root)}: {message}'))
    display = findings if as_json else human_findings(findings)
    return emit('Model attribution', display, {'files_found': len(files), 'files_checked': checked}, as_json, name)


if __name__ == '__main__':
    sys.exit(main())
