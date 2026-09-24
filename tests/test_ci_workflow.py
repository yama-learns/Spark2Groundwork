#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for CI-0 GitHub Actions workflow and repository hygiene contracts (CI-0 r6)."""
import ast
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import importlib.util
from types import SimpleNamespace
import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "ci.yml"

sys.path.insert(0, str(ROOT / "scripts"))
import check_repo_hygiene


@pytest.mark.parametrize('lang', ['zh', 'en'])
@pytest.mark.parametrize('response', ['valid', 'generic_failure', 'not_loaded', 'stale_pass', 'wrong_exit'])
def test_fault_control_requires_loaded_named_case(tmp_path, monkeypatch, lang, response):
    """Exercise the checker, including the sensor it writes, using a tiny runner.

    Deliberate stubs here test result validation, not product execution coverage;
    the complete product runner is exercised separately by --check-disposable.
    """
    sensor = 'sensor_claim_ledger.py'
    case = check_repo_hygiene.FAULT_CASES[lang][sensor]
    monkeypatch.setattr(check_repo_hygiene.secrets, 'choice',
                        lambda values: sensor if isinstance(values[0], str) else 0)
    harness = tmp_path / 'scripts/harness'
    harness.mkdir(parents=True)
    (harness / 'selftest' / case['fixture']).mkdir(parents=True)
    (harness / sensor).write_text('original = True\n', 'utf-8')
    detail = f" (expected exit {case['code']}, got 0)" if lang == 'en' else f"（期望 exit {case['code']}，實得 0）"
    line = '❌ ' + case['case'] + detail
    runner = (
        'import pathlib, subprocess, sys\n'
        'h = pathlib.Path(__file__).resolve().parent\n'
        + (f"subprocess.run([sys.executable, '-B', str(h/{sensor!r}), '--root', str(h/'selftest'/{case['fixture']!r})], check=True)\n"
           if response != 'not_loaded' else '')
        + f"print({(line if response != 'generic_failure' else 'passed 179 | failed 0')!r})\n"
        + (f"print({('✅ ' + case['case'])!r})\n" if response == 'stale_pass' else '')
        + f"raise SystemExit({2 if response == 'wrong_exit' else 1})\n"
    )
    (harness / 'run_selftest.py').write_text(runner, 'utf-8')
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    errors, records = check_repo_hygiene.check_fault_propagation(tmp_path, lang, '✅ '+case['case'], env)
    assert bool(errors) == (response != 'valid')
    assert records[-1]['passed'] == (response == 'valid')
    assert (harness / sensor).read_text('utf-8') == 'original = True\n'


@pytest.mark.parametrize('lang', ['zh', 'en'])
def test_checkpoint_reads_changed_content_despite_same_stat(tmp_path, monkeypatch, lang):
    """CI0-O1 deterministic regression; also protect adds/deletes/ignore/reviewed."""
    def git(*args):
        r = subprocess.run(['git', '-C', str(tmp_path), *args], capture_output=True, timeout=20)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()
    git('init', '-q')
    git('config', 'user.name', 'CI fixture')
    git('config', 'user.email', 'ci@local')
    git('config', 'core.trustctime', 'false')
    git('config', 'core.checkStat', 'minimal')
    (tmp_path / 'governance').mkdir()
    for name in ('AGENTS.md', 'WORKFLOW_CONSTITUTION.md'):
        (tmp_path / 'governance' / name).write_text('fixture\n', 'utf-8')
    (tmp_path / '.gitignore').write_text('ignored.txt\ngit-checkpoint.log\n', 'utf-8')
    changed = tmp_path / 'sample.txt'
    changed.write_bytes(b'old\n')
    os.utime(changed, (1600000000, 1600000000))
    (tmp_path / 'delete.txt').write_bytes(b'delete\n')
    for name in ('hidden-assume.txt', 'hidden-skip.txt', '中文 [literal].txt'):
        (tmp_path / name).write_bytes(b'old\n')
    git('add', '.')
    git('commit', '-qm', 'baseline')
    git('tag', 'reviewed')
    reviewed = git('rev-parse', 'reviewed')
    git('update-index', '--assume-unchanged', '--', 'hidden-assume.txt')
    git('update-index', '--skip-worktree', '--', 'hidden-skip.txt')
    for name in ('hidden-assume.txt', 'hidden-skip.txt', '中文 [literal].txt'):
        (tmp_path / name).write_bytes(b'new\n')
    changed.write_bytes(b'new\n')
    os.utime(changed, (1600000000, 1600000000))
    (tmp_path / 'delete.txt').unlink()
    (tmp_path / 'added.txt').write_bytes(b'added\n')
    (tmp_path / 'ignored.txt').write_bytes(b'ignored\n')
    expected = git('hash-object', '--path=sample.txt', '--', str(changed))
    checkpoint = ROOT / f'Spark2Groundwork_{lang}/scripts/harness/checkpoint.py'
    r = subprocess.run([sys.executable, '-B', str(checkpoint), '--root', str(tmp_path),
                        '--mode', 'tool', '--tool-id', 'upgrade', '--operation', 'stat-test'],
                       capture_output=True, timeout=30,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1'))
    assert r.returncode == 0, r.stdout + r.stderr
    assert git('rev-parse', 'HEAD:sample.txt') == expected
    assert git('show', 'HEAD:added.txt') == b'added'
    assert git('show', 'HEAD:中文 [literal].txt') == b'new'
    for name in ('hidden-assume.txt', 'hidden-skip.txt'):
        assert git('show', 'HEAD:' + name) == b'old'
        assert (tmp_path / name).read_bytes() == b'new\n'
    files = git('ls-tree', '-r', '--name-only', 'HEAD').splitlines()
    assert b'delete.txt' not in files and b'ignored.txt' not in files
    assert git('rev-parse', 'reviewed') == reviewed
    head = git('rev-parse', 'HEAD')
    spec = importlib.util.spec_from_file_location('checkpoint_under_test', checkpoint)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(sys, 'argv', [str(checkpoint), '--root', str(tmp_path),
                                    '--mode', 'tool', '--tool-id', 'upgrade', '--operation', 'stat-test'])
    assert module.main(module.MSG) == 0
    assert git('rev-parse', 'HEAD') == head  # no-op stays a no-op
    real_run = module.run
    def fail_renormalize(argv, root, log):
        return (17, 'injected staging failure') if '--renormalize' in argv else real_run(argv, root, log)
    monkeypatch.setattr(module, 'run', fail_renormalize)
    changed.write_bytes(b'another change\n')
    assert module.main(module.MSG) == 2
    assert git('rev-parse', 'HEAD') == head
    assert git('rev-parse', 'reviewed') == reviewed


@pytest.mark.parametrize('lang', ['zh', 'en'])
def test_checkpoint_falls_back_when_git_lacks_pathspec_from_file(tmp_path, monkeypatch, lang):
    """Git < 2.25 has no `add --pathspec-from-file`; the checkpoint must still work.

    ⛔ The fallback is only for an option-level rejection. A real staging failure
    must still refuse to commit and return 2.
    """
    def git(*args):
        r = subprocess.run(['git', '-C', str(tmp_path), *args], capture_output=True, timeout=20)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()
    git('init', '-q')
    git('config', 'user.name', 'CI fixture')
    git('config', 'user.email', 'ci@local')
    git('config', 'core.trustctime', 'false')
    git('config', 'core.checkStat', 'minimal')
    (tmp_path / 'governance').mkdir()
    for name in ('AGENTS.md', 'WORKFLOW_CONSTITUTION.md'):
        (tmp_path / 'governance' / name).write_text('fixture\n', 'utf-8')
    (tmp_path / '.gitignore').write_text('git-checkpoint.log\n', 'utf-8')
    changed = tmp_path / 'sample.txt'
    changed.write_bytes(b'old\n')
    os.utime(changed, (1600000000, 1600000000))
    (tmp_path / '中文 [literal].txt').write_bytes(b'old\n')
    git('add', '.')
    git('commit', '-qm', 'baseline')
    git('tag', 'reviewed')
    reviewed = git('rev-parse', 'reviewed')
    head = git('rev-parse', 'HEAD')
    changed.write_bytes(b'new\n')
    os.utime(changed, (1600000000, 1600000000))
    (tmp_path / '中文 [literal].txt').write_bytes(b'new\n')
    expected = git('hash-object', '--path=sample.txt', '--', str(changed))

    checkpoint = ROOT / f'Spark2Groundwork_{lang}/scripts/harness/checkpoint.py'
    spec = importlib.util.spec_from_file_location('checkpoint_old_git', checkpoint)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Option-level detection itself.
    assert module._unsupported_pathspec_file(129,
        "error: unknown option `pathspec-from-file=/tmp/x'\nusage: git add ...")
    assert not module._unsupported_pathspec_file(128, 'fatal: Unable to write new index file')
    assert not module._unsupported_pathspec_file(129, '')

    real_run = module.run
    calls = []

    def old_git(argv, root, log):
        if any(str(a).startswith('--pathspec-from-file') for a in argv):
            calls.append('rejected')
            return 129, "error: unknown option `pathspec-from-file=<file>'\nusage: git add [<options>]"
        if '--renormalize' in argv:
            calls.append('fallback')
        return real_run(argv, root, log)

    monkeypatch.setattr(module, 'run', old_git)
    monkeypatch.setattr(sys, 'argv', [str(checkpoint), '--root', str(tmp_path),
                                      '--mode', 'tool', '--tool-id', 'upgrade', '--operation', 'old-git'])
    assert module.main(module.MSG) == 0
    assert calls.count('rejected') == 1 and calls.count('fallback') >= 1
    assert git('rev-parse', 'HEAD:sample.txt') == expected
    assert git('show', 'HEAD:中文 [literal].txt') == b'new'
    assert git('rev-parse', 'reviewed') == reviewed
    assert git('rev-parse', 'HEAD') != head

    # A genuine failure inside the fallback must NOT be swallowed.
    head2 = git('rev-parse', 'HEAD')
    changed.write_bytes(b'newer\n')

    def old_git_then_fail(argv, root, log):
        if any(str(a).startswith('--pathspec-from-file') for a in argv):
            return 129, "error: unknown option `pathspec-from-file=<file>'"
        if '--renormalize' in argv:
            return 17, 'fatal: injected staging failure'
        return real_run(argv, root, log)

    monkeypatch.setattr(module, 'run', old_git_then_fail)
    assert module.main(module.MSG) == 2
    assert git('rev-parse', 'HEAD') == head2
    assert git('rev-parse', 'reviewed') == reviewed


def test_launcher_exit_contract_covers_fail_code():
    """Stub exits 0, 1 and 2 must all be exercised, and a launcher must pass 1 through.

    ⛔ A launcher that turns FAIL into PASS is the most damaging honest regression,
    so exit 1 is part of the contract, not only 0 and 2.
    """
    source = (ROOT / 'scripts' / 'check_repo_hygiene.py').read_text(encoding='utf-8')
    assert 'for expected_exit in (0, 1, 2)]' in source

    for lang in ('zh', 'en'):
        edition = ROOT / f'Spark2Groundwork_{lang}'
        stem = next(iter(check_repo_hygiene.LAUNCHER_CONTRACT[f'Spark2Groundwork_{lang}']))
        with tempfile.TemporaryDirectory(prefix='launcher_exit_') as tmp:
            target = pathlib.Path(tmp) / edition.name
            shutil.copytree(edition, target)
            (target / 'scripts' / 'harness' / 'check_environment.py').write_text(
                'raise SystemExit(1)\n', encoding='utf-8')
            if sys.platform == 'win32':
                run_cmd = [str(target / f'{stem}.bat'), '--no-pause']
            else:
                run_cmd = [shutil.which('bash') or 'bash', str(target / f'{stem}.command'), '--no-pause']
            env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
                       PATH=str(pathlib.Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', ''))
            r = subprocess.run(run_cmd, cwd=target, capture_output=True, timeout=60, env=env)
            assert r.returncode == 1, (stem, r.returncode, r.stdout, r.stderr)


def test_pyyaml_installed():
    """Ensure PyYAML is installed; strict AST validation cannot proceed without PyYAML."""
    assert HAS_YAML, "PyYAML must be installed in the test environment to validate workflows."


def test_ci_workflow_valid_yaml_and_structure():
    """Verify that .github/workflows/ci.yml is valid YAML and has required top-level keys."""
    assert WORKFLOW_FILE.exists(), f"Workflow file missing at {WORKFLOW_FILE}"
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "Workflow YAML must parse to a dictionary"
    assert data.get("name") == "CI-0", f"Unexpected workflow name: {data.get('name')}"
    assert "on" in data, "Workflow must define 'on' triggers"
    assert "permissions" in data, "Workflow must define explicit 'permissions'"
    assert "jobs" in data, "Workflow must define 'jobs'"


def test_ci_workflow_permissions_strictly_read_only():
    """Verify that permissions are top-level and strictly read-only."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    perms = data.get("permissions")
    assert perms == {"contents": "read"}, f"Expected strictly {{'contents': 'read'}}, got {perms}"

    jobs = data.get("jobs", {})
    for jname, job in jobs.items():
        jperms = job.get("permissions")
        if jperms is not None:
            if isinstance(jperms, dict):
                for k, v in jperms.items():
                    assert v == "read", f"Job {jname} has non-read permission: {k}={v}"
            else:
                assert jperms == "read-all", f"Job {jname} has unexpected permission: {jperms}"


def test_ci_workflow_zero_secrets():
    """Verify that zero secrets are used or referenced."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "secrets." not in content, "Workflow must not reference secrets"
    assert "${{" not in content or "secrets" not in content, "No secrets interpolation allowed"


def test_ci_workflow_action_commit_sha_pinning():
    """Verify that all external actions are pinned to 40-character commit SHAs."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    sha_pattern = re.compile(r"^[0-9a-f]{40}$")
    checked_actions = 0
    for jname, job in data.get("jobs", {}).items():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if uses:
                action_spec = uses.strip()
                assert "@" in action_spec, f"Action {action_spec} missing version specifier in job {jname}"
                name, version = action_spec.split("@", 1)
                assert sha_pattern.match(version), f"Action {name} in job {jname} is not pinned to a 40-char commit SHA: got '{version}'"
                checked_actions += 1
    assert checked_actions >= 4, f"Expected at least 4 pinned action invocations, found {checked_actions}"


def test_ci_workflow_no_blanket_continue_on_error():
    """Verify no job or step has blanket continue-on-error: true."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    for jname, job in data.get("jobs", {}).items():
        assert job.get("continue-on-error") is not True, f"Job {jname} sets continue-on-error: true"
        for step in job.get("steps", []):
            assert step.get("continue-on-error") is not True, f"Step '{step.get('name')}' in job {jname} sets continue-on-error: true"


def test_ci_workflow_matrix_coverage_and_job_timeouts():
    """Verify lean matrix for PR (2 jobs) and full matrix for push/dispatch (8 jobs), with exact event conditions and timeouts."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    jobs = data.get("jobs", {})

    assert "hygiene" in jobs, "Workflow must contain 'hygiene' job"
    assert "selftest-matrix-lean" in jobs, "Workflow must contain 'selftest-matrix-lean' job for PR"
    assert "selftest-matrix-full" in jobs, "Workflow must contain 'selftest-matrix-full' job for push/dispatch"

    for jname in ("hygiene", "selftest-matrix-lean", "selftest-matrix-full"):
        assert jobs[jname].get("timeout-minutes") == 15, f"Job {jname} missing timeout-minutes: 15"

    lean_job = jobs["selftest-matrix-lean"]
    assert lean_job.get("if") == "github.event_name == 'pull_request'", \
        f"selftest-matrix-lean must have exact condition 'github.event_name == \\'pull_request\\'', got {lean_job.get('if')!r}"
    lean_matrix = lean_job.get("strategy", {}).get("matrix", {})
    lean_includes = lean_matrix.get("include", [])
    assert len(lean_includes) == 2, f"PR lean matrix must have exactly 2 jobs, found {len(lean_includes)}"
    lean_combos = {(inc["os"], inc["python-version"]) for inc in lean_includes}
    assert lean_combos == {("ubuntu-latest", "3.9"), ("windows-latest", "3.12")}, f"Unexpected lean matrix combos: {lean_combos}"

    full_job = jobs["selftest-matrix-full"]
    assert full_job.get("if") == "github.event_name != 'pull_request'", \
        f"selftest-matrix-full must have exact condition 'github.event_name != \\'pull_request\\'', got {full_job.get('if')!r}"
    full_matrix = full_job.get("strategy", {}).get("matrix", {})
    full_os = full_matrix.get("os", [])
    full_py = full_matrix.get("python-version", [])
    full_includes = full_matrix.get("include", [])

    base_combos = {(o, p) for o in full_os for p in full_py}
    inc_combos = {(inc["os"], inc["python-version"]) for inc in full_includes}
    all_combos = base_combos | inc_combos
    assert len(all_combos) == 8, f"Push/dispatch matrix must expand to exactly 8 combinations, found {len(all_combos)}: {all_combos}"

    all_os = {c[0] for c in all_combos}
    assert all_os == {"ubuntu-latest", "windows-latest", "macos-latest", "macos-15-intel"}, f"Missing runner architectures: {all_os}"
    all_py = {c[1] for c in all_combos}
    assert all_py == {"3.9", "3.12"}, f"Expected Python 3.9 and 3.12 in full matrix, got: {all_py}"


def test_check_repo_hygiene_falsification_kills():
    """Verify check_repo_hygiene catches planted falsifications (line endings, launcher reachability, tokens, AST, stubs)."""
    with tempfile.TemporaryDirectory(prefix="hygiene_kill_test_") as tmp:
        td = pathlib.Path(tmp)

        # 1. Plant mixed CRLF / standalone LF in .bat file -> check_line_endings must catch it
        bat_file = td / "test_mixed.bat"
        bat_file.write_bytes(b"@echo off\r\nline1\nline2\r\n")
        errs = check_repo_hygiene.check_line_endings(td)
        assert any("test_mixed.bat" in e and "standalone LF" in e for e in errs), "Failed to catch mixed CRLF/LF in .bat"

        # 2. Plant CRLF in .command file -> check_line_endings must catch it
        cmd_file = td / "test_cr.command"
        cmd_file.write_bytes(b"#!/bin/bash\r\nline\r\n")
        errs = check_repo_hygiene.check_line_endings(td)
        assert any("test_cr.command" in e and "CR" in e for e in errs), "Failed to catch CRLF in .command"

        # 3. Plant invalid shebang in .command file -> check_launchers must catch it
        zh_dir = td / "Spark2Groundwork_zh"
        zh_dir.mkdir()
        cmd_bad = zh_dir / "儲存進度.command"
        cmd_bad.write_bytes(b"#!/usr/bin/env bash\npython3 -I -B scripts/harness/check_environment.py --lang zh --action save --no-pause\n")
        errs = check_repo_hygiene.check_launchers(td)
        assert any("儲存進度.command" in e and "invalid shebang" in e for e in errs), "Failed to catch invalid shebang"

        # 4. Plant unchecked passthrough (%*) in .bat file -> check_launchers must catch it
        bat_bad = zh_dir / "儲存進度.bat"
        bat_bad.write_text('@echo off\r\n"%PY%" -I -B scripts\\harness\\check_environment.py --lang zh --action save %* --no-pause\r\n', encoding="utf-8")
        errs = check_repo_hygiene.check_launchers(td)
        assert any("儲存進度.bat" in e and "%*" in e for e in errs), "Failed to catch %* passthrough"

        # 5. Plant unreachable launcher (exit 0 / exit /b 0 before python line) -> kills unreachable_launchers probe
        cmd_unreach = zh_dir / "同步規則.command"
        cmd_unreach.write_bytes(b"#!/bin/bash\nexit 0\n\"$PY\" -I -B scripts/harness/check_environment.py --lang zh --action sync --no-pause\n")
        bat_unreach = zh_dir / "同步規則.bat"
        bat_unreach.write_bytes(b"@echo off\r\nexit /b 0\r\n\"%PY%\" -I -B scripts\\harness\\check_environment.py --lang zh --action sync --no-pause\r\n")
        errs = check_repo_hygiene.check_launchers(td)
        assert any("同步規則.command" in e and "unreachable" in e for e in errs), f"Failed to catch unreachable .command launcher: {errs}"
        assert any("同步規則.bat" in e and "unreachable" in e for e in errs), f"Failed to catch unreachable .bat launcher: {errs}"

        # 6. Plant corrupted argument tokens (--lang zhx / --action savex) -> kills suffix_argument_launchers probe
        cmd_suffix = zh_dir / "查看變更.command"
        cmd_suffix.write_bytes(b"#!/bin/bash\n\"$PY\" -I -B scripts/harness/check_environment.py --lang zhx --action review --no-pause\n")
        bat_suffix = zh_dir / "查看變更.bat"
        bat_suffix.write_bytes(b"@echo off\r\n\"%PY%\" -I -B scripts\\harness\\check_environment.py --lang zh --action reviewx --no-pause\r\n")
        errs = check_repo_hygiene.check_launchers(td)
        assert any("查看變更.command" in e and "invalid --lang argument" in e for e in errs), f"Failed to catch corrupted --lang zhx: {errs}"
        assert any("查看變更.bat" in e and "invalid --action argument" in e for e in errs), f"Failed to catch corrupted --action reviewx: {errs}"

        # 7. Plant launcher distribution clustering (12 launchers in zh, 0 in en) -> check_mandatory_structure must catch it
        cluster_root = td / "cluster_test"
        cluster_root.mkdir()
        c_zh = cluster_root / "Spark2Groundwork_zh"
        c_en = cluster_root / "Spark2Groundwork_en"
        c_zh.mkdir()
        c_en.mkdir()
        for idx in range(12):
            (c_zh / f"stub_{idx}.command").write_bytes(b"#!/bin/bash\nexit 0\n")
            (c_zh / f"stub_{idx}.bat").write_bytes(b"@echo off\r\nexit /b 0\r\n")
        errs = check_repo_hygiene.check_mandatory_structure(cluster_root)
        assert any("expected exactly 6 .bat" in e or "expected exactly 6 .command" in e for e in errs), \
            f"Failed to catch single-language clustering in structure check: errs={errs}"

        # 8. Empty root check -> check_mandatory_structure must catch it
        empty_root = td / "empty_dir"
        empty_root.mkdir()
        errs = check_repo_hygiene.check_mandatory_structure(empty_root)
        assert any("Mandatory directory missing" in e for e in errs), "Failed to catch missing mandatory structure on empty root"

        # 9. Plant Python 3.10 match/case in .py file -> check_python_ast must catch it
        py_file = td / "test_match.py"
        py_file.write_text("def f(x):\n    match x:\n        case 1: pass\n", encoding="utf-8")
        errs = check_repo_hygiene.check_python_ast(td)
        assert any("test_match.py" in e and ("SyntaxError" in e or "structural pattern" in e or "match/case" in e) for e in errs), \
            f"check_python_ast failed to catch incompatible match/case syntax: {errs}"
        py_file.unlink()

        # 10. Ordinary valid Python file must walk cleanly without AttributeError (kills B1)
        valid_py = td / "test_valid.py"
        valid_py.write_text("def hello(name: str) -> str:\n    return f'hello {name}'\nclass Foo:\n    pass\n", encoding="utf-8")
        errs_valid = check_repo_hygiene.check_python_ast(td)
        assert not errs_valid, f"check_python_ast failed on ordinary valid Python 3.9 file: {errs_valid}"
        valid_py.unlink()

        # 11. Plant forged launcher with redirection and tautology -> check_launchers must catch it (kills B3 static)
        bat_taut = zh_dir / "檢查專案.bat"
        bat_taut.write_bytes(b"@echo off\r\n> \"scripts\\harness\\launcher_receipt.json\" echo {}\r\nif 1==1 exit /b 0\r\n\"%PY%\" -I -B scripts\\harness\\check_environment.py --lang zh --action check --no-pause\r\n")
        errs_taut = check_repo_hygiene.check_launchers(td)
        assert any("forbidden file write redirection" in e or "tautological condition" in e or "forbidden early exit" in e for e in errs_taut), \
            f"check_launchers failed to catch forged launcher with redirection and tautology: {errs_taut}"


def test_disposable_projects_catches_all_tampering_forms():
    """Verify check_disposable_projects catches fake summaries, duplicate tests, forged 186 cases, under-run 165, and sensor tampering."""
    with tempfile.TemporaryDirectory(prefix="disposable_kill_test_") as tmp:
        td = pathlib.Path(tmp)
        zh_harness = td / "Spark2Groundwork_zh" / "scripts" / "harness"
        zh_harness.mkdir(parents=True)
        en_harness = td / "Spark2Groundwork_en" / "scripts" / "harness"
        en_harness.mkdir(parents=True)

        # 1. Fake selftest producing 'NO TESTS EXECUTED'
        (zh_harness / "run_selftest.py").write_text("print('NO TESTS EXECUTED')\n", encoding="utf-8")
        (zh_harness / "run_all_sensors.py").write_text("print('NO TESTS EXECUTED')\n", encoding="utf-8")
        (en_harness / "run_selftest.py").write_text("print('NO TESTS EXECUTED')\n", encoding="utf-8")
        (en_harness / "run_all_sensors.py").write_text("print('NO TESTS EXECUTED')\n", encoding="utf-8")

        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("fake execution" in e or "NO TESTS EXECUTED" in e for e in errs), \
            f"Failed to catch NO TESTS EXECUTED: errs={errs}"

        # 2. Fake selftest with under-run (165 items instead of 186) -> kills under_run_165 probe
        items_165 = "\n".join([f"print('  ✅ test-item-{i:03d}')" for i in range(165)])
        code_165 = f"{items_165}\nprint('通過 165 項｜失敗 0 項\\n結果：自測全數通過')\n"
        (zh_harness / "run_selftest.py").write_text(code_165, encoding="utf-8")
        (en_harness / "run_selftest.py").write_text(code_165, encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("under-run or count mismatch" in e or "not EXACTLY 186" in e for e in errs), \
            f"Failed to catch under-run 165: errs={errs}"

        # 3. Fake selftest with fabricated 186 unique cases (matching 5 substrings only) -> kills forged_exact_186 probe
        req = check_repo_hygiene.REQUIRED_ZH_TESTS
        fab_items = [f"required-{i}: {name}" for i, name in enumerate(req)]
        fab_items.extend(f"fabricated-unique-{i:03d}" for i in range(186 - len(fab_items)))
        code_fab_186 = "\n".join([f"print('  ✅ ' + {item!r})" for item in fab_items]) + "\nprint('通過 186 項｜失敗 0 項\\n結果：自測全數通過')\n"
        (zh_harness / "run_selftest.py").write_text(code_fab_186, encoding="utf-8")
        (en_harness / "run_selftest.py").write_text(code_fab_186, encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("test cases mismatch with expected registry" in e for e in errs), \
            f"Failed to catch forged 186 cases mismatch: errs={errs}"

        # 4. Fake selftest with duplicate items repeated 186 times
        dup_items = "\n".join(["print('  ✅ UPG-REC-12: identical test repeated')"] * 186)
        zh_fake_dup = f"{dup_items}\nprint('通過 186 項｜失敗 0 項\\n結果：自測全數通過')\n"
        (zh_harness / "run_selftest.py").write_text(zh_fake_dup, encoding="utf-8")
        (en_harness / "run_selftest.py").write_text(zh_fake_dup, encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("duplicate test executions" in e for e in errs), \
            f"Failed to catch duplicated selftest executions: errs={errs}"

        # 5. Fake sensor script reporting 999 sensors run
        fake_sensors_code = (
            "import pathlib, json\n"
            "status = {'worst': 0, 'results': [{'sensor': 'sensor_conjecture_ledger.py', 'code': 0}] * 10}\n"
            "pathlib.Path('harness_status.json').write_text(json.dumps(status), encoding='utf-8')\n"
            "print('✅ 總結：PASS（999 支已執行）')\n"
        )
        (zh_harness / "run_all_sensors.py").write_text(fake_sensors_code, encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("expected EXACTLY 10" in e or "duplicate sensor names" in e for e in errs), \
            f"Failed to catch 999 sensors summary or duplicate sensor names: errs={errs}"

        # 6. Fake sensor status with missing / unknown sensor
        status_tampered = {
            "worst": 0,
            "results": [{"sensor": f"unknown_sensor_{i}.py", "code": 0} for i in range(10)]
        }
        fake_unknown_code = (
            "import pathlib, json\n"
            f"pathlib.Path('harness_status.json').write_text({json.dumps(status_tampered)!r}, encoding='utf-8')\n"
            "print('✅ 總結：PASS（10 支已執行）')\n"
        )
        (zh_harness / "run_all_sensors.py").write_text(fake_unknown_code, encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("sensor mismatch" in e for e in errs), \
            f"Failed to catch unknown sensor names in status.json: errs={errs}"

        # 7. Exact registry fake runner with zero execution -> caught by controlled fault injection (kills B2)
        exact_zh_cases = "\n".join([f"print({('✅ ' + case)!r})" for case in check_repo_hygiene.EXPECTED_ZH_TEST_CASES])
        exact_en_cases = "\n".join([f"print({('✅ ' + case)!r})" for case in check_repo_hygiene.EXPECTED_EN_TEST_CASES])
        fake_runner_zh = f"{exact_zh_cases}\nprint('通過 186 項｜失敗 0 項\\n結果：自測全數通過')\n"
        fake_runner_en = f"{exact_en_cases}\nprint('passed 186 | failed 0\\nResult: all self-tests passed')\n"
        (zh_harness / "run_selftest.py").write_text(fake_runner_zh, encoding="utf-8")
        (en_harness / "run_selftest.py").write_text(fake_runner_en, encoding="utf-8")
        (zh_harness / "sensor_claim_ledger.py").write_text("print('genuine')\n", encoding="utf-8")
        (en_harness / "sensor_claim_ledger.py").write_text("print('genuine')\n", encoding="utf-8")
        errs, stats, records = check_repo_hygiene.check_disposable_projects(td)
        assert any("FAULT_REGRESSION_FAILURE" in e for e in errs), \
            f"Failed to catch exact registry fake runner via fault injection: errs={errs}"


def test_disposable_projects_git_and_timeout_failures(monkeypatch):
    """Verify check_disposable_projects and check_bash_syntax cleanly catch timeouts and git failures via monkeypatching."""
    with tempfile.TemporaryDirectory(prefix="timeout_probe_test_") as tmp:
        base = pathlib.Path(tmp)
        for edition in ("Spark2Groundwork_zh", "Spark2Groundwork_en"):
            harness = base / edition / "scripts" / "harness"
            harness.mkdir(parents=True)
            (harness / "run_selftest.py").write_text("raise SystemExit(88)\n", encoding="utf-8")
            (harness / "run_all_sensors.py").write_text("raise SystemExit(89)\n", encoding="utf-8")

        def ok(stdout=""):
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        # 1. Git init timeout
        def fake_git_timeout(argv, **kwargs):
            if argv and argv[0] == "git" and argv[1] == "init":
                raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"), output=b"git-partial-out", stderr=b"git-partial-err")
            return ok()

        monkeypatch.setattr(check_repo_hygiene.subprocess, "run", fake_git_timeout)
        errs, stats, records = check_repo_hygiene.check_disposable_projects(base)
        assert any("git step timed out" in e for e in errs), f"git_timeout error missing: {errs}"
        assert any(r.get("returncode") == -1 for r in records), "git_timeout failure record missing"

        # 2. Git commit failure (exit code 17)
        def fake_commit_fail(argv, **kwargs):
            if argv and argv[0] == "git" and argv[1] == "commit":
                return SimpleNamespace(returncode=17, stdout="commit-out", stderr="commit-err")
            return ok()

        monkeypatch.setattr(check_repo_hygiene.subprocess, "run", fake_commit_fail)
        errs, stats, records = check_repo_hygiene.check_disposable_projects(base)
        assert any("git step failed" in e for e in errs), f"commit_failure error missing: {errs}"
        assert any(r.get("returncode") == 17 for r in records), "commit_failure returncode 17 record missing"

        # 3. Selftest timeout
        def fake_selftest_timeout(argv, **kwargs):
            name = pathlib.Path(str(argv[-1])).name if argv else ""
            if argv and argv[0] == "git":
                return ok()
            if name == "run_selftest.py":
                raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"), output=b"selftest-partial-out", stderr=b"selftest-partial-err")
            return ok()

        monkeypatch.setattr(check_repo_hygiene.subprocess, "run", fake_selftest_timeout)
        errs, stats, records = check_repo_hygiene.check_disposable_projects(base)
        assert any("run_selftest.py timed out" in e for e in errs), f"selftest_timeout error missing: {errs}"
        assert any(r.get("returncode") == -1 for r in records), "selftest_timeout failure record missing"

        # 4. Sensor runner timeout
        def fake_sensor_timeout(argv, **kwargs):
            name = pathlib.Path(str(argv[-1])).name if argv else ""
            if argv and argv[0] == "git":
                return ok()
            if name == "run_selftest.py":
                if "fault_injection" in str(kwargs.get("cwd", "")) or any("fault_injection" in str(a) for a in argv):
                    return SimpleNamespace(returncode=1, stdout="Result: self-test FAILED\n❌ claim_ghost: FAIL\n", stderr="")
                lang = "zh" if "Spark2Groundwork_zh" in str(argv[-1]) else "en"
                cases = check_repo_hygiene.EXPECTED_ZH_TEST_CASES if lang == "zh" else check_repo_hygiene.EXPECTED_EN_TEST_CASES
                lines = "\n".join("✅ " + item for item in cases)
                summary = "通過 186 項｜失敗 0 項\n結果：自測全數通過" if lang == "zh" else "passed 186 | failed 0\nResult: all self-tests passed"
                return ok(lines + "\n" + summary)
            if name == "run_all_sensors.py":
                raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"), output=b"sensor-partial-out", stderr=b"sensor-partial-err")
            return ok()

        monkeypatch.setattr(check_repo_hygiene.subprocess, "run", fake_sensor_timeout)
        errs, stats, records = check_repo_hygiene.check_disposable_projects(base)
        assert any("run_all_sensors.py timed out" in e for e in errs), f"sensor_timeout error missing: {errs}"
        assert any(r.get("returncode") == -1 for r in records), "sensor_timeout failure record missing"

        # 5. Bash syntax check timeout
        (base / "hang.command").write_text("#!/bin/bash\n", encoding="utf-8")
        monkeypatch.setattr(check_repo_hygiene.shutil, "which", lambda _name: "bash")
        monkeypatch.setattr(
            check_repo_hygiene.subprocess,
            "run",
            lambda argv, **kwargs: (_ for _ in ()).throw(
                subprocess.TimeoutExpired(argv, kwargs.get("timeout"), output=b"bash-out", stderr=b"bash-err")
            ),
        )
        errs, note, is_inc = check_repo_hygiene.check_bash_syntax(base)
        assert any("timed out" in e for e in errs), f"bash_timeout error missing: {errs}"
        assert not is_inc, "bash_timeout should not be marked as incomplete"


@pytest.mark.parametrize('lang', ['zh', 'en'])
@pytest.mark.parametrize('legacy', [False, True])
def test_checkpoint_large_literal_paths_and_failure_boundaries(tmp_path, monkeypatch, lang, legacy):
    # Real Git handles all filesystem/index/commit operations. Only its missing-option
    # response is simulated; this is not a claim to have run an old Git binary.
    with tempfile.TemporaryDirectory(prefix='s2gr7_') as td:
        root = pathlib.Path(td)
        def git(*args):
            r=subprocess.run(['git','-C',str(root),*args],capture_output=True,timeout=30)
            assert r.returncode == 0, r.stderr
            return r.stdout.strip()
        git('init','-q'); git('config','user.name','fixture'); git('config','user.email','ci@local')
        (root/'governance').mkdir()
        for n in ('AGENTS.md','WORKFLOW_CONSTITUTION.md'):
            (root/'governance'/n).write_text('fixture\n',encoding='utf-8')
        (root/'.gitignore').write_text('git-checkpoint.log\n',encoding='utf-8')
        # Keep absolute paths legal on systems without Windows long-path opt-in.
        n=min(180, 235-len(str(root))-1)
        names=[f'{i:03d}_'+('x'*(n-8))+'.txt' for i in range(205)]
        names+=['中文 [literal].txt','-leading.txt','space name.txt']
        for name in names: (root/name).write_bytes(b'old\n')
        git('add','.'); git('commit','-qm','base'); git('tag','reviewed')
        reviewed=git('rev-parse','reviewed')
        for name in names: (root/name).write_bytes(b'new\n')
        path=ROOT/f'Spark2Groundwork_{lang}/scripts/harness/checkpoint.py'
        spec=importlib.util.spec_from_file_location('checkpoint_r7',path)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        real=mod.run; batches=[]
        def old(argv,cwd,log):
            if legacy and any(x.startswith('--pathspec-from-file=') for x in argv):
                return 129,"error: unknown option `pathspec-from-file=paths'\nusage: git add"
            if '--' in argv and '--renormalize' in argv:
                batches.append(argv)
                assert mod._argv_size(argv) <= mod._ARGV_BUDGET
            return real(argv,cwd,log)
        monkeypatch.setattr(mod,'run',old)
        monkeypatch.setattr(sys,'argv',[str(path),'--root',str(root),'--mode','tool','--tool-id','test','--operation','refresh'])
        assert mod.main(mod.MSG)==0
        expected=git('hash-object',str(root/names[0]))
        entries=git('ls-tree','-rz','HEAD').split(b'\0')
        blobs={e.split(b'\t',1)[1].decode('utf-8'):e.split()[2] for e in entries if e}
        assert all(blobs[name]==expected for name in names)
        assert (len(batches)>1) if legacy else not batches
        assert git('rev-parse','reviewed')==reviewed
        head=git('rev-parse','HEAD')
        # Neither a misleading usage banner nor an unrelated option may trigger fallback.
        for code, diagnostic in [(128,'fatal: cannot read --pathspec-from-file=paths\nusage: git add'),
                                 (129,'usage: git add --pathspec-from-file'),
                                 (129,"error: unknown option `other'\nusage: git add --pathspec-from-file")]:
            (root/names[0]).write_bytes(b'changed again\n')
            def fail(argv,cwd,log):
                if any(x.startswith('--pathspec-from-file=') for x in argv): return code,diagnostic
                if '--renormalize' in argv: pytest.fail('true failure entered fallback')
                return real(argv,cwd,log)
            monkeypatch.setattr(mod,'run',fail)
            assert mod.main(mod.MSG)==2
            assert git('rev-parse','HEAD')==head and git('rev-parse','reviewed')==reviewed
        # OS startup failure (including Windows 206) must be a controlled refusal.
        for phase in ('modern','fallback'):
            def os_fail(argv,cwd,log):
                if any(x.startswith('--pathspec-from-file=') for x in argv):
                    if phase=='modern': raise OSError(206,'command too long')
                    return 129,"error: unknown option `pathspec-from-file'"
                if '--renormalize' in argv: raise OSError(206,'command too long')
                return real(argv,cwd,log)
            monkeypatch.setattr(mod,'run',os_fail)
            assert mod.main(mod.MSG)==2
            assert git('rev-parse','HEAD')==head and git('rev-parse','reviewed')==reviewed
        # Budget uses quoted UTF-16 units and encoded bytes, including non-BMP text.
        prefix=['git','--literal-pathspecs','add','--renormalize','--']
        paths=['space U0001f600\\"'+str(i) for i in range(2000)]
        split=list(mod._path_batches(prefix,paths))
        assert [p for batch in split for p in batch]==paths
        assert all(mod._argv_size(prefix+b)<=mod._ARGV_BUDGET for b in split)
        with pytest.raises(OSError): list(mod._path_batches(prefix,['x'*20000]))


@pytest.mark.parametrize('lang', ['en', 'zh'])
def test_scope_readonly_index_and_malformed_git_outputs(tmp_path, monkeypatch, lang):
    checkpoint = ROOT / f'Spark2Groundwork_{lang}/scripts/harness/sensor_scope_and_t0.py'
    spec=importlib.util.spec_from_file_location('scope_contract',checkpoint)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def git(*args):
        p=subprocess.run(['git','-C',str(tmp_path),*args],capture_output=True)
        assert p.returncode==0,p.stderr
    git('init','-q');git('config','user.name','test');git('config','user.email','test@local')
    f=tmp_path/'safe.txt';f.write_bytes(b'base\n');git('add','.');git('commit','-qm','base');git('tag','reviewed')
    os.utime(f,(1600000000,1600000000));index=tmp_path/'.git/index';before=index.read_bytes()
    assert module.git_changed(tmp_path)==([],None)
    assert index.read_bytes()==before
    real=subprocess.run
    for payload in (b'X\0',b'ZZ safe.txt\0',b'R  safe.txt\0',b' M safe.txt',b' M \xff\0'):
        def malformed(argv,**kw):
            if 'status' in argv: return SimpleNamespace(returncode=0,stdout=payload,stderr=b'')
            return real(argv,**kw)
        with monkeypatch.context() as m:
            m.setattr(module.subprocess,'run',malformed)
            assert module.git_changed(tmp_path)[0] is None
    for payload in (b'R100\0safe.txt\0',b'Q\0safe.txt\0',b'M\0safe.txt',b'M\0\0'):
        with pytest.raises(ValueError):module._parse_history(payload)
    assert module._parse_history(b'R100\0from.txt\0to.txt\0')==['from.txt','to.txt']
    assert module._parse_status(b'R  to.txt\0from.txt\0')==['to.txt','from.txt']


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_e2b_generated_metadata_and_protected_recovery(tmp_path, lang):
    source = ROOT / ("Spark2Groundwork_" + lang)
    root = tmp_path / "project"
    shutil.copytree(source, root)
    config = {"write_scopes": {"agent": ["my", "handoffs"]}, "deny": ["corpus", "ledgers"]}
    (root / "governance_config.json").write_text(json.dumps(config), encoding="utf-8")
    def git(*args):
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
        assert r.returncode == 0, r.stderr
        return r.stdout
    git("init", "-q"); git("config", "user.name", "Test"); git("config", "user.email", "test@local")
    with (root / ".gitignore").open("a", encoding="utf-8") as out:
        out.write("\ncorpus/private/\n*.other.json\n")
    git("add", "."); git("commit", "-qm", "baseline"); git("tag", "reviewed")
    sensor = root / "scripts/harness/sensor_scope_and_t0.py"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    def inspect():
        before = (root / ".git/index").read_bytes()
        r = subprocess.run([sys.executable, "-B", str(sensor), "--root", str(root), "--json"], capture_output=True, env=env)
        assert (root / ".git/index").read_bytes() == before
        data = json.loads(r.stdout)
        return r.returncode, {x["code"] for x in data["findings"]}
    assert inspect()[0] == 0
    # The real runner creates the ignored status report. Two successive runs stay usable.
    runner = root / "scripts/harness/run_all_sensors.py"
    for _ in range(2):
        subprocess.run([sys.executable, "-B", str(runner)], cwd=root, capture_output=True, env=env, timeout=90)
        report = json.loads((root / "scripts/harness/harness_status.json").read_text("utf-8"))
        assert next(r for r in report["results"] if r["sensor"] == "sensor_scope_and_t0.py")["code"] == 0
        assert inspect()[0] == 0
    for name in (".DS_Store", "corpus/.DS_Store", "ledgers/.DS_Store", "git-checkpoint.log"):
        (root / name).write_bytes(b"generated")
    assert inspect()[0] == 0
    (root / "x.other.json").write_bytes(b"not a generated report")
    assert "IGNORED_OUT_OF_SCOPE_PRESENT" in inspect()[1]
    (root / "x.other.json").unlink()
    private = root / "corpus/private/raw.pdf"; private.parent.mkdir(); private.write_bytes(b"private research")
    assert "IGNORED_DENIED_PATH_PRESENT" in inspect()[1]
    git("tag", "-f", "reviewed", "HEAD")
    assert "IGNORED_DENIED_PATH_PRESENT" in inspect()[1]
    # Explicit approved local tracking + real review resolves it without deleting data.
    git("add", "-f", "corpus/private/raw.pdf"); git("commit", "-qm", "record approved local data"); git("tag", "-f", "reviewed", "HEAD")
    assert inspect()[0] == 0
    assert private.read_bytes() == b"private research"
    config["deny"].append("corpus/.DS_Store")
    (root / "governance_config.json").write_text(json.dumps(config), encoding="utf-8")
    git("add", "governance_config.json"); git("commit", "-qm", "explicit deny"); git("tag", "-f", "reviewed", "HEAD")
    assert "IGNORED_DENIED_PATH_PRESENT" in inspect()[1]


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_e3a_conjecture_cross_tree_target_config(tmp_path, lang):
    """V145-E3a: Verify conjecture sensor honors target root's governance_config.json cross-tree.

    Validates:
    1. Custom conjecture ledger path is read from target root cfg (cross-tree PASS).
    2. Negative control: missing custom ledger reports LEDGER_MISSING pointing to the custom path.
    3. Custom proposal markers are read from target root cfg (proposal citation exempted).
    4. Negative control: citation in unexempted handoff reports CITATION_NOT_IN_LEDGER.
    5. Custom excluded_dirs are read from target root cfg (ignored folder not scanned).
    6. Negative control: citation in unexcluded folder reports CITATION_NOT_IN_LEDGER.
    """
    target = tmp_path / ("target_" + lang)
    target.mkdir(parents=True)
    custom_ledger_rel = "custom_ledgers/my_conjectures.md" if lang == "en" else "台帳/我的猜想.md"
    custom_marker = "custom-pending" if lang == "en" else "自訂待套用"
    custom_exclude = "scratch_custom"

    cfg = {
        "conjecture_ledger": custom_ledger_rel,
        "proposal_markers": [custom_marker],
        "excluded_dirs": ["archive", ".git", "__pycache__", custom_exclude],
    }
    (target / "governance_config.json").write_text(json.dumps(cfg), encoding="utf-8")

    ledger_path = target / custom_ledger_rel
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if lang == "en":
        ledger_content = (
            "# Conjecture Ledger\n"
            "## 0. How to use it\n"
            "### 0.1 Six states\n"
            "| State | Meaning |\n"
            "|---|---|\n"
            "| Conjecture | unverified |\n"
            "## 1. Conjectures\n\n"
            "### C-01 | 🟡 Falsifiable | main line\n\n"
            "**Statement:** When A increases, B decreases.\n"
            "**Origin:** Paragraph 2 of the original idea\n"
            "**Falsification:** If A and B are unrelated after controlling C, this conjecture is false.\n"
            "**Falsification adjudicated:** adjudicated\n"
            "**Strongest rival:** Theory D holds that the A-B link is fully mediated by C.\n"
            "**Rival's differing prediction:** D predicts the link vanishes once C is controlled; this conjecture predicts it persists.\n"
            "**Basis:** -\n"
            "**Log:** 2026-01-01 created\n"
        )
    else:
        ledger_content = (
            "# 猜想台帳\n"
            "## 0. 使用方法\n"
            "### 0.1 六種狀態\n"
            "| 狀態 | 意義 |\n"
            "|---|---|\n"
            "| 🔵 猜想 | 尚未查證 |\n"
            "## 1. 猜想\n\n"
            "### C-01 ｜ 🟡 已可證偽 ｜ 主線\n\n"
            "**表述：** 甲條件提高時，乙指標會下降。\n"
            "**來源：** 原始構想第二段\n"
            "**反證條件：** 若在控制丙之後甲與乙無關聯，則本猜想為假。\n"
            "**反證條件裁決：** 已裁決\n"
            "**最強競爭解釋：** 丁理論主張甲乙的關聯完全由丙中介。\n"
            "**競爭解釋的不同預測：** 丁預測控制丙之後關聯消失；本猜想預測仍存在。\n"
            "**依據：** —\n"
            "**紀錄：** 2026-01-01 建立\n"
        )
    ledger_path.write_text(ledger_content, encoding="utf-8")
    (target / "ordinary_note.md").write_text("# Note\nClean content without citations\n", encoding="utf-8")

    sensor = ROOT / ("Spark2Groundwork_" + lang) / "scripts/harness/sensor_conjecture_ledger.py"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")

    def run_sensor():
        r = subprocess.run([sys.executable, "-B", str(sensor), "--root", str(target), "--json"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        data = json.loads(r.stdout)
        return r.returncode, {x["code"] for x in data.get("findings", [])}, data

    # 1. Custom ledger path recognized cross-tree -> PASS
    rc, codes, data = run_sensor()
    assert rc == 0
    assert data["status"] == "PASS"
    assert "LEDGER_MISSING" not in codes
    stat_key = "conjectures" if lang == "en" else "猜想筆數"
    assert data.get("stats", {}).get(stat_key) == 1

    # 2. Negative control: missing custom ledger fails with target path in finding
    ledger_path.unlink()
    rc, codes, data = run_sensor()
    assert rc == (2 if lang == "en" else 1)
    assert data["status"] == ("INCOMPLETE" if lang == "en" else "FAIL")
    assert "LEDGER_MISSING" in codes
    missing_msg = next(x["message"] for x in data["findings"] if x["code"] == "LEDGER_MISSING")
    assert custom_ledger_rel in missing_msg
    ledger_path.write_text(ledger_content, encoding="utf-8")

    # 3. Custom proposal markers recognized cross-tree -> exempted
    handoffs_dir = target / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    proposal_file = handoffs_dir / f"handoff_{custom_marker}.md"
    proposal_file.write_text("# Proposal\nRefers to C-99 pending adjudication.\n", encoding="utf-8")
    rc, codes, data = run_sensor()
    assert rc == 0
    assert data["status"] == "PASS"
    assert "CITATION_CHECK_EXEMPTED" in codes
    assert "CITATION_NOT_IN_LEDGER" not in codes

    # 4. Negative control: citation without proposal marker fails
    normal_handoff = handoffs_dir / "handoff_plain.md"
    normal_handoff.write_text("# Plain\nRefers to C-99.\n", encoding="utf-8")
    rc, codes, data = run_sensor()
    assert rc == 1
    assert data["status"] == "FAIL"
    assert "CITATION_NOT_IN_LEDGER" in codes
    normal_handoff.unlink()
    proposal_file.unlink()

    # 5. Custom excluded_dirs recognized cross-tree -> excluded from scan
    scratch_dir = target / custom_exclude
    scratch_dir.mkdir(parents=True, exist_ok=True)
    scratch_file = scratch_dir / "scratch_with_ghost_citation.md"
    scratch_file.write_text("# Scratch\nRefers to C-99.\n", encoding="utf-8")
    rc, codes, data = run_sensor()
    assert rc == 0
    assert data["status"] == "PASS"
    assert "CITATION_NOT_IN_LEDGER" not in codes

    # 6. Negative control: moving file to unexcluded directory triggers failure
    regular_note = target / "unexcluded_note.md"
    regular_note.write_text("# Regular\nRefers to C-99.\n", encoding="utf-8")
    rc, codes, data = run_sensor()
    assert rc == 1
    assert data["status"] == "FAIL"
    assert "CITATION_NOT_IN_LEDGER" in codes
    regular_note.unlink()
