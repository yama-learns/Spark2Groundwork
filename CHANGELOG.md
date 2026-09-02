# Changelog

All notable changes to this project are recorded here.
本專案的重要變更記錄於此。

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ｜ Versioning: [SemVer](https://semver.org/lang/zh-TW/)

> ⚠️ **Per-sensor detail lives with the sensors, not here.**
> Every sensor change records its own triggering case in
> `Spark2Groundwork_<en|zh>/scripts/harness/SENSOR_CHANGELOG.md`.
> This file summarises releases and points there; ⛔ it does not restate them.
>
> ⚠️ **各感測器的細節記在感測器旁邊，不在這裡。**
> 每一次感測器變更的觸發個案都登錄在
> `Spark2Groundwork_<en|zh>/scripts/harness/SENSOR_CHANGELOG.md`。
> 本檔只做版本層級的摘要並指向該處，⛔ 不重述其內容。

---

## [1.4.4] — 2026-09-03

> 🔴 **`v1.4.3` 從未發布。** 它在發布前的覆核中被發現有五項缺陷，其中三項是紅級；
> 主持人裁決退回其中的 `--adopt` 寫入路徑，其餘內容改以 `v1.4.4` 發布。
> **⇒ 你不會在任何地方看到 `v1.4.3`，⛔ 那不是遺漏。**
>
> 🔴 **`v1.4.3` was never released.** Pre-release review found five defects in it, three of
> them red; the principal ruled its `--adopt` write path back out and the rest ships as
> `v1.4.4`. **⇒ There is no `v1.4.3` anywhere; ⛔ that is not an omission.**

### 🔴 The change / 這一版做的事

**Preserve wholesale folder replacement without letting it erase project-owned files.**
**保留整包替換，同時讓專案專屬檔不再住在替換目標內。**

### Changed / 變更

- The filled decomposition prompt moved from `prompts/TEMPLATE_decompose.txt` to the project
  root as `FIRST_IDEA.md` / `第一個想法.md`. It is now project-owned beside `PROJECT.md` and
  never appears in the replaceable-file list.
- `upgrade.py diff` now lists target-only files. `apply` refuses the replacement before making
  a checkpoint or writing anything until those files are moved out. The generated-state
  exception is restricted to the exact package path `scripts/harness/harness_status.json`;
  a project-owned namesake anywhere else still blocks replacement.
- Multi-agent guidance makes `my/` part of the governance role's scope, including project rules,
  incidents, index descriptions, and `my/tools/`; old projects must migrate
  `governance_config.json` by hand because upgrades never overwrite authorisation.
- The update buttons run the read-only diff automatically when `_upgrade/` exists and preserve
  the Python program's exit code.
- Windows installations may omit `.command`; macOS installations may omit `.bat`. A public
  package carrying both is still scanned in full. Routine diff omits a missing foreign launcher,
  while an explicit `apply <exact filename>` remains available for cross-platform packaging.
- The migration checklist now applies to both programmatic and no-code wholesale replacement.
  It separates program-only checkpoint guarantees from the manual backup route and gives a
  no-code procedure for synchronising new public rules without replacing project-owned
  `MY_RULES.md`.
- 🔴 **`policy/` retired: its four documents moved into `governance/`.** The upgrader now
  carries a retired-package list — it ⛔ never deletes your files, but `check`, `diff` and every
  successful `apply` name the orphan folder and say where its contents went. Asking to
  `apply policy` returns a message that says so, ⛔ not a generic "not a framework item".
  🔴 **`policy/` 退役，四份文件併入 `governance/`。** 升級工具⛔ 不刪你的檔案，但會逐一列名。
- 🔴 **The Chinese edition's `讀我` files are now `說明書`; the English edition's `READ_ME`
  files are now `README`.** "讀我" was a literal translation of README, ⛔ not how the thing is
  named in Chinese. Index descriptions were re-keyed in the same round.
- **A new tenth sensor, `sensor_version_consistency.py`,** compares the framework packages
  against each other. 🔴 **Project D ran for weeks with `policy/` at v1.3.0 and the rest at
  v1.4.2, all sensors green** — "half an upgrade" produced no error anywhere.
- **`R-34` gains a clause** (`B-4`): the *scope* of an authoritative statement is itself
  something to check. "This tool cannot do X" being true does ⛔ not make "no tool can do X" true.
- **Counts of the replaceable list were removed from the prose entirely.** They had already
  drifted twice (nine → 16 → 15). ⛔ The list is the authority; a number restating it is not.
- Every path sort in the harness now passes an explicit key. Re-counting found **seven** such
  sites, ⛔ not the six recorded after v1.4.2 — `framework_config.resolve_globs()` was missed.
- 🔴 **The version sensor no longer claims which version is newest.** It compared version strings
  with a string sort, which ranks `v1.9.0` above `v1.10.0`. More fundamentally, the sensor cannot
  see `_upgrade/`, so it has no way to know the target — that is `upgrade.py diff`'s job. It now
  reports the disagreement and points there.
- **The manual, no-code upgrade route now covers the retired `policy/` folder.** A folder that
  retired in the new version has no same-named replacement to put in, so it stays quietly in the
  project; the program route names it, ⛔ and the manual route said nothing.
- **The release version gate now fixes its own output encoding** and ships a `--selftest` that
  runs it under three non-UTF-8 output channels. It crashed with `UnicodeEncodeError` on the
  Traditional Chinese Windows console it exists to run on — ⛔ **a gate that cannot run is not
  a gate.**
- **When a rule carries an override marker with no reason, the sync tool now says the sensor
  will FAIL on it** instead of reporting it as a recorded override.
- 🔴 **A program had been signing a person's name since v1.4.1.** `upgrade.py` called the
  checkpoint program without a mode, so it fell to the human default, which moves the `reviewed`
  tag and prints "I have looked at this". **The consequence was not a moved tag: work an AI had
  finished and a person had not reviewed silently dropped off "what changed since I last looked",
  because the user upgraded the framework.** Reproduced on the released `v1.4.2` tag. The
  checkpoint program now has a third identity, `tool`, and ⛔ neither `tool` nor `ai` may move
  that tag or print a human-review banner. **⛔ A tag that was already moved does not move back
  on its own — SETUP explains how to check and reset it.**
- 🔴 **The rule-sync tool reports drift line by line, ⛔ and never writes over an existing word.**
  🔴 **"The framework revised an existing rule" previously had no prescribed action at all** —
  the sensor reported a FAIL nothing could fix. An `--adopt` flag that overwrote drifted rules
  for you was built for `v1.4.3` and **ruled back out before release**: it wrote before printing
  its own "preview", claimed a checkpoint existed without checking, and still wrote when the
  checkpoint program had explicitly failed. **What was kept is the line-by-line difference — with
  nothing doing it for you, that is what tells you which lines to paste.** ⛔ Marked overrides are
  never listed as drift, and that criterion is shared with the sensor rather than re-implemented.

### Fixed / 修正

- A root glob such as `*.command` resolved to the parent directory, so a neighbouring project's
  launcher could manufacture `COVERAGE_COLLAPSE`. The secondary collapse check also ignored
  `excluded_dirs`, allowing files under `_upgrade/` to manufacture the same false result.
- `tool_my_index.py --help` and unknown arguments used to continue into index generation;
  argument parsing now completes before any write.
- `tool_sync_my_rules.py` ignored `--root`, `--help`, and unknown arguments and could therefore
  write to the project containing the tool instead of the selected project. It now parses all
  arguments before I/O and confines writes to the resolved root.
- Every replaceable framework directory now carries `_VERSION`, `docs/` included; `CITATION.cff` is
  aligned to v1.4.4. A version marker is explicitly documented as a label, not proof that the
  package contents are complete.
- 🔴 **A human checkpoint used to print "reviewed baseline moved" without checking whether
  `git tag -f reviewed` had worked.** With a `reviewed/child` tag present, Git cannot create
  `reviewed` at all and returns 128 — **⛔ and the program still exited 0.** It now checks the
  exit code, reads the tag back, compares it against `HEAD`, and on any failure exits non-zero
  saying the commit was made ⛔ and the baseline did not move.
- 🔴 **The upgrade called a checkpoint commit a receipt without proving the commit contained
  the files it was about to delete.** An ignored same-path hand edit reproduced the failure:
  checkpoint exit 0, no pre-image in its tree, replacement still proceeded, and the edit was
  lost. `apply` now verifies every existing non-transient overwrite path against the checkpoint
  through Git's own filters and fails closed on ignored, untracked, `assume-unchanged`,
  `skip-worktree`, type-mismatched, or target-only content.
- **Upgrade receipts are now durable and usable without raw Git commands.** Each receipt pins
  both checkpoint and authoritative manifest under `refs/spark2groundwork/restore/`, with a JSON
  mirror in Git's private directory. `receipts`, `receipt-diff`, and single-file `restore`
  validate the receipt before use; restore creates an undo receipt first and never moves
  `reviewed`. A downloaded v1.4.4 upgrader uses the checkpoint peer from the same download when
  targeting an older project, so `scripts/` can bootstrap without calling the old checkpoint
  CLI. Receipts have no automatic cleanup in v1.4.4.
- **That restore path now uses the same compatible-peer resolver as apply.** It prefers the
  `checkpoint.py` beside the running upgrader, then a compatible project copy, and recognises
  compatibility by reading an exact tool-API marker without executing the candidate. If no peer
  matches, it writes nothing and tells the user to download the complete same-edition,
  same-version package. A receipt is durable inside this Git repository; ordinary clone or file
  backup does not carry its private ref automatically.
- 🔴 **A Chinese package could overwrite an English project, or the reverse, with exit 0.** Apply
  now derives a v1.4.4 edition fingerprint from the three language-specific launchers. Complete
  Windows-only, macOS-only, and dual-platform layouts pass; cross-edition, mixed, and incomplete
  signatures fail before checkpoint, receipt, or replacement. Other project-owned launchers are
  ignored. A formal package edition field is deferred to v1.5.0.
- 🔴 **The reset instructions for already-affected projects only covered `snapshot …`.** On a
  clean working tree — the common case — the old upgrader moved the tag onto an existing `auto:`
  commit instead, ⛔ and `auto:` is also what a legitimate human review looks like. SETUP now
  walks three steps, says outright which evidence proves nothing, and ⛔ tells you not to guess
  or reset when neither step can tell.
- `--adopt` had been removed from the program while three pieces of current instruction still
  told users to add it. Those are cleared, and a static scan now fails on any withdrawn flag
  that survives in current instructions without being marked as withdrawn.
- 🔴 **The extraction tool wrote files whose own hash it then recorded, without fixing the line
  ending.** On Windows those files land as CRLF while `.gitattributes` normalises the repository
  copy to LF — so the next clean checkout makes every recorded hash mismatch and
  `CORPUS_MD_MODIFIED` fires on the whole corpus, **with not one character changed**. The tool
  now writes with `newline="\n"`; a project that has already run it should run it once more.
  A static check requires every module that computes hashes to fix its line endings, and is
  itself paired with a planted violation and a must-not-flag sample.
- **The Claim Ledger sensor re-hashes every extract on every run, and never said so.** Its stats
  line was empty, so two separate reviewers seven days apart concluded no sensor was comparing
  the manifest. The count is now printed, including as `0` when the corpus is empty.
- **Three failure families were added to the incident log** — two writers sharing one
  identifier space where **each allocation looks successful locally and the collision is only
  visible after the merge** (measured three times in one day; "re-read before allocating" does
  not stop it), a batch edit that succeeds while
  doing the wrong thing (**a diff cannot catch it**), and a constant tuned for one environment
  copied verbatim into another (**both sides are textually identical, so every consistency
  check reports consistent**) — along with two new variants of "index as authority": measuring
  a proxy and treating it as the fact, and reading a scoped statement as a universal one.
- **The index tool called a file inside the exclude list "does not exist".** It asked only
  whether the scan had seen the path and never looked at the disk, so a real file under an
  excluded folder was reported as moved or renamed — and deleting the note, which the message
  invites, does not fail, so nobody finds out. Present-but-excluded is now its own WARN.
  **索引工具把「在排除範圍內的檔案」說成「檔案不存在」。** 它只問掃描有沒有看到，
  ⛔ 從來沒看過磁碟。⇒ 現在先 `exists()`，兩種情形給兩個代碼。
- **Constitution §6.1 contradicted general rule 2 nine lines below it and §6.3.** "In every
  situation, ledgers are in no AI's output area" against "that is a default, not a
  prohibition" and "the user may authorise anything; `deny` is the mechanical counterpart" —
  all three in one T0 document. The first is now stated as a default governed by `deny`. What
  is not fixed: a project's ruling on a framework clause still has nowhere to live that an
  upgrade will not overwrite.
  **憲章 §6.1 與同節第 2 條通則及 §6.3 直接矛盾，三句話在同一份 T0 裡。**
- **The edition gate refused without saying what it saw.** It reads only the twelve framework
  launcher names and not who put them there, so a legitimate Chinese project owning a file
  called `snapshot.bat` read as "mixed" and the whole upgrade was refused — while the message
  asked for a fresh download, which was never the cause. The refusal now lists the launchers
  found on each side with their edition. The decision itself is unchanged: the inventory runs
  only on the failure path.
  **語言版本閘門被擋下時不說它看到了什麼。** 它只讀那十二個框架啟動器檔名、不看是誰放的，
  ⇒ 一個自有 `snapshot.bat` 的合法中文專案會被判「混合」而整次拒絕，⛔ 而訊息叫人重新下載
  套件——那從來不是原因。現在會逐一列出兩側看到的檔名與所屬版本；**判定邏輯未變。**
- **A rule citation in the framework's own source pointed at a rule that does not exist.**
  `anchor_norm.py` cited `R-43` twice while `RULES.md` ends at `R-35`; both statements are in
  fact `R-27`. No sensor checks rule-ID references — one checks files, another checks sections —
  so it survived every green run. The English edition never carried the citation at all.
  **框架自己的原始碼引用了一條不存在的規則。** `anchor_norm.py` 兩處寫 `R-43`，
  ⛔ 而 `RULES.md` 只到 `R-35`；那兩句其實都是 `R-27`。⛔ **沒有任何一支感測器在查規則 ID 引用**
  （一支查檔案、一支查章節），⇒ 它在每一次全綠中存活。英文版⛔ 從來沒有這個引用。

### Self-tests / 自測

**79 → 159. Sensors 9 → 10.** New paired cases cover parent-directory and excluded-directory
glob contamination, real collapse preservation, optional foreign launchers on Windows and
macOS, no-write CLI help/error paths for both index and rule-sync tools, exact `--root`
confinement, exact-path transient filtering, target-only refusal before a checkpoint,
successful wholesale replacement after project data is moved out, routine-omit/explicit-apply
launcher behaviour, a static AST check that no path sort omits its key, version consistency
across packages (including that the sensor's package list and the upgrader's list are the same
names), the `reviewed` tag staying put under `tool` and `ai` while human mode still moves it,
a human checkpoint refusing to report success when the tag cannot be created, an upgrade
refusing to overwrite when it cannot name its own restore point, a static scan for withdrawn
CLI flags surviving in current instructions, and the retired-package list (must list a
surviving orphan, ⛔ must stay silent for a clean new project, ⛔ must not overlap the
replaceable list). Receipt cases additionally cover ignored same-path content, both Git index
hiding flags, tracked hand edits, CRLF normalisation, persistent ref/manifest integrity,
single-file diff/restore with an undo receipt, stable `reviewed`, path confinement, missing-file
refusal, exact transient scope, target-only empty directories, manifest tampering, same-edition
Windows/macOS/dual layouts, cross/mixed/missing edition rejection before any write, post-bootstrap
restore through the downloaded peer, and missing-compatible-peer restore refusal.

⚠️ **Worth recording: an existing sample went red the moment the receipt gate was added, and
the tool was right — its fixture had no git repository at all.** 🔴 **The fixture was fixed,
⛔ not the assertion.**

### ⛔ This release does not claim / 本版不宣稱

- Native macOS execution of `.command` has not been run in this Windows maintenance environment.
- F-08 (ledger anchors and index wording in Project D) is outside v1.4.4.
- Unknown CLI arguments still use argparse's exit code 2; harmonising tool errors with the
  framework's PASS/FAIL/INCOMPLETE semantics is deferred to v1.5.0.
- Project D's `FIRST_IDEA` / `_human` permission semantics are deferred to v1.5.0, and this
  correction does not update Project D.
- 🔴 **`corpus_md/` was ⛔ not merged into `corpus/` in this release.** `policy/` is a framework
  folder the framework can move on its own; `corpus_md/` holds user data that only a person can
  move. ⛔ Different risk, so they were deliberately split across two versions — the merge is v1.5.0.
- ⛔ **An existing project's empty `policy/` folder is not removed by anything.** The upgrader
  names it; deleting it is the user's action.
- Green sensors do not prove substantive research correctness.

---

## [1.4.2] — 2026-08-28

### 🔴 The change / 這一版做的事

**One defect, found by releasing v1.4.1: the file index was sorted by platform, not by name.**
🔴 **索引的排序取決於作業系統，⛔ 而不是檔名。**

### Fixed / 修正

- 🔴 **`tool_my_index.py` sorted `Path` objects.** ⚠️ **`WindowsPath` comparison casefolds
  first; `PosixPath` does not** — so `PROJECT.md` sorts before `corpus/` on Linux and after it
  on Windows.
  ⛔ **The index shipped with v1.4.1 was generated on Linux, so `sensor_my_index.py` reported
  `MY_INDEX_STALE` on the first run on a Windows machine.**
  **⚠️ What it reported was ⛔ not "the index is stale" but "your operating system is not the
  one that generated it" — and it had already forced a manual workaround mid-release.**
  🔴 **A criterion that fires on a correct state teaches people to ignore it (`R-19`).**
  **The sort key is now the relative posix string. ⛔ Never the `Path` object.**

### Self-tests / 自測

**78 → 79.** ⚠️ **The new sample is honest about its reach: it only lights up on a
case-insensitive filesystem (Windows, macOS). ⛔ On Linux the old and new code agree, so it
cannot fire there** — it is kept because the release procedure runs the self-test on Windows.

### ⛔ This release does not claim / 本版不宣稱

- ⛔ **That every generated artefact is now reproducible across platforms.** ⚠️ **Only this one
  was examined. The general shape — "sorted() on a type whose ordering is platform-dependent" —
  ⛔ has not been swept for.**

---

## [1.4.1] — 2026-08-27

### 🔴 The change / 這一版做的事

**Six defects where a document and the code disagreed, or where one of them was inert.**
🔴 **The most consequential: an upgrade deleted the rules a project had accumulated,
while `PROFILE_solo.md` was actively telling users to accumulate them.**
🔴 **升級會刪掉專案自己累積的規則，而說明書正在鼓勵使用者去累積。**

### Added / 新增

- 🔴 **`my/`** — everything in it belongs to the project and is ⛔ never touched by an upgrade:
  `MY_RULES.md` (project rules `P-xx`, with the framework's rules copied verbatim into §1),
  `MY_INCIDENTS.md` (moved from `incidents/`, now also holds the project's own failure
  families `專-①`), and `tools/` for scripts the project writes itself.
  **⚠️ `tools/` exists because a self-written script placed in `scripts/` is deleted by the
  next upgrade — observed in a live downstream project.**
- 🔴 **`scripts/harness/sensor_my_rules.py`** — checks that `my/MY_RULES.md` covers every
  framework rule (`RULE_MISSING_IN_MY` / `RULE_TEXT_DRIFT` / `OVERRIDE_WITHOUT_REASON`).
- **`scripts/harness/tool_sync_my_rules.py`** — copies newly added framework rules in verbatim.
- 🔴 **`governance_config.json` now ships** at the project root with the permission settings.
  ⚠️ **It is on the upgrade tool's never-replace list — the settings finally live somewhere
  an upgrade cannot erase.**
- **`governance/CLAIM_LEDGER_SPEC.md`, `governance/CONJECTURE_LEDGER_SPEC.md`** — the ledger
  specifications, moved out of `ledgers/`.
- **`handoffs/`** now ships. ⚠️ **It never did, while the whole handoff ritual pointed at it.**
- **Constitution §6.4 — "a file may have exactly one owner"**, with the criterion for
  deciding which of the three treatments a document gets.
- 🔴 **`my/MY_INDEX.md` — an index of everything in the project that is yours**, generated by
  `scripts/harness/tool_my_index.py` and watched by `sensor_my_index.py`; the descriptions
  live in `my/MY_INDEX_notes.json` and are AI-maintained.
  ⚠️ **Why: a project that adopted v1.3.0 stopped maintaining its own file index — its
  `file_index.md` holds not one research-related entry. 🔴 `file_index.md` began as a
  predecessor project's table for research documents; the contents became the framework's own
  and the name did not change, so the framework displaced a mechanism that already existed.**
  ⛔ **The criterion is "everything the framework does not own", never a list of what to
  include — a list of what to include is a whitelist (`R-21`).**

### Fixed / 修正

- 🔴 **An upgrade deleted a project's accumulated rules** (`governance/` is replaced
  wholesale). ⚠️ **Verified by experiment, ⛔ not by reading the code.**
- 🔴 **`t0_docs` was folded into `denied` in code**, so no configuration could turn T0
  protection off — while the config comment said the opposite. **T0 is now listed in the
  `deny` default instead. ✅ "Clear `deny` and you have full authorisation" is true for the
  first time.**
- 🔴 **The permission check was skipped entirely when `write_scopes` was empty** — and
  `PROFILE_solo.md` tells solo projects to leave it empty. **So `deny` had never been in
  effect in a solo project.** Now a solo project gets a WARN listing the files.
- 🔴 **An unrecognised key in `governance_config.json` was silently absorbed.** Now a FAIL
  that names the closest valid key.
- 🔴 **Framework updates to the ledger specifications could never reach an existing project**
  (`ledgers/` is on the never-replace list). The specs moved to `governance/`.
- **Two dangling citations to `PROFILE_multi_agent.md` §4.3**, a section that no longer
  exists, plus "four attack points" where there are five. ⚠️ **The sensor had been reporting
  this every round and nobody read the output.**
- `attribution_globs` / `artifact_globs` pointed at `outputs/` and `reports/`, **two
  directories that never existed.** ⚠️ **They are ⛔ not being created — where research output
  lands is defined in v1.5.0. `MODEL_IDENTITY.md` §3.4 now states the resulting gap.**

### Documentation / 說明

- 🔴 **Both figures redrawn for v1.4.1**, in both editions: `my/` replaces `incidents/`,
  the ledger specs appear on the framework side, `handoffs/` and `governance_config.json`
  are shown as shipped, and **an arrow now shows what an upgrade does to your rules.**
- 🔴 **The figures are now produced by a generator, ⛔ no longer hand-edited SVG.**
  ⚠️ **Every box width is computed from its own text, so the generator fails loudly instead of
  producing an overflowing box** — **the v1.3.0 defect where one pill width was copied
  verbatim between editions and the English line was 306px wide cannot recur by construction.**
  **⛔ The generator is a maintainer tool and does not ship (decision 42).**
- **All three READMEs**: the file list is now split into "yours" and "the framework's",
  with the reason (§6.4) stated where the reader meets it.

⚠️ **Verified with Chromium `getBBox()`: 0 overflows and 0 overlaps across all four figures.**
🔴 **That measurement found two defects the eye did not: a 2px text collision present only in
the Chinese edition, and a blind spot in the measurement itself** — a band's left column could
run into the boxes beside it without being flagged, because the band rectangle was too wide to
count as "the containing box". **The criterion moved into the generator.**

### Self-tests / 自測

**57 → 78 paired samples.** Both editions pass. **Sensors 7 → 9.**

### Fixed after the principal ran it on their own machine / 主持人實跑後修正

- 🔴 **`sensor_scope_and_t0.py` crashed** with `AttributeError` when `git` returned exit 0
  with `stdout` set to `None`. ⚠️ **The code path had been there since v1.0.0 and had never
  once run**, because the old code skipped the whole block when `write_scopes` was empty and
  `PROFILE_solo.md` tells solo projects to leave it empty. **Making `deny` effective did not
  cause the crash; it revealed it.** 🔴 **Cause, established by a diagnostic run on that machine (⛔ not guessed):**
  with `text=True` and no `encoding`, Python decodes the child's output with the locale
  encoding — `cp950` on Traditional-Chinese Windows — and git prints paths in UTF-8.
  **The decode fails inside `subprocess`'s reader thread, that thread dies, the exception
  never propagates, and `communicate()` returns `None`.** ⛔ **The standard library turned an
  error into a silent empty value.**
- 🔴 **The same fix already existed in two files in the same folder and had never been carried
  to the third**: `checkpoint.py` and `review_changes.py` both state
  `encoding="utf-8", errors="replace"`. ⚠️ **`_common._force_utf8()` fixes what the harness
  *prints*, ⛔ not what it *reads* — a true fix whose scope did not cover the other channel
  (`R-34`). Its docstring now says what it does not cover.**
- **New static self-test**: any `subprocess.run` in the harness that decodes without naming
  an `encoding` is a FAIL, named as `file:line`.
- 🔴 **`docs/` and the six launcher buttons were never on the upgrade tool's replaceable list**,
  so the seven figure-layout fixes shipped in v1.3.0 **reach no existing project.** They are on
  the list now. ⚠️ **This was caught by `tool_my_index.py` on its first run**, because they
  appeared in the list of "things the framework does not own".
  ⛔ **`.gitignore` and `.gitattributes` are deliberately left off** — mixed ownership, per §6.4.
- 🔴 **A project sitting in a subdirectory of a repository no longer refuses to report.**
  The report is narrowed to that subtree, with paths outside it dropped. ⚠️ **The framework's
  own repository has that shape, and so does any project dropped into an existing notes repo —
  the old behaviour was a light that is always on (`R-19`).**

### ⛔ This release does not claim / 本版不宣稱

- ⛔ **The permission model is not rebuilt.** ⚠️ Seven separate mechanisms still express
  permission; ⚠️ this release fixes the ones that were false or inert. **The single table is
  v1.6.0.**
- ⛔ **Research-side document management does not exist yet.** ⚠️ `research/` is v1.5.0;
  **the main text still has nothing watching its author field.**
- ⛔ **`sensor_my_rules.py` does not judge the quality of a `P-xx`**, nor whether an
  override's reason is sound — only that the line has text.

---

## [1.4.0] — 2026-08-26

> 🔴 **⛔ 1.4.0 was never released on its own: it carries no git tag.**
> **It was prepared, then folded into 1.4.1 and pushed as one release.**
> ⚠️ **This note exists because a changelog entry with no tag behind it is
> "the document says it shipped" with nothing under it.**
>
> 🔴 **⛔ 1.4.0 沒有單獨發布，也沒有 tag。** 它備妥之後併入 1.4.1 一起推。

### 🔴 The change / 這一版做的事

**Three start-up prompts for the multi-agent setup**, a **prior-art template that actually
works out of the box**, and **`scratch/` finally explained.**
**多角色情境現在有三份可以直接貼的開工指令。**

### Added / 新增

- 🔴 **`prompts/START_governance_AI.md`, `START_research_AI.md`, `START_audit_AI.md`**
  (`START_治理AI.md` / `START_研究AI.md` / `START_審計AI.md` in the Chinese edition).
  ⚠️ **`PROFILE_multi_agent.md` told you to set up three roles and to "put this in the
  governance role's standing instructions" — ⛔ while no such document existed anywhere.**
  Each file is self-contained: model declaration, write scope, the tools that already exist,
  verification tags, the academic bottom lines, decision rights, what to do when an
  instruction conflicts with a rule, the closing packet, and **how that particular role helps
  the framework grow.**
  ⚠️ **A solo setup does not need these** — `INITIALIZE_PROMPT.md` still covers it.
- **A title-accuracy clause in `_COMMON_BLOCKS.md` block A.** ⚠️ **Found because an assembled
  prior-art prompt still failed the deep-research check** — the clause was simply not in the
  parts bin.

### Changed / 變更

- 🔴 **`TEMPLATE_prior_art.txt` now ships assembled.** It used to be 24 lines, six of them
  `<<<paste block X>>>`, ⛔ **unusable as shipped**, and it was the one file that failed the
  self-containment check by design — **with half a page in `prompts/README.md` explaining why
  that failure was correct.**
  ⚠️ **That is a framework saying "every prompt must stand on its own" and then shipping one
  that does not, plus an official note calling it fine.**
  **It now passes both plain and `--profile deep-research`.**
- **`prompts/README.md` rewritten.** ⛔ The half-page explaining the expected failure is gone.
  ⚠️ **In its place is the cost that is actually still there:** the assembled template
  duplicates the parts-bin text, **⛔ and no program watches those two copies for drift** —
  the clause-sync check reads single-line term lists, not multi-line passages.
- **`scratch/` is now explained where it is used.** It is named in the constitution, assigned
  to the audit role, and excluded from scanning — ⛔ **and nothing ever told you it does not
  come with the framework.** It cannot: it is in `.gitignore` by definition, since a sandbox
  under version control is not a sandbox. **`SETUP.md` and `PROFILE_multi_agent.md` now say
  to create it yourself.**

### ⚠️ Upgrade notes / 升級注意

- **Nothing breaks.** These are additions and a rewritten template.
- ⛔ **No rule IDs changed.** `R-01`–`R-35` are unchanged.

### ⛔ What this release does not claim / 這一版不宣稱什麼

- ⛔ **The two copies of the block text are not watched.** Stated in `prompts/README.md` and
  repeated here so it is not forgotten quietly.
- ⛔ **The start-up prompts have not been tested with a real three-role project.** They were
  written from a working example and checked mechanically for self-containment,
  ⚠️ **which is not the same as having been used.**

---

## [1.3.0] — 2026-08-26

### 🔴 The change / 這一版的主要變更

**Short-form section citations are now checked.** `sensor_governance_text.py` resolved only the
long `` `<file>.md` §N `` form, while the framework itself writes **"constitution §N" in 68 places
(Chinese) and 58 (English)** — and its scan never reached `scripts/**/*.py` at all.
**Three dangling citations had been living there**, found by hand at v1.2.0 release time.
**短式章節引用現在查得到了。**

### Added / 新增

- 🔴 **`corpus/` and `corpus_md/` now ship with the framework**, each with a short note inside
  saying what belongs there. **`corpus/` also contains a blank `BIBLIOGRAPHY.docx`** —
  export your references from Zotero or EndNote into it, and **from then on every citation in
  the project follows that file, ⛔ not what the AI says.**
  ⚠️ **Why:** a model will get DOIs, page numbers and years wrong, and **a wrong one reads
  exactly like a right one.** A bibliography you maintain yourself is something to check against.
- **`CORPUS_EMPTY` (WARN)** — the extraction folder exists but holds nothing yet.
  ⛔ **Not the same as "could not check"** (see Fixed).
- **Config key `section_ref_aliases`** — `{anchor word: target file}`. ⛔ **Not hard-coded**:
  `R-21` forbids a whitelist as the definition of scan scope, and a downstream project's short
  name for its constitution will not be this one's. Absent key → the check simply does not run
  for that project, ⛔ and the statistic says so.
- **`ALIAS_TARGET_MISSING` (INCOMPLETE)** — an anchor is configured but its target file is not in
  the tree. ⛔ **Not a silent skip** (`R-33`).
- **A "section citations checked" statistic.** ⛔ Silence is not a pass.
- **Four paired fixtures**, ⛔ two of them the "must not false-alarm" half:
  `secref_alias_bad` / `secref_alias_ok` / `secref_py` (the citation lives in a `.py` header) /
  `secref_fence`. **Self-tests 50 → 54.**

### Changed / 變更

- **The section-citation check now runs over `code_globs + launcher_globs + governance_globs`** —
  the same scope as `sensor_reference_integrity`. ⚠️ **That sensor exists because `.py` headers
  were never scanned; ⛔ it fixed *file* references and not *section* references.
  The same hole was half-fixed, and the half that was fixed made it look closed.**

### Fixed / 修正

- **Three dangling constitution citations** — already fixed in the v1.2.0 release commit;
  this version is what stops the next one.
- 🔴 **A heading inside a fenced block was counted as a heading.** The first run after the scope
  widened reported `HANDOFF.md` as having two `## 3.` sections; one was a line inside the fenced
  template. ⚠️ **The defect was already in the long-form check** and had simply never been
  reached. ⛔ **Fixed by stripping fenced blocks, not by an exemption list** (`R-20`/`R-21`).
  **Stated cost: a real heading inside a fenced block becomes invisible. ⛔ Nobody writes that.**
- 🔴 **"Which folders does an upgrade touch" is now a measured fact, not a sentence in a guide.**
  ⚠️ **The behaviour was already right** — the tool recognises five framework folders and four
  framework files and refuses every other target, so **a folder a user invented was never a
  candidate.** ⛔ **The documentation was what read backwards**: it described protection as a
  *list of protected items*, **and a list reads as "only these are safe".**
  **Rewritten everywhere to state the guarantee the other way round**, and
  **`upgrade_case()` in the self-test now proves it**: a folder the tool has never heard of is
  refused and left byte-identical, **even when the upgrade source contains one by the same
  name.** ⛔ The "your data" list is documented as what it is — **a better error message, not
  the defence.** **Self-tests 56 → 57.**
- **Constitution §6.2 gained a clause on folders the user creates**, saying plainly that
  ⛔ **no registration is required**, and naming the two mechanical reasons they are safe.
- **`profiles/PROFILE_external_tools.md` corrected**: it said `external/` was "not on the
  protected list", which ⚠️ **was true and read as a warning about something that was never at
  risk.**
- 🔴 **A brand-new project reported INCOMPLETE on its very first run.** Shipping an empty
  `corpus_md/` tripped a check that knew only two states — *no directory* and *directory
  without a manifest*. **It had no third state for "a directory with nothing in it yet".**
  ⚠️ **With nothing to protect, there is no "could not protect it"** — and ⛔ **a first run
  that cries wolf is what teaches people to ignore the output.**
  ⛔ **Fixed structurally, not with an exemption**: the criterion now keys on whether
  extractions exist. **Self-tests 54 → 56.**
- 🔴 **The figures overflowed and collided — in both editions.** The divider pill in
  `fig1_architecture.svg` carried `width="260"`, **identical in both files**: the Chinese
  sentence fits, the English one is 306px wide, **so the dashed line ran straight through the
  text.** ⚠️ **The same shape as the sentence-length constant in `SENSOR_CHANGELOG` pre-history
  #2 — a constant tuned for Chinese, ported unchanged — ⛔ this time in SVG coordinates.**
  Seven overflows and collisions were found and fixed across the four figures.
  ⚠️ **Found by rendering each SVG and reading every element's `getBBox()`, ⛔ not by eye:**
  the Chinese constitution box was 1.5px inside its padding — **invisible to a reader,
  and still wrong.**
- **Drifting counts removed from the figures** (`7 sensors`, `8 failure families`,
  `policy/ × 4`, `profiles/ × 4`, `three templates`). ⚠️ **All five were correct at the time.**
  🔴 **The README deliberately carries no counts (`R-16`) while the figures did — and a figure
  is read as authority more often than the README is.** `R-01`–`R-35` is kept: that is an id
  range, ⛔ not a count. Exit codes and "three buttons" are kept: design constants.

### Changed: the three guides / 三份說明文件

🔴 **`README.md` at the root, and `README.md` + `SETUP.md` in both editions, were rewritten for
readers with no programming background.**

- ⛔ **`git clone` is gone.** Getting started is now: **Download ZIP → unzip → copy the folder
  for your language → rename it to your project.** ⚠️ Anyone who prefers `git clone` already
  knows how, and did not need the instruction.
- **A new section on pointing your AI at the folder**, with the actual steps for
  **Claude (Cowork)**, **Gemini (Antigravity)** and **ChatGPT (Projects)**.
  ⚠️ **Stated plainly: a ChatGPT project has a file limit and cannot see your folder** —
  `profiles/PROFILE_chat_only.md` is written for that case.
- **The root README is now written in English throughout** (the two opening lines stay in
  Chinese), because both editions are linked at the top. ⚠️ **Two languages interleaved in one
  document made it harder to read in either.**
- **Plainer wording, and notes written for the AI rather than the reader were removed.**
  These are documents for people.
- 🔴 **A section on the framework growing with you**, in all three READMEs:
  *there is no perfect framework — only one that gets better as you use it.*
  **You say "log that" when something goes wrong; the AI finds the repeating pattern;
  ⛔ you decide whether it becomes a rule.** After a while your copy stops looking like anyone
  else's, **and that is the point.**
- **`profiles/` rewritten, all four, in both editions.** Each now says how the framework keeps
  improving *in that particular setup* — ⚠️ **including the chat-only one, where the growth
  goes into the text you paste at the start of every conversation.**
  Arguments are self-contained rather than pointing at rule numbers, and the file lists match
  the v1.3.0 layout (`corpus/`, `corpus_md/`, `incidents/`).
- **ChatGPT is now documented as Work mode in the desktop app**, which links a live local
  folder and is the equivalent of the other two. ⚠️ **Web ChatGPT is described separately**,
  since it holds uploaded copies with a file limit.
  **Claude Code and Codex are named as working too** — ⛔ **without steps, because they have
  not been tested here**, and with the warning that a coding agent will not pause for the
  snapshot habit on your behalf.

### ⚠️ Upgrade notes / 升級注意

- **A project that was green on v1.2.0 can go WARN on v1.3.0.** That is the point.
  Set `section_ref_aliases` to your own short name, or leave it unset and the check does not run.
- ⛔ **No rule IDs changed.** `R-01`–`R-35` are unchanged.

### ⛔ What this release does not claim / 這一版不宣稱什麼

- ⛔ **It does not claim every citation form is now checked.** One anchor is configured.
  **`R-35`: that is the result of taking stock — ⚠️ and nobody has taken stock of whether a
  third form exists.**
- ⛔ **It does not claim a citation points at the right content** — only that the section exists
  and is unique.
- ⛔ **Nothing compares the two editions.** Still true, and still done by hand.
- ⛔ **Nothing checks the figures.** No sensor reads `.svg`. The layout defects above were
  reported by a human and measured with a throwaway script that is ⛔ **deliberately not
  shipped** — **a known and accepted gap, not an overlooked one.**

---

## [1.2.0] — 2026-08-26

### 🔴 The headline changes / 這一版最重要的三件事

1. **One file to fill in.** Everything a user must author now lives in `PROJECT.md` at the root;
   every other governance document is AI-maintained. **使用者只需要填一個檔案。**
2. **Buttons, on both platforms.** `snapshot` / `review changes` / `check update` ship as
   `.bat` **and** `.command`; the logic behind them lived in **8 near-duplicate files**
   (four batch scripts of 203–246 lines, plus four shell scripts) and now lives in **2 Python
   files** per edition — the six launchers are 40–43-line shells. macOS is supported for the
   first time. **兩個平台都有按鈕。**
3. **Folder-level upgrades.** Framework folders can be replaced wholesale from GitHub while
   `PROJECT.md`, ledgers, corpus, handoffs and `incidents/` are never touched.
   **框架可以整包升級，你的資料不會被碰。**


**Theme: the two editions are now actually equivalent, and the harness now fails loudly
instead of quietly passing.**
**主題：兩個版本這次真的對等了；檢查工具不再「靜靜地通過」，而是會出聲。**

### ⚠️ Why this release exists / 這個版本為什麼存在

v1.0.0 shipped two editions described as "independent and equivalent". **They were not.**
The English edition was missing one sensor outright and three checks inside another; the two
prompt sensors were two different programs; thresholds differed between editions with the
divergence registered nowhere. **A weaker sensor reads as a cleaner document** — which is the
failure this release is mostly about.

v1.0.0 宣稱兩個版本「各自獨立且對等」。**它們並不對等。**
英文版整支少了一個感測器，另一支少了三項檢查；兩版的 prompt 感測器根本是兩支不同的程式；
門檻不一樣而且沒有登記在任何地方。**一支較弱的感測器，會被讀成一份較乾淨的文件**——
這一版修的主要就是這件事。

### Added / 新增

- **`sensor_reference_integrity.py`** — whether a referenced file actually exists, including
  `.py` / `.sh` file headers, which had never been scanned.
  **被引用的檔案存不存在**（含從未被掃過的 `.py`／`.sh` 檔頭）。
- **`sensor_clause_sync.py`** — whether a clause list copied into a prompt still matches its
  home. Exists because `R-24` (prompts must be self-contained) and constitution §3.2 (one home
  per rule) exclude each other, **and the product of that exclusion is silent drift.**
  **被抄到 prompt 裡的條款清單是否仍與定義處相同。**
- **`tool_extract_compare.py`** — strict / loose / gap columns, so "normalisation does not cover
  this" and "the extraction is poor" stop looking the same.
- **`R-33`** ⛔ "nothing to do" must not be the default branch after a failed operation.
- **`R-34`** capability boundaries are read off the tool list, ⛔ not asserted from memory.
- **`R-35`** "none" must be the result of taking stock, ⛔ never an omission. Raised to a rule
  because the same sentence appeared **verbatim in four places** across two documents, each
  with a complete context of its own — one higher-order principle instanced in four settings.
  All four sites now cite it. ⛔ Not reworded to dodge the sensor.
  **「無」必須是盤點的結果**——同一句話原本逐字散在四處，現在四處都引用 `R-35`。
- **Constitution §4.1.1** — an exit-code disposition table (0 / 1 / 2).
- **`Audit_Protocol.md` §6** — cross-family is not independence (with verified source anchors).
- **`Claim_Ledger.md` §1.1 rule 5** — ⛔ an anchor must not span a page break.
- **`Conjecture_Ledger.md` §0.2** — an optional "why I could not fill this" field, so a
  deliberate blank stops looking like a forgotten one.
- **A new failure family: "text about a defect, and the defect itself, are indistinguishable to
  string matching"** — with two forms running in opposite directions and taking opposite
  dispositions: mentioning it *commits* it (reword into description, add no exemption), and
  mentioning it is *mistaken for* committing it (quotation detection, ⛔ not an exemption list).
  Tagged `[framework's own]`, a new provenance tag: **it happened while maintaining this
  framework**, not to somebody else.
- **Two cross-cutting axes named above the family table.** Axis one: *two states carrying very
  different information look identical on screen* (four families sit on it). Axis two: *one fact
  has two copies and only one gets updated*. ⛔ **The families on an axis are deliberately not
  merged** — a family covering five families recognises no shape at all.
- **Constitution §6.2 defines the operational directories** (`scratch/`, `archive/`,
  `_to_delete/`). They appeared in `.gitignore`, in `excluded_dirs`, in the constitution and in
  the audit protocol — **four places using them, none defining them**, the same shape "output
  area" was in before §6.1. **Nothing in `scratch/` may be cited**: it is not version-controlled,
  so a citation into it reads exactly like a well-founded one and resolves to nothing.
- **`HANDOFF.md` §3.3: section 4 must carry the raw output of `git diff --stat`.** It is the one
  part of a handoff packet that can become a mechanical fact at zero cost. **What it blocks is
  not lying but under-reporting** — a file list written from memory comes up short, and the
  missing entries look exactly like files that were never touched.
- **A root `CHANGELOG.md`** — this file.

### Changed / 變更

- **Failure families are now cited by name, never by number**, across every document and
  source comment. The number is the table's ordinal; the name is the identifier.
- **The "fixed one layer, missed another" family gained two forms** — the second copy living on
  *a carrier that evaporates* (a conversation, screen output, memory), and *a number written into
  prose*. **The "index as authority" family gained a third variant**: treating "this looks like a
  known family" as "this is that family" — 🔴 **a failure the family table itself induces.**
- **Predicted failure families moved to their own `P1`–`P6` namespace.** They used to share one
  run of circled numbers with families that had actually occurred, so the next number for a new
  occurred family was ⑭ — and if a predicted family were ever removed or promoted, its number
  would fall free and be reused, **silently retargeting every citation that used it.**
  **預測家族改用獨立的 `P1`～`P6` 命名空間**——兩套命名空間結構性地不可能相撞。
- **`R-10` no longer cites an incident-log case.** A downstream project's incident log is its
  own; inserting a case ahead of the cited one shifts the numbering while the citation still
  resolves. **A citation that silently retargets is worse than one that dangles, because it
  stays green.** The rule now carries the mechanism and the reason; the log carries the
  verbatim evidence.

- **Both editions brought into equivalence.** The English edition gained
  `sensor_model_attribution.py` (absent entirely), three checks inside
  `sensor_conjecture_ledger.py`, and English text for three changelog sections that had been
  left in Chinese.
- **`sensor_model_attribution.py` rewritten.** Hard-coded filenames **25 → 0**; dangling
  references **9 → 0**. The old whitelist existed only to suppress alarms a wrong scan scope
  had created.
- **`sensor_prompt_self_contained.py` split into two layers** — self-containment always;
  the deep-research clause table only under `--profile deep-research`. Previously **all three
  templates the framework ships came out FAIL**, and `prompts/README.md` had written the
  excuse for it.
- **`tool_pdf_to_md.py`** — PyMuPDF primary with a pypdf fallback, and **the backend is
  recorded**. Degrading is fine; degrading silently is not.
- **`ai_checkpoint.sh`** — role + model + topic mandatory, UTC timestamps, sweeps every stale
  git lock, falls back to `mv` where deletion is denied, **and checks `git add`'s exit status.**
- **`framework_config.py`** — `load()` now takes the scanned root, so `--root` no longer reads
  another project's configuration in silence.
- **Self-tests: 12 → 50**, over 43 paired fixtures.
- **Both T0 documents rewritten and trimmed**, and one contradiction between them removed.
  The six academic bottom lines now have **one home, `AGENTS.md` §3**; `RULES.md` §A carries
  `R-01`–`R-04` as **four one-line pointers naming the item each maps to**.
  ⛔ **The four rows are deliberately not collapsed into the range `R-01`–`R-04`**: the mapping
  is not contiguous (`R-03` → item 5, `R-04` → item 6), and a range would state something true
  while losing which rule is which. **Items 3 and 4 carry no `R-xx`** — that is the result of
  taking stock, ⛔ not an omission, and has been so since v1.0.0.

### Fixed / 修正

- 🔴 **INCOMPLETE could be swallowed by a later FAIL.** Exit codes `[2, 1]` aggregated to `1`,
  so "a sensor never managed to check" disappeared behind a fixable failure.
  **一支感測器根本沒查成，會被後面一支 FAIL 蓋掉。**
- 🔴 **"Must not false-alarm" tests were checking nothing.** WARN-level findings do not change
  the exit code, so any number of WARN-level false alarms printed ✅.
  **「不得誤報」那一半的測試，對任意多筆 WARN 級誤報一律印 ✅。**
- 🔴 **A glob that matches nothing is not automatically fine.** When the directory holds files
  of that extension and the glob still sees none, that is coverage collapse → INCOMPLETE.
- 🔴 **`sensor_self_certification.py` returned PASS on a real audit report** containing six
  phrases its own protocol bans.
- **`sensor_governance_text.py`** — a character-count threshold is systematically weaker for
  Chinese; the sentence splitter knew only `。` and newlines, so the English edition was
  comparing whole lines only.
- **`tool_pdf_to_md.py` created an empty output directory before checking whether there were
  any PDFs** — flipping a clean harness from 0 to 2, invisibly, because git does not track
  empty directories.
- Numerous dangling file and section references across both editions, including ones the
  framework itself promised and did not ship.
- 🔴 **`policy/MODEL_IDENTITY.md`: the English edition was a 62-line abridgement of a 201-line
  document.** Missing: the platform-mechanism comparison, **every rule §3.1–§3.7**, and the
  mechanical-defence table — **including the two sections `sensor_model_attribution.py` names as
  its own rule source.** ⚠️ **Both editions' sensors ran green throughout**: nothing in the
  framework compares the two editions, and a reference sensor can only say "the file you cited
  exists", ⛔ never "this edition is missing three sections". The editions are now equivalent
  section for section.
- **Chinese edition, same file:** two different sections were both numbered `3.6` — **and the
  sensor's citation pointed at the second one**; `§3.7` sat after `§4` and `§5`; the tier line
  still used a superseded scheme. Merged, reordered, and renumbered to `3.6.1`–`3.6.3`
  ⛔ **without changing the number anything cites.**
- **Three dangling constitution citations** (`§5.11` in both editions' `sensor_model_attribution.py`,
  `§8.1` in both editions' `Audit_Protocol.md`, `§5.8` in the Chinese `MODEL_IDENTITY.md`).
  🔴 **The `§5.11` one was a defect description that instantiated the defect it described** —
  two lines above it, the same comment explains why the filenames were deliberately *not*
  written out.
- **`SENSOR_CHANGELOG.md` carried two `#n` series in one namespace** (undated pre-history and
  dated maintenance), so `#1` meant two different things. ⛔ **Not renumbered** — the file is
  append-only. Divider headings and a citation rule were added instead: cite a maintenance
  entry with its date.

### Removed / 移除

- **`enable_reference_authenticity` and `enable_bat_checks`** config keys — ⛔ nothing in the
  project ever read them. **A switch that looks like it turns something on, and does not.**
  **⛔ 全專案沒有任何程式讀過它們——看起來有一個功能可以打開，其實打開了不會發生任何事。**

### ⚠️ Upgrade notes / 升級注意

- If you carry a `governance_config.json`, drop `enable_reference_authenticity` and
  `enable_bat_checks`; add `synced_lists` / `sync_scan_globs` if you want the new clause-sync
  sensor to do anything. Absent keys fall back to the defaults.
- **Exit code 2 now happens where it used to be 0.** That is deliberate: incomplete is not a
  pass. Constitution §4.1.1 says what to do with it.
- ⛔ **Rule IDs are permanent and append-only.** `R-01`–`R-32` are unchanged; nothing was
  renumbered.

### ⛔ What this release does not claim / 這一版不宣稱什麼

- Links ⑥ and ⑦ of the evidence chain — *does the passage support the claim*, and *may you
  generalise* — remain **deliberately unmechanised**. Green covers only what is mechanised.
- Cross-model adversarial audit is still untested by anything other than a human.
- ⛔ **Short-form section citations are not mechanised.** The sensor resolves the
  `` `file.md` §N `` form; **the shorter "constitution §N" form used in 68 places (Chinese) and
  58 (English) is checked by nobody.** The three dangling citations fixed in this release were
  found by hand, ⛔ not by a sensor. **Until that is mechanised, "green" does not cover them.**
- ⛔ **Nothing compares the two editions.** The equivalence stated above was established by a
  one-off comparison of heading structure, section numbers and language-neutral code tokens —
  ⚠️ **not of meaning, and ⛔ not by anything that will run again.**
- ⚠️ **One true positive is known and open**: a duplicated sentence between
  `Incident_Log.md` and `RULES.md`, where the right fix depends on an unresolved question —
  whether a rule may cite an incident-log case number at all, given that each downstream
  project's incident log is its own and does not inherit. **A citation that silently retargets
  is worse than one that dangles, because it stays green.**
  It is reported as WARN rather than hidden. **A known open finding is not a bug fixed.**

---

## [1.0.0] — 2026-08-12

Initial public release: bilingual file-based governance framework, two independent editions,
two ledgers, five sensors, twelve paired self-tests.
首次公開釋出：雙語檔案化治理框架，兩個獨立版本、兩本台帳、五支感測器、十二組成對自測。

[1.4.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.4.0
[1.3.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.3.0
[1.2.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.2.0
[1.0.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.0.0
