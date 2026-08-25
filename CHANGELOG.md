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

[1.2.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.2.0
[1.0.0]: https://github.com/yama-learns/Spark2Groundwork/releases/tag/v1.0.0
