"""Fixed external CLI oracle for sourced model records (no backend claims)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def record(model='Sol', source='user', status='reported'):
    return f'[Model: {model}]\n[Model source: {source}]\n[Model status: {status}]\n'


CASES = [
    ('user_partial', record(), 0, None),
    ('ui_partial', record(source='ui'), 0, None),
    ('environment_partial', record('Future Family', 'environment', 'read'), 0, None),
    ('future_name_no_allowlist', record('Unlisted Name'), 0, None),
    ('unknown', record('unknown', 'unknown', 'unknown'), 0, 'MODEL_UNREADABLE_DECLARED'),
    ('declared_conflict', record('unknown', 'conflict', 'conflict'), 0, 'MODEL_IDENTITY_CONFLICT_DECLARED'),
    ('missing', '# No identity\n', 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('partial_no_source', '[Model: Sol]\n', 1, 'MODEL_ATTRIBUTION_VAGUE'),
    ('missing_status', '[Model: Sol]\n[Model source: user]\n', 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('missing_source', '[Model: Sol]\n[Model status: reported]\n', 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('invented_source', record(source='telepathy'), 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('user_claims_read', record(status='read'), 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('unknown_claims_reported', record('unknown'), 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('known_claims_unknown', record('Sol','unknown','unknown'), 1, 'MODEL_ATTRIBUTION_STATE_INVALID'),
    ('duplicate_conflict', record()+'[Model: Opus]\n', 1, 'MODEL_ATTRIBUTION_CONFLICT'),
    ('author_conflict', record()+'**Author:** Opus, date unknown\n', 1, 'MODEL_ATTRIBUTION_CONFLICT'),
    ('source_conflict', record()+'[Model source: ui]\n', 1, 'MODEL_ATTRIBUTION_CONFLICT'),
    ('duplicate_same', record()+'[Model: Sol]\n', 0, None),
    ('platform', record('ChatGPT'), 1, 'MODEL_ATTRIBUTION_VAGUE'),
    ('placeholder', record('...'), 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('empty', record(''), 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('quoted_example', '```text\n'+record()+'```\n', 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('inline_example', 'Example: [Model: Sol]\n', 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('outside_header', '\n'*15+record(), 1, 'MODEL_ATTRIBUTION_MISSING'),
    ('legacy', '[Model: model-7]\n', 0, 'MODEL_SOURCE_UNRECORDED'),
    ('legacy_unknown', '[Model: cannot read — field unavailable]\n', 0, 'MODEL_UNREADABLE_DECLARED'),
    ('non_utf8', b'\xff\xfe\x00', 2, 'FILE_NOT_DECODABLE'),
]



def run_display_cases(here):
    """Exercise the actual CLI, including a second full scan of changed input."""
    passed = failed = 0
    with tempfile.TemporaryDirectory(prefix='s2g_source_display_') as temp:
        root=Path(temp);(root/'handoffs').mkdir()
        for n in range(3):
            (root/f'handoffs/old{n}.md').write_text('[Model: model-7]\n',encoding='utf-8')
        steps=[('legacy_summary',False,0),('legacy_json',True,0),
               ('new_missing_visible',False,1),('unknown_conflict_visible',False,0),
               ('unreadable_visible',True,2)]
        for name,as_json,want in steps:
            if name=='new_missing_visible':
                (root/'handoffs/new.md').write_text('# Missing model\n',encoding='utf-8')
            if name=='unknown_conflict_visible':
                (root/'handoffs/new.md').write_text(record('unknown','conflict','conflict'),encoding='utf-8')
                (root/'handoffs/unknown.md').write_text(record('unknown','unknown','unknown'),encoding='utf-8')
            if name=='unreadable_visible':
                (root/'handoffs/binary.md').write_bytes(b'\xff\xfe')
            started=time.time();print('IDENTITY_START '+name,flush=True)
            args=[sys.executable,'-B',str(here/'sensor_model_attribution.py'),'--root',str(root)]
            if as_json:args.append('--json')
            try:
                p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20,
                    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1'))
                out=p.stdout+p.stderr;good=p.returncode==want
                if as_json:
                    data=json.loads(p.stdout);rows=data['findings'];stats=list(data['stats'].values())
                    good=good and len([r for r in rows if r['code']=='MODEL_SOURCE_UNRECORDED'])==3
                    good=good and all(any(r['message'].startswith(tuple(str(Path('handoffs')/f'old{n}.md')+sep for sep in (':','：'))) for r in rows) for n in range(3))
                    good=good and stats==([3,3] if name=='legacy_json' else [6,5])
                    if name=='unreadable_visible':good=good and data['status']=='INCOMPLETE' and 'FILE_NOT_DECODABLE' in out
                else:
                    good=good and out.count('[WARN] MODEL_SOURCE_UNRECORDED_SUMMARY:')==1
                    good=good and str(Path('handoffs')/'old0.md') not in out and '3' in out
                    if name=='new_missing_visible':good=good and 'MODEL_ATTRIBUTION_MISSING' in out and str(Path('handoffs')/'new.md') in out
                    if name=='unknown_conflict_visible':good=good and 'MODEL_IDENTITY_CONFLICT_DECLARED' in out and 'MODEL_UNREADABLE_DECLARED' in out
                item=dict(case=name,started_unix=started,ended_unix=time.time(),seconds=time.time()-started,exit=p.returncode,expected=want,passed=good,stdout=p.stdout,stderr=p.stderr)
            except (subprocess.TimeoutExpired,ValueError,KeyError) as exc:
                good=False;item=dict(case=name,passed=False,error=repr(exc),seconds=time.time()-started)
            print('IDENTITY_RESULT '+json.dumps(item,ensure_ascii=True),flush=True)
            passed+=int(good);failed+=int(not good)
    print('IDENTITY_DISPLAY_COLLECTION '+json.dumps(dict(expected=len(steps),executed=passed+failed,passed=passed,failed=failed,skipped=len(steps)-passed-failed)),flush=True)
    return passed,failed

def run_cases(here):
    passed = failed = 0
    for name, body, want, needle in CASES:
        start=time.time()
        with tempfile.TemporaryDirectory(prefix='s2g_identity_') as temp:
            root=Path(temp);(root/'handoffs').mkdir()
            (root/'handoffs/record.md').write_bytes(body if isinstance(body,bytes) else body.encode())
            args=[sys.executable,'-B',str(here/'sensor_model_attribution.py'),'--root',str(root)]
            print('IDENTITY_START '+name,flush=True)
            try:
                p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20,
                    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1'))
                out=p.stdout+p.stderr
                # Positive sourced cases require no warning at all, not just exit zero.
                good=(p.returncode==want and (needle in out if needle else '[WARN]' not in out and '[FAIL]' not in out and '[INCOMPLETE]' not in out))
                if want==0 and needle:
                    good=good and '[FAIL]' not in out and '[INCOMPLETE]' not in out
                item=dict(case=name,exit=p.returncode,expected=want,required_code=needle,passed=good,stdout=p.stdout,stderr=p.stderr)
            except subprocess.TimeoutExpired as e:
                good=False;item=dict(case=name,passed=False,timeout=True,stdout=repr(e.stdout),stderr=repr(e.stderr))
            item['seconds']=time.time()-start
            print('IDENTITY_RESULT '+json.dumps(item,ensure_ascii=True),flush=True)
            if good:passed+=1
            else:failed+=1
    extra_passed,extra_failed=run_display_cases(here)
    passed+=extra_passed;failed+=extra_failed
    print('IDENTITY_COLLECTION '+json.dumps(dict(expected=len(CASES)+5,executed=passed+failed,passed=passed,failed=failed,skipped=len(CASES)+5-passed-failed)),flush=True)
    return passed,failed


if __name__=='__main__':
    good,bad=run_cases(Path(__file__).resolve().parent)
    raise SystemExit(bool(bad))
