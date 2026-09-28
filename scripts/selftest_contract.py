"""Validate the fixed v1.5 selftest inventory without trusting summary counts."""
import json
import pathlib
import re


def validate_output(output, lang):
    registry = json.loads(pathlib.Path(__file__).with_name('selftest_registry.json').read_text('utf-8'))
    expected = registry[lang]
    errors = []
    if not output.strip() or 'NO TESTS EXECUTED' in output:
        errors.append('empty or fake execution output (NO TESTS EXECUTED)')
    ordinary = []
    structured = {name: [] for name in expected['structured']}
    collections = {}
    for line in output.splitlines():
        text = line.strip()
        if text.startswith('✅'):
            ordinary.append(text[1:].strip())
        elif text.startswith('❌'):
            errors.append('failing ordinary case: ' + text[1:].strip())
        prefix, _, payload = text.partition(' ')
        if prefix in structured or prefix in expected['collections']:
            try:
                value = json.loads(payload)
                if not isinstance(value, dict):
                    raise ValueError('record is not an object')
            except (ValueError, TypeError):
                errors.append('malformed record: ' + prefix)
                continue
            if prefix in structured:
                key = 'model' if prefix == 'CHECKPOINT_MODEL_RESULT' else 'case'
                name = value.get(key)
                if key not in value or not (isinstance(name, str) or (key == 'model' and name is None)):
                    errors.append('missing or invalid case identity: ' + prefix)
                    continue
                structured[prefix].append(name)
                if value.get('passed') is not True or type(value.get('exit')) is not int or type(value.get('expected')) is not int or value['exit'] != value['expected']:
                    errors.append('failed/incomplete structured case: ' + prefix)
            else:
                collections.setdefault(prefix, []).append(value)
    if len(ordinary) != len(expected['ordinary']):
        errors.append('under-run or count mismatch in ordinary cases')
    if len(ordinary) != len(set(ordinary)):
        errors.append('duplicate test executions in ordinary cases')
    if set(ordinary) != set(expected['ordinary']):
        errors.append('test cases mismatch with expected registry')
    for prefix, names in expected['structured'].items():
        if len(structured[prefix]) != len(names) or set(structured[prefix]) != set(names):
            errors.append('structured case inventory mismatch or duplicate: ' + prefix)
    for prefix, count in expected['collections'].items():
        records = collections.get(prefix, [])
        wanted = dict(expected=count, executed=count, passed=count, failed=0, skipped=0)
        if len(records) != 1 or any(type(records[0].get(key)) is not int or records[0].get(key) != val for key, val in wanted.items()):
            errors.append('collection mismatch: ' + prefix)
    count = len(expected['ordinary']) + sum(len(x) for x in expected['structured'].values())
    pattern = r'^\s*通過\s+(\d+)\s+項｜失敗\s+(\d+)\s+項\s*$' if lang == 'zh' else r'^\s*passed\s+(\d+)\s+\|\s+failed\s+(\d+)\s*$'
    summaries = re.findall(pattern, output, re.MULTILINE)
    marker = '結果：自測全數通過' if lang == 'zh' else 'Result: all self-tests passed'
    if summaries != [(str(count), '0')] or marker not in output:
        errors.append('summary mismatch or missing success marker')
    return errors, {'expected_cases': count, 'ordinary_cases': len(ordinary), 'structured_cases': sum(len(x) for x in structured.values()), 'failed_checks': len(errors)}
