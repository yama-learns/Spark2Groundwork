# CI-0: minimal v1.4.5 regression checks (r6)

## Purpose and trust boundary

CI replays defined regression checks to detect missing execution, missing inputs, bad arguments, failure propagation errors, timeouts and incomplete environments. Green means those checks passed for the stated candidate and environment. It does not certify research, human review, release readiness or every platform.

CI-0 does **not authenticate execution against malicious runner, launcher or checker code with the same privileges**. Such code can inspect probes, forge receipts or modify checks. Random identifiers prevent accidental stale-result reuse and vary sampled coverage; they are not secrets or identity credentials. Independent code review, exact candidate binding and merge authorization remain necessary.

Before merging, an independent reviewer must inspect changes to `.github/workflows/**`, `scripts/check_repo_hygiene.py`, `tests/**`, either edition's `scripts/harness/run_selftest.py`, `run_all_sensors.py`, `selftest/**`, every `.bat` / `.command`, and this specification. Sensors and core code remain subject to the existing review process. This is a process requirement. This card does not install remote branch protection, CODEOWNERS or an isolated trusted executor, and claims no such enforcement.

## Workflow

| Event | Matrix |
|---|---|
| PR targeting main or work/** | Linux / Python 3.9; Windows / Python 3.12 |
| Push to main or work/**, or dispatch | Linux, Windows, Apple Silicon macOS, Intel macOS; Python 3.9 and 3.12 on each, 8 combinations |

Each job has a 15-minute timeout. Matrix fail-fast is disabled to preserve other platform results. Permissions are contents: read, checkout does not persist credentials, and no secrets, PR target events, deployment or automatic publication are used. External actions are pinned to full commit SHAs. Test dependencies are pytest 8.4.2 and PyYAML 6.0.3; this is not a full transitive dependency lock.

Runner labels are not test evidence. The first authorized remote run must record its URL, exact commit and each matrix result. An unavailable runtime/runner means incomplete. Download line endings and executable `.command` modes still require integration/packaging verification: local copies and bash invocation do not prove Git index modes, ZIP permissions or Finder/Gatekeeper behavior.

## Three responsibilities

1. **File and entry lint:** bilingual structure, 24 expected launcher files, CRLF batch / LF shell and Python files, shebangs, closed arguments, obvious early exits, bash syntax, Python 3.9 syntax and absence of runtime artifacts. Static scanning is lint, not a general control-flow proof.
2. **Disposable project regression:** run each original selftest in an external Git project; require the exact 186 expected names with no duplicates, missing items or failures. Run aggregate sensors, validate the fresh ten-sensor status, then execute each sensor directly and compare exits. Exit 1/2, errors and timeouts cannot pass. The case registry is a reviewed contract, not an immutable numeric target: legitimate case changes require a corresponding reviewed diff.
3. **Failure propagation and native entries:** after a successful baseline, sample one of six existing negative-fixture sensor families per language in a new copy. Inject a controlled wrong exit of 0 or 3. Require the named fixture's load record, the previously passing case's expected failure, runner exit 1 and no retained pass for that case. Generic `failed` text or an arbitrary nonzero exit is insufficient. Record selection, before/after hashes and outputs. This is sampled regression, not coverage of all ten sensors or anti-forgery security. Run every platform-native entry with stub exits 0, 1 and 2, checking fresh invocation identifiers, exact lang/action and exit propagation. Exit 1 is included because a launcher that swallows FAIL into PASS is the most damaging honest regression. Record the actual launcher-selected Python executable/version; it may differ from the matrix Python.

## Execution and evidence

In a disposable repository copy:

```text
python -B scripts/check_repo_hygiene.py --all
python -B -m pytest -p no:cacheprovider tests/test_ci_workflow.py
```

Never run inside a frozen candidate. Job logs retain actual versions, commands, stdout/stderr, exits, fault selection and launcher receipts, including partial timeout output. Work-package integrity verification belongs to external `verify.py`; published pytest does not contain a package-only test that permanently skips.

Missing bash yields exit 2; other check failures yield exit 1. Neither is success. No blanket continue-on-error, retry-until-green or skipping known product faults. Preserve failed runs and record the diff before new runs. New capabilities and same-privilege attack research belong to separate scoped work, not endless string-probe repairs.

## CI0-O1 baseline correction

Ordinary Git add can reuse stat data after a same-size content replacement with identical/coarse file timestamps. After normal add handles additions/deletions and ignore rules, r6 renormalizes ordinary tracked H entries while preserving assume-unchanged / skip-worktree exclusions; failure returns 2. `git add --pathspec-from-file` requires Git 2.25 or newer; when Git rejects the option itself the checkpoint falls back to batched literal pathspec arguments, so older Git (for example Apple Git 2.24) keeps working. A real staging failure still returns 2 and never silently skips files. This re-applies existing clean / line-ending rules and increases tracked-file read cost. Tool checkpoints still do not move reviewed; upgrade's durable-receipt safety gate remains intact. Tests cover reproducible omission, additions, deletion, ignores, no-op and no commit on staging failure. This product change requires independent review with r6; X89 acceptance does not extend to it.

Official references, checked 2026-09-22: [Git add](https://git-scm.com/docs/git-add), [GitHub runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

Legacy Git fallback is permitted only for exit 129 with an explicit unknown/unrecognized pathspec-from-file option diagnostic (C locale). Batches use a conservative 16,000-unit budget covering quoted UTF-16 and UTF-8 argv bytes plus executable headroom. Process creation and pathspec-file failures return 2 without a new commit. Each shipped edition includes CHECKPOINT-STAT, a deterministic same-size/same-time content regression; this adds one real selftest (167 → 168). Native launcher checks cover 12 platform-native entries × exits 0/1/2 = 36 invocations per full run. Old Git responses are simulated in local tests; actual legacy Git and remote runners require separate evidence.
