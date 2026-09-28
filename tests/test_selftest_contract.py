"""Result-contract negatives; real execution remains checked by fault injection."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from selftest_contract import validate_output


def contract_output(lang):
    registry = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'scripts/selftest_registry.json').read_text('utf-8'))[lang]
    lines = ['✅ ' + name for name in registry['ordinary']]
    for prefix, names in registry['structured'].items():
        key = 'model' if prefix == 'CHECKPOINT_MODEL_RESULT' else 'case'
        lines += [prefix + ' ' + json.dumps({key: name, 'passed': True, 'exit': 0, 'expected': 0}) for name in names]
    for prefix, count in registry['collections'].items():
        lines.append(prefix + ' ' + json.dumps(dict(expected=count, executed=count, passed=count, failed=0, skipped=0)))
    lines += ['通過 233 項｜失敗 0 項', '結果：自測全數通過'] if lang == 'zh' else ['passed 233 | failed 0', 'Result: all self-tests passed']
    return '\n'.join(lines)


@pytest.mark.parametrize('lang', ['zh', 'en'])
@pytest.mark.parametrize('change', ['none', 'missing', 'duplicate', 'malformed', 'failed', 'skip', 'summary', 'unknown', 'missing_identity', 'list_identity', 'dict_model'])
def test_structured_contract_rejects_incomplete_results(lang, change):
    text = contract_output(lang)
    lines = text.splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith('IDENTITY_RESULT '))
    if change == 'missing':
        lines.pop(index)
    elif change == 'duplicate':
        lines[index + 1] = lines[index]
    elif change == 'malformed':
        lines[index] = 'IDENTITY_RESULT {'
    elif change == 'failed':
        lines[index] = lines[index].replace('"passed": true', '"passed": false')
    elif change == 'skip':
        k = next(i for i, line in enumerate(lines) if line.startswith('IDENTITY_COLLECTION '))
        lines[k] = lines[k].replace('"skipped": 0', '"skipped": 1')
    elif change == 'summary':
        lines[-2] = lines[-2].replace('233', '232')
    elif change == 'unknown':
        lines[index] = lines[index].replace('user_partial', 'invented_case')
    elif change == 'missing_identity':
        value = json.loads(lines[index].partition(' ')[2])
        del value['case']
        lines[index] = 'IDENTITY_RESULT ' + json.dumps(value)
    elif change in ('list_identity', 'dict_model'):
        if change == 'dict_model':
            index = next(i for i, line in enumerate(lines) if line.startswith('CHECKPOINT_MODEL_RESULT '))
        prefix, _, payload = lines[index].partition(' ')
        value = json.loads(payload)
        value['model' if change == 'dict_model' else 'case'] = {} if change == 'dict_model' else []
        lines[index] = prefix + ' ' + json.dumps(value)
    errors, stats = validate_output('\n'.join(lines), lang)
    assert bool(errors) == (change != 'none')
    assert stats['expected_cases'] == 233
