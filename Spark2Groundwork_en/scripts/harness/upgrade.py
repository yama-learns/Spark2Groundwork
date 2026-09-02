#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升級工具 —— **框架資料夾可以整包換掉，你的資料不會被碰到**

三個步驟，⛔ 每一步都停下來等你決定：

    check    我這一版是什麼？GitHub 上最新的是什麼？
    diff     `_upgrade/` 裡的新版，跟我現在的差在哪？
    apply    把其中**一個**資料夾換掉（⛔ 換之前強制建立檢查點與持久收據）
    receipts 列出升級與復原留下的持久收據
    receipt-diff  以收據查看升級前後差異
    restore       從收據安全取回一個檔案

⛔ **本工具不會下載任何東西，也不會自動覆蓋。**
下載由你做（`git clone` 或在 GitHub 上按 Download ZIP），放進 `_upgrade/`。

⚠️ **為什麼不做成一鍵自動：覆蓋是不可逆的。**
**不可逆的操作只隔一個按鈕，遲早會被誤按。**

退出碼：0 正常｜1 前置條件不成立｜2 我沒能查／沒能做
"""
import argparse
import datetime
import difflib
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ Output encoding must be pinned to UTF-8 first, ⛔ or Windows dies at the
#    first symbol printed. Single home: `_common._force_utf8` (see the case there).
from _common import _force_utf8                            # noqa: E402
_force_utf8()

MSG = {
 "title": "  Framework upgrade (⛔ framework only; your data is never touched)",
 "usage": """Usage:
  python3 scripts/harness/upgrade.py check         what version am I on? what is latest?
  python3 scripts/harness/upgrade.py diff          what differs in `_upgrade/`?
  python3 scripts/harness/upgrade.py apply <name>  replace one of them
  python3 scripts/harness/upgrade.py receipts      list durable upgrade restore receipts
  python3 scripts/harness/upgrade.py receipt-diff <receipt> [path]
  python3 scripts/harness/upgrade.py restore <receipt> <path>

⛔ This tool never downloads and never overwrites on its own.
Download it yourself and put it in `_upgrade/`.""",
 "wrong_folder": "[FAIL] Not the project root (no governance/AGENTS.md). Current location: {root}",
 "check_head": "Your current versions:",
 "check_row": "  {d:<12} {v}",
 "check_marker_warning": "⚠️ A version marker says what a folder calls itself; it does ⛔ not prove the contents are complete. Use diff to inspect actual contents.",
 "unknown": "(no version marker)",
 "latest": "Latest release on GitHub: {tag}",
 "check_offline": """[INCOMPLETE] Could not reach GitHub to read the latest version ({err}).
       ⚠️ **This does not mean you are up to date** — it means this check did not run.
       -> Possibly no network, or a firewall. Check by hand:
         https://github.com/yama-learns/Spark2Groundwork/releases""",
 "check_tail": """Next: download the new version into `_upgrade/`, then run `upgrade.py diff`.
⛔ Only the items listed above are replaced. **Everything else is left alone,
including folders you created yourself.**""",
 "no_upgrade_dir": """[FAIL] No `_upgrade/` folder found.
       -> Download and unpack the new version into `_upgrade/` inside this project, then re-run.""",
 "diff_none": "What is in `_upgrade/` is identical to what you have — ⛔ nothing to replace.",
 "diff_head": "These framework items differ from yours:",
 "diff_row": "  {name:<20} {m} file(s) changed | {n} new | {o} target-only",
 "target_only_row": "      ⛔ {path}",
 "diff_tail": """To replace one: `upgrade.py apply <name>`
⚠️ **One at a time.** ⛔ There is no "replace everything" option —
**it would leave you unable to tell which package caused a problem.**

If the list above includes `prompts/TEMPLATE_decompose.txt`, first move it to project root
and rename it `FIRST_IDEA.md`. Move self-written tools under `scripts/` to `my/tools/`.""",
 "never": """[FAIL] "{t}" is **your data**; ⛔ the upgrade tool never touches it.
       (Constitution §6.3: that class can be restored from nowhere.)""",
 "not_framework": "[FAIL] \"{t}\" is not a replaceable framework item. Replaceable: {ok}",
 "retired_target": """[FAIL] "{t}" retired in {v}; its contents were folded into `{into}/` — ⛔ the upgrader no longer replaces it.
       ⚠️ **The folder in your project has ⛔ not been deleted.** Once you have checked that `{into}/` holds what you need, it is yours to delete.""",
 "missing_in_upgrade": "[FAIL] `_upgrade/` does not contain \"{t}\". Source: {src}",
 "target_only_block": """[FAIL] "{t}" contains files absent from the new source. ⛔ **No checkpoint was made and nothing was replaced.**
       They may belong to this project. Move each one outside the wholesale-replacement area, then re-run:""",
 "retired_head": """
⚠️ **These folders have retired, ⛔ and the upgrader ⛔ does not delete your files:**""",
 "retired_row": "      ⛔ `{d}/` (folded into `{into}/` in {v}) — **the contents are already in `{into}/`; once you have checked, this folder is yours to delete**",
 "cp_first": "Making a checkpoint before overwriting (⛔ if this fails, nothing is overwritten)...\n",
 "cp_failed": """
[FAIL] No checkpoint was made (exit {rc}) — ⛔ **nothing was overwritten.**
       ⚠️ Fix the checkpoint problem first, then come back. If the download is
          incomplete or mismatched, download the full package in the same edition and version.""",
 "checkpoint_peer_missing": """[FAIL] No `checkpoint.py` compatible with this upgrader's tool mode was found.
       ⛔ No checkpoint or receipt was created, and no project file was written.
       -> Download the complete package in the same edition and version, keeping
          `upgrade.py` beside its `checkpoint.py`.""",
 "applied": "\n  ✅ Replaced: {t}",
 "no_receipt": """
[FAIL] The checkpoint was made, ⛔ **but I could not read back its commit id (exit {rc}) —
       nothing was overwritten.**
       🔴 **Reason: that id is your only entry point for recovering hand edits later.**
       **⛔ An overwrite that "saved a restore point but cannot say where it is" has no
       restore point at all.**
       -> Run `git status`, deal with what it shows, then come back and upgrade.""",
 "receipt_unprotected": """
[FAIL] The checkpoint exists, ⛔ **but these files are not recoverable from it under Git semantics:**
{paths}
       Nothing was overwritten. A commit id alone is not a restore receipt.
       -> Make sure the files are tracked by Git and not hidden by ignore/assume-unchanged rules,
          then run the upgrade again.""",
 "receipt_create_failed": """
[FAIL] The checkpoint exists, ⛔ **but a durable upgrade receipt could not be created:** {err}
       Nothing was overwritten. The checkpoint commit is still present.""",
 "receipt": """
🔴 **Project-local durable restore receipt created before this upgrade:**
      receipt: {rid}
      commit:  {cp}
      target:  {target}
  Every existing non-transient file that this replacement will overwrite was verified
  against the checkpoint using Git's own content semantics. The receipt is pinned by a
  private Git ref in this project and is listed by `upgrade.py receipts`.
  ⚠️ It is not carried to another repository by an ordinary `git clone` or file backup.""",
 "applied_tail": """
Next:
  1. Press the review-changes button to see what this package changed
  2. Run `python3 scripts/harness/run_all_sensors.py` and confirm it is still green
  3. 🔴 **Run `python3 scripts/harness/tool_my_index.py` to regenerate your file index**
     ⚠️ The upgrade touched framework files, so the index is now stale — ⛔ without this
     you will see MY_INDEX_STALE on the next round
  4. ⚠️ **If this package contained hand edits, wholesale replacement has moved them out
     of the working copy.** The review-changes button cannot see that pre-image because its
     baseline is `reviewed`, and an automatic tool must never move that human-review tag.
     **With a complete, matching v1.4.4 package, use the built-in receipt interface —
     no raw Git command is needed:**
       list receipts:       python3 scripts/harness/upgrade.py receipts
       see one difference:  python3 scripts/harness/upgrade.py receipt-diff {rid} <path/to/file>
       restore one file:    python3 scripts/harness/upgrade.py restore {rid} <path/to/file>
  5. ⚠️ **If the framework added working rules, `my/MY_RULES.md` is now short a few** —
     run `python3 scripts/harness/tool_sync_my_rules.py` to copy them in verbatim\n  6. ⚠️ **If the framework revised an existing rule, your copy in `my/MY_RULES.md`\n     stays on the old wording** — the tool prints a line-by-line difference ⛔ **and\n     writes nothing for you**: paste the `+` lines verbatim into that rule's body.\n     ⛔ **It never touches a rule you marked as an override**""",
 "apply_needs_target": "[FAIL] Say which one, e.g.: upgrade.py apply governance",
 "receipts_empty": "No durable upgrade receipts exist in this project yet.",
 "receipts_head": "Durable upgrade restore receipts (newest first):",
 "receipts_row": "  {rid}  {created}  {operation:<14}  {target}",
 "receipts_bad": "  [WARN] Ignored an unreadable receipt file: {name} ({err})",
 "receipt_needs_id": "[FAIL] Give a receipt id (or `latest`). Run `upgrade.py receipts` to list them.",
 "receipt_unknown": "[FAIL] No valid receipt named `{rid}` was found. Run `upgrade.py receipts`.",
 "receipt_invalid": "[FAIL] Receipt `{rid}` failed integrity checks: {err}",
 "receipt_path_bad": "[FAIL] `{path}` is outside this receipt's target `{target}`.",
 "receipt_path_not_saved": "[FAIL] `{path}` has no pre-upgrade file in receipt `{rid}`.",
 "receipt_diff_head": "Changes since receipt `{rid}` for `{path}`:",
 "receipt_no_diff": "  (no tracked-content difference from this receipt)",
 "receipt_new_head": "  Current paths that did not exist in the receipt:",
 "receipt_new_row": "      + {path}",
 "restore_needs_path": "[FAIL] Give exactly one file path from the receipt to restore.",
 "restore_current_missing": "[FAIL] `{path}` is missing or is not a regular file now. Nothing was restored because an undo receipt could not be made.",
 "restore_noop": "`{path}` already matches receipt `{rid}`; nothing was changed.",
 "restore_cp_first": "Making an undo checkpoint before restoring this file...",
 "restore_cp_failed": """[FAIL] The undo checkpoint failed (exit {rc}); nothing was restored.
       If the download is incomplete or mismatched, download the full package in the same edition and version.""",
 "edition_guard_failed": """[FAIL] The upgrade source and current project could not be proved to use the same edition.
       Upgrade source: {source}; current project: {project}.
       ⛔ No checkpoint or receipt was created, and no file was replaced.
       ⚠️ The decision reads only the twelve framework launcher names below, ⛔ not who
          put them there. What was actually found:
            upgrade source: {src_found}
            current project: {root_found}
       -> Use a complete package in the same language. Its three English or Chinese
          launchers must form a complete Windows (.bat), macOS (.command), or dual-platform set;
          missing or mixed sets are rejected.
       🔴 -> If one of the files above is ⛔ not the framework's and merely shares the name,
          that is the cause: rename it (or move it under `my/`) and run again.""",
 "edition_found_none": "⛔ none (⇒ that is the result of a scan, not the absence of one)",
 "edition_found_item": "{name}[{tag}]",
 "edition_found_join": ", ",
 "edition_tag_zh": "zh",
 "edition_tag_en": "en",
 "restore_receipt_failed": "[FAIL] The undo checkpoint exists, but its durable receipt failed: {err}. Nothing was restored.",
 "restore_git_failed": "[FAIL] Git could not restore `{path}` (exit {rc}). The undo receipt is `{undo}`.",
 "restore_verify_failed": "[FAIL] `{path}` was written, but read-back did not match receipt `{rid}`. Use undo receipt `{undo}` and stop.",
 "restore_done": "✅ Restored `{path}` from `{rid}` without moving `reviewed`. Undo receipt: `{undo}`",
}


# 🔴 **可整包替換的框架項目。這兩份清單就是保護機制本身。**
#    ⛔ **不在這兩份清單上的任何東西，一律不會被替換**——
#    **包含使用者自己開的資料夾（筆記、圖表、投稿版本……），⛔ 那些名字不可能事先列舉。**
#    ⚠️ 成對樣本見 `run_selftest.py` 的 `upgrade_case()`：
#    **拿一個工具沒聽過的資料夾當目標，必須被拒絕，且內容原封不動。**
# ⚠️ **v1.4.1 added `docs` and the six launchers.**
#    🔴 **They have always been the framework's, ⛔ and they were not on the replaceable
#    list — meaning the seven figure-layout fixes made in v1.3.0 ⛔ reach no existing project.**
#    ⚠️ **This was caught by `tool_my_index.py` on its very first run: it lists everything the
#    framework does ⛔ not own, and `docs/` and the six buttons appeared in that list.**
FRAMEWORK_DIRS = ("governance", "profiles", "prompts", "scripts", "docs")
# 🔴 **Retired packages: they used to be on the replaceable list and are not any more.**
#    ⚠️ **Why this list is needed: a folder taken out of `FRAMEWORK_DIRS` becomes an orphan
#    in an existing project — ⛔ its contents stay frozen at the version it retired in, and
#    ⛔ nothing will ever touch it again.**
#    🔴 **⛔ The upgrader does not delete your files (constitution §6.3), ⚠️ but it must say
#    so** — **⛔ an orphan folder nobody knows about is exactly a stale framework document.**
#    Format: `dirname: (retired in, where the contents went)`.
RETIRED_DIRS = {"policy": ("v1.4.4", "governance")}
FRAMEWORK_FILES = ("README.md", "SETUP.md", "INITIALIZE_PROMPT.md", "file_index.md",
                   "check_update.bat", "check_update.command",
                   "review_changes.bat", "review_changes.command",
                   "snapshot.bat", "snapshot.command")
# 🔴 **`.gitignore` and `.gitattributes` are deliberately ⛔ absent above.**
#    ⚠️ **They have mixed ownership: the framework supplies defaults, ⛔ and users add their
#    own rules.** **⇒ Per constitution §6.4, replacing them wholesale would delete those lines.**
#    ⛔ **Known cost: later changes to the framework's default ignore rules ⛔ do not reach
#    existing projects. ⚠️ Written down here rather than left blank.**
# ⚠️ **這一份⛔ 不是保護機制。** 保護機制是上面那兩份「可替換清單」。
#    **本清單唯一的用途，是在使用者不小心把常見的自有資料當成升級目標時，
#    給他一句看得懂的錯誤訊息**，而不是通用的「這不是可替換項目」。
#    ⛔ **不要把它改成主要防線**——**那會讓沒列在這裡的資料夾看起來像是不受保護的。**
NEVER_TOUCH = ("PROJECT.md", "FIRST_IDEA.md", "ledgers", "corpus", "corpus_md", "handoffs",
               "my", "NEXT_SESSION_MEMO.md", "governance_config.json")
VERSION_FILE = "_VERSION"
TRANSIENT_NAMES = {".DS_Store", "Thumbs.db"}
TRANSIENT_SUFFIXES = {".pyc", ".pyo"}
# Only this exact package-relative path is framework-generated state.
# ⛔ A name-only exemption would silently discard a project-owned namesake anywhere else.
TRANSIENT_PACKAGE_PATHS = {("scripts", "harness/harness_status.json")}

RECEIPT_SCHEMA = 1
RECEIPT_REF_PREFIX = "refs/spark2groundwork/restore"
RECEIPT_GIT_PATH = "spark2groundwork/receipts"
RECEIPT_ID_RE = re.compile(r"^upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]{0,39}-[0-9a-f]{8}$")
CHECKPOINT_TOOL_API = "spark2groundwork-checkpoint-tool-v1"
EDITION_LAUNCHERS = {
    "zh": {
        "bat": ("查看變更.bat", "檢查更新.bat", "記錄快照.bat"),
        "command": ("查看變更.command", "檢查更新.command", "記錄快照.command"),
    },
    "en": {
        "bat": ("review_changes.bat", "check_update.bat", "snapshot.bat"),
        "command": ("review_changes.command", "check_update.command", "snapshot.command"),
    },
}


class ReceiptError(RuntimeError):
    """A durable receipt could not be created or did not pass integrity checks."""


class PreimageError(ReceiptError):
    """One or more files about to be overwritten are absent from the checkpoint."""

    def __init__(self, paths):
        self.paths = sorted(set(paths))
        super().__init__(", ".join(self.paths))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def _git(root, args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _checkpoint_program(root):
    """Select a compatible peer without executing candidates during the probe."""
    candidates = (pathlib.Path(__file__).resolve().with_name("checkpoint.py"),
                  root / "scripts/harness/checkpoint.py")
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not candidate.is_file():
            continue
        seen.add(resolved)
        try:
            if CHECKPOINT_TOOL_API in candidate.read_text(encoding="utf-8", errors="replace"):
                return candidate
        except OSError:
            continue
    return None


def _edition_fingerprint(root):
    """Return one proven edition, or a fail-closed diagnostic state."""
    present = {}
    complete = {}
    for edition, layouts in EDITION_LAUNCHERS.items():
        known = tuple(name for names in layouts.values() for name in names)
        present[edition] = any((root / name).is_file() for name in known)
        complete[edition] = any(all((root / name).is_file() for name in names)
                                for names in layouts.values())
    seen = [edition for edition, yes in present.items() if yes]
    proven = [edition for edition, yes in complete.items() if yes]
    if len(seen) > 1:
        return None, "mixed"
    if len(proven) == 1 and seen == proven:
        return proven[0], proven[0]
    return None, "missing/incomplete"


def _edition_launchers_found(root):
    """⛔ For the failure message only: which framework launchers this directory
    actually shows, and which edition each belongs to.

    ⚠️ **It takes ⛔ no part in the decision** — that stays in `_edition_fingerprint`.
    🔴 **⇒ Why they are separate: changing how a refusal explains itself must ⛔ not
    change what it decides.**
    ⚠️ Order follows `EDITION_LAUNCHERS`, so both platforms print the same list.

    **Triggering case (pre-release review, 2026-09-03):** a legitimate Chinese project
    owning a file called `snapshot.bat` read as `mixed` and the whole upgrade was
    refused, while the message only said the edition could not be proved and asked for
    a fresh download — **⚠️ and the download was never the cause.**
    """
    found = []
    for edition, layouts in EDITION_LAUNCHERS.items():
        for names in layouts.values():
            for name in names:
                if (root / name).is_file():
                    found.append((name, edition))
    return found


def _edition_found_text(root, MSG):
    found = _edition_launchers_found(root)
    if not found:
        return MSG["edition_found_none"]
    return MSG["edition_found_join"].join(
        MSG["edition_found_item"].format(name=name, tag=MSG["edition_tag_" + edition])
        for name, edition in found)


def _same_edition(root, src, MSG):
    project_edition, project_state = _edition_fingerprint(root)
    source_edition, source_state = _edition_fingerprint(src)
    if project_edition and project_edition == source_edition:
        return True
    print(MSG["edition_guard_failed"].format(
        source=source_state, project=project_state,
        src_found=_edition_found_text(src, MSG),
        root_found=_edition_found_text(root, MSG)))
    return False


def _git_input(root, args, value):
    # Binary stdin avoids Windows text-mode LF->CRLF translation. `git mktag`
    # strictly rejects CR bytes in object headers.
    p = subprocess.run(["git", "-C", str(root), *args], input=value.encode("utf-8"),
                       capture_output=True)
    p.stdout = (p.stdout or b"").decode("utf-8", errors="replace")
    p.stderr = (p.stderr or b"").decode("utf-8", errors="replace")
    return p


def _safe_rel(value):
    """Return a canonical repository-relative POSIX path, or reject it."""
    raw = str(value).replace("\\", "/")
    p = pathlib.PurePosixPath(raw)
    if (not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw)
            or any(ord(char) < 32 for char in raw)
            or any(part in ("", ".", "..") for part in p.parts)
            or raw != p.as_posix()):
        raise ReceiptError(f"unsafe repository-relative path: {value!r}")
    return p.as_posix()


def _under_target(path, target):
    return path == target or path.startswith(target.rstrip("/") + "/")


def _is_transient(package, rel, path=None):
    parts = pathlib.PurePosixPath(rel).parts
    name = parts[-1] if parts else ""
    suffix = pathlib.PurePosixPath(name).suffix
    return ("__pycache__" in parts or name in TRANSIENT_NAMES
            or suffix in TRANSIENT_SUFFIXES
            or (package, rel) in TRANSIENT_PACKAGE_PATHS)


def _receipt_store(root, create=False):
    p = _git(root, ["rev-parse", "--git-path", RECEIPT_GIT_PATH])
    if p.returncode != 0 or not (p.stdout or "").strip():
        raise ReceiptError((p.stderr or p.stdout or "cannot locate Git receipt store").strip())
    store = pathlib.Path(p.stdout.strip())
    if not store.is_absolute():
        store = root / store
    store = store.resolve()
    if create:
        store.mkdir(parents=True, exist_ok=True)
    return store


def _tree_entry(root, commit, rel):
    p = _git(root, ["ls-tree", "-z", commit, "--", rel])
    if p.returncode != 0:
        raise ReceiptError((p.stderr or "git ls-tree failed").strip())
    raw = p.stdout.rstrip("\0")
    if not raw:
        return None
    first = raw.split("\0", 1)[0]
    try:
        meta, found = first.split("\t", 1)
        mode, kind, blob = meta.split(" ", 2)
    except ValueError as e:
        raise ReceiptError(f"unreadable tree entry for {rel}") from e
    if found != rel:
        raise ReceiptError(f"tree path mismatch for {rel}")
    return {"mode": mode, "type": kind, "blob": blob}


def _index_entry(root, rel):
    p = _git(root, ["ls-files", "--stage", "-z", "--", rel])
    if p.returncode != 0:
        raise ReceiptError((p.stderr or "git ls-files failed").strip())
    rows = [row for row in p.stdout.split("\0") if row]
    if len(rows) != 1:
        return None
    try:
        meta, found = rows[0].split("\t", 1)
        mode, blob, stage = meta.split(" ", 2)
    except ValueError as e:
        raise ReceiptError(f"unreadable index entry for {rel}") from e
    if found != rel or stage != "0":
        return None
    return {"mode": mode, "blob": blob}


def _hash_worktree(root, path, rel):
    p = _git(root, ["hash-object", f"--path={rel}", "--", str(path)])
    if p.returncode != 0 or not (p.stdout or "").strip():
        raise ReceiptError((p.stderr or f"cannot hash {rel}").strip())
    return p.stdout.strip()


def _worktree_mode(root, path, checkpoint_mode):
    if path.is_symlink() or not path.is_file():
        return None
    # On Windows, or when core.filemode is false, executable bits are outside Git's
    # working-tree semantics. On POSIX with core.filemode enabled they must agree.
    p = _git(root, ["config", "--bool", "core.filemode"])
    filemode = p.returncode == 0 and (p.stdout or "").strip().lower() == "true"
    if os.name != "nt" and filemode:
        return "100755" if os.access(path, os.X_OK) else "100644"
    return checkpoint_mode


def _verified_entries(root, commit, paths):
    entries = []
    bad = []
    for rel in sorted(set(paths)):
        try:
            rel = _safe_rel(rel)
            path = root / pathlib.PurePosixPath(rel)
            if path.is_symlink() or not path.is_file():
                bad.append(rel)
                continue
            tracked = _git(root, ["ls-files", "--error-unmatch", "--", rel])
            tree = _tree_entry(root, commit, rel)
            index = _index_entry(root, rel)
            if (tracked.returncode != 0 or tree is None or tree["type"] != "blob"
                    or tree["mode"] not in ("100644", "100755") or index is None
                    or index["mode"] != tree["mode"] or index["blob"] != tree["blob"]
                    or _hash_worktree(root, path, rel) != tree["blob"]
                    or _worktree_mode(root, path, tree["mode"]) != tree["mode"]):
                bad.append(rel)
                continue
            entries.append({"path": rel, "blob": tree["blob"], "mode": tree["mode"]})
        except (OSError, ReceiptError):
            bad.append(rel)
    if bad:
        raise PreimageError(bad)
    return entries


def _preimage_paths(root, dst, source, target):
    """Return existing files that replacement will overwrite and transient omissions."""
    target = _safe_rel(target)
    if source.is_symlink() or (not source.is_file() and not source.is_dir()):
        raise PreimageError([target])
    if dst.is_symlink():
        raise PreimageError([target])
    if source.is_file():
        if dst.exists() and not dst.is_file():
            raise PreimageError([target])
        return ([target] if dst.is_file() else []), []
    if dst.exists() and not dst.is_dir():
        raise PreimageError([target])

    paths = []
    omitted = []
    if dst.is_dir():
        for p in sorted(dst.rglob("*"), key=lambda value: value.as_posix()):
            rel = p.relative_to(dst).as_posix()
            full_rel = f"{target}/{rel}"
            if _is_transient(target, rel, p):
                if p.is_file() or p.is_symlink():
                    omitted.append(full_rel)
                continue
            if p.is_symlink() or (not p.is_file() and not p.is_dir()):
                raise PreimageError([full_rel])
    for p in sorted(source.rglob("*"), key=lambda value: value.as_posix()):
        rel = p.relative_to(source).as_posix()
        full_rel = f"{target}/{rel}"
        if _is_transient(target, rel, p):
            continue
        if p.is_symlink() or (not p.is_file() and not p.is_dir()):
            raise PreimageError([full_rel])
        old = dst / pathlib.PurePosixPath(rel)
        if p.is_file() and old.exists():
            if old.is_symlink() or not old.is_file():
                raise PreimageError([full_rel])
            paths.append(full_rel)
        elif p.is_dir() and old.exists() and not old.is_dir():
            raise PreimageError([full_rel])
    return paths, sorted(set(omitted))


def _atomic_json(path, data):
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".receipt-",
                                         suffix=".tmp", delete=False) as f:
            tmp_name = f.name
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except OSError as e:
        if tmp_name:
            try:
                pathlib.Path(tmp_name).unlink()
            except OSError:
                pass
        raise ReceiptError(str(e)) from e


def _load_receipt(root, rid):
    if not RECEIPT_ID_RE.fullmatch(rid or ""):
        raise ReceiptError("invalid receipt id")
    expected_ref = f"{RECEIPT_REF_PREFIX}/{rid}"
    tagged = _git(root, ["cat-file", "-p", expected_ref])
    if tagged.returncode != 0:
        raise ReceiptError("durable ref is missing")
    try:
        header, message = tagged.stdout.split("\n\n", 1)
        tag_fields = dict(line.split(" ", 1) for line in header.splitlines()
                          if " " in line and not line.startswith("tagger "))
        authoritative = json.loads(message)
    except (ValueError, TypeError) as e:
        raise ReceiptError("private ref does not contain a receipt tag") from e
    if tag_fields.get("type") != "commit":
        raise ReceiptError("receipt tag does not point to a commit")
    path = _receipt_store(root) / f"{rid}.json"
    if path.exists():
        try:
            mirror = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise ReceiptError(str(e)) from e
        if mirror != authoritative:
            raise ReceiptError("manifest mirror differs from the Git-pinned receipt")
    data = authoritative
    if data.get("schema") != RECEIPT_SCHEMA or data.get("receipt_id") != rid:
        raise ReceiptError("schema or receipt id mismatch")
    ref = data.get("ref")
    commit = data.get("commit")
    if ref != expected_ref or not isinstance(commit, str):
        raise ReceiptError("invalid receipt ref or commit")
    if tag_fields.get("object") != commit:
        raise ReceiptError("receipt tag object and manifest commit differ")
    resolved = _git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if resolved.returncode != 0 or resolved.stdout.strip() != commit:
        raise ReceiptError("durable ref is missing or no longer matches")
    target = _safe_rel(data.get("target", ""))
    files = data.get("files")
    if not isinstance(files, list):
        raise ReceiptError("files is not a list")
    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ReceiptError("invalid file entry")
        rel = _safe_rel(entry.get("path", ""))
        if rel in seen or not _under_target(rel, target):
            raise ReceiptError(f"invalid or duplicate receipt path: {rel}")
        seen.add(rel)
        tree = _tree_entry(root, commit, rel)
        if (tree is None or tree["type"] != "blob"
                or entry.get("mode") != tree["mode"]
                or entry.get("blob") != tree["blob"]):
            raise ReceiptError(f"checkpoint tree mismatch: {rel}")
    omitted = data.get("omitted_transient", [])
    if not isinstance(omitted, list):
        raise ReceiptError("omitted_transient is not a list")
    for rel in omitted:
        rel = _safe_rel(rel)
        if not _under_target(rel, target):
            raise ReceiptError(f"transient path is outside target: {rel}")
        inner = rel[len(target):].lstrip("/")
        if not inner or not _is_transient(target, inner):
            raise ReceiptError(f"path is not an allowed transient: {rel}")
    return data


def _create_receipt(root, commit, target, paths, omitted, operation, target_existed):
    target = _safe_rel(target)
    entries = _verified_entries(root, commit, paths)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-")[:40] or "target"
    rid = f"upg-{stamp}-{slug}-{uuid.uuid4().hex[:8]}"
    ref = f"{RECEIPT_REF_PREFIX}/{rid}"
    reviewed = _git(root, ["rev-parse", "--verify", "refs/tags/reviewed^{commit}"])
    data = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": rid,
        "created_utc": now.isoformat().replace("+00:00", "Z"),
        "operation": operation,
        "target": target,
        "target_existed": bool(target_existed),
        "commit": commit,
        "ref": ref,
        "reviewed_before": reviewed.stdout.strip() if reviewed.returncode == 0 else None,
        "files": entries,
        "omitted_transient": sorted(set(_safe_rel(p) for p in omitted)),
    }
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    tag_text = (f"object {commit}\ntype commit\ntag {rid}\n"
                f"tagger Spark2Groundwork <receipt@local> {int(now.timestamp())} +0000\n\n"
                f"{canonical}\n")
    made_tag = _git_input(root, ["mktag"], tag_text)
    tag_oid = (made_tag.stdout or "").strip()
    if made_tag.returncode != 0 or not tag_oid:
        raise ReceiptError((made_tag.stderr or "could not pin receipt manifest").strip())
    made_ref = _git(root, ["update-ref", ref, tag_oid, ""])
    if made_ref.returncode != 0:
        raise ReceiptError((made_ref.stderr or "could not create durable ref").strip())
    path = None
    try:
        store = _receipt_store(root, create=True)
        path = store / f"{rid}.json"
        if path.exists():
            raise ReceiptError("receipt manifest already exists")
        _atomic_json(path, data)
        checked = _load_receipt(root, rid)
        if checked.get("receipt_id") != rid:
            raise ReceiptError("receipt read-back failed")
    except Exception as e:  # noqa: BLE001 -- rollback must cover filesystem failures too
        if path is not None and path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        _git(root, ["update-ref", "-d", ref, tag_oid])
        if isinstance(e, ReceiptError):
            raise
        raise ReceiptError(str(e)) from e
    return data


def _receipt_files(data):
    return {entry["path"]: entry for entry in data["files"]}


def _receipt_rows(root):
    try:
        store = _receipt_store(root)
    except ReceiptError:
        return [], []
    good, bad = [], []
    ids = set()
    if store.is_dir():
        for path in sorted(store.glob("*.json"), key=lambda value: value.as_posix()):
            if RECEIPT_ID_RE.fullmatch(path.stem):
                ids.add(path.stem)
            else:
                bad.append((path.name, "invalid receipt id"))
    refs = _git(root, ["for-each-ref", "--format=%(refname)", RECEIPT_REF_PREFIX + "/"])
    if refs.returncode == 0:
        for ref in refs.stdout.splitlines():
            rid = ref[len(RECEIPT_REF_PREFIX) + 1:] if ref.startswith(RECEIPT_REF_PREFIX + "/") else ""
            if RECEIPT_ID_RE.fullmatch(rid):
                ids.add(rid)
            else:
                bad.append((ref or "(empty ref)", "invalid receipt ref name"))
    for rid in sorted(ids):
        try:
            good.append(_load_receipt(root, rid))
        except ReceiptError as e:
            bad.append((f"{rid}.json", str(e)))
    good.sort(key=lambda row: (row.get("created_utc", ""), row["receipt_id"]), reverse=True)
    return good, bad


def _resolve_receipt(root, token):
    if token == "latest":
        rows, _ = _receipt_rows(root)
        return rows[0] if rows else None
    if not RECEIPT_ID_RE.fullmatch(token or ""):
        return None
    path = _receipt_store(root) / f"{token}.json"
    exists = _git(root, ["show-ref", "--verify", "--quiet",
                         f"{RECEIPT_REF_PREFIX}/{token}"])
    if exists.returncode != 0 and not path.is_file():
        return None
    return _load_receipt(root, token)


def _worktree_matches(root, entry):
    rel = entry["path"]
    path = root / pathlib.PurePosixPath(rel)
    if path.is_symlink() or not path.is_file():
        return False
    try:
        return (_hash_worktree(root, path, rel) == entry["blob"]
                and _worktree_mode(root, path, entry["mode"]) == entry["mode"])
    except ReceiptError:
        return False


def read_version(p):
    """只取第一個非註解、非空的行。

    ⚠️ 首版直接 `.strip()` 整個檔案，**於是把說明註解一起當成版本號印出來**——
    ⛔ 一個把三行註解顯示成「版本」的畫面，讀者無法判斷自己是哪一版。
    """
    if not p.is_file():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return None


def local_versions(root):
    return {d: read_version(root / d / VERSION_FILE) for d in FRAMEWORK_DIRS}


def cmd_check(root, MSG):
    print(MSG["check_head"])
    for d, v in local_versions(root).items():
        print(MSG["check_row"].format(d=d, v=v or MSG["unknown"]))
    print(MSG["check_marker_warning"])
    print()
    try:
        import urllib.request, json
        url = "https://api.github.com/repos/yama-learns/Spark2Groundwork/releases/latest"
        with urllib.request.urlopen(url, timeout=10) as r:
            tag = json.load(r).get("tag_name", "")
        print(MSG["latest"].format(tag=tag or MSG["unknown"]))
    except Exception as e:                                  # noqa: BLE001
        # ⛔ 查不到就說查不到。**「查不到」與「已是最新」⛔ 不得共用一個輸出。**
        print(MSG["check_offline"].format(err=type(e).__name__))
        return 2
    print_retired(root, MSG)
    print(MSG["check_tail"])
    return 0



def retired_present(root):
    """Return the retired folders that still exist in this project.

    ⚠️ **The criterion is "the folder exists", ⛔ not "it has anything in it"** —
    🔴 **an empty orphan still reads as a folder the framework maintains.**
    """
    return [(d, v, into) for d, (v, into) in sorted(RETIRED_DIRS.items())
            if (root / d).is_dir()]


def print_retired(root, MSG):
    """⛔ Both `check` and `diff` must print this. ⚠️ Printing it on only one route
    leaves the other one silent."""
    rows = retired_present(root)
    if not rows:
        return
    print(MSG["retired_head"])
    for d, v, into in rows:
        print(MSG["retired_row"].format(d=d, v=v, into=into))
    print()

def pairs(root, src):
    for d in FRAMEWORK_DIRS:
        if (src / d).is_dir():
            yield d, root / d, src / d
    for f in FRAMEWORK_FILES:
        if (src / f).is_file():
            suffix = pathlib.PurePosixPath(f).suffix
            native = ".bat" if sys.platform == "win32" else (".command" if sys.platform == "darwin" else None)
            # Routine diff omits an absent foreign-platform launcher. Explicit apply still
            # deliberately accepts its exact FRAMEWORK_FILES name for cross-platform packaging.
            if suffix in (".bat", ".command") and not (root / f).exists() and suffix != native:
                continue
            yield f, root / f, src / f


def target_only_files(cur, new, package):
    """List non-transient entries wholesale replacement would delete or change type."""
    if not cur.is_dir() or not new.is_dir():
        return []
    out = []
    for p in sorted(cur.rglob("*"), key=lambda value: value.as_posix()):
        rel = p.relative_to(cur)
        rel_text = rel.as_posix()
        if _is_transient(package, rel_text, p):
            continue
        peer = new / rel
        if p.is_symlink():
            out.append(rel_text)
        elif p.is_file() and (not peer.is_file() or peer.is_symlink()):
            out.append(rel_text)
        elif p.is_dir() and (not peer.is_dir() or peer.is_symlink()):
            out.append(rel_text.rstrip("/") + "/")
        elif not p.is_file() and not p.is_dir():
            out.append(rel_text)
    return sorted(out)


def cmd_diff(root, src, MSG):
    changed = []
    for name, cur, new in pairs(root, src):
        if new.is_file():
            same = cur.is_file() and sha(cur) == sha(new)
            if not same:
                changed.append((name, 1, 0 if cur.is_file() else 1, 0, []))
            continue
        n_mod = n_new = 0
        for np in sorted(new.rglob("*"), key=lambda p: p.as_posix()):
            if not np.is_file() or VERSION_FILE == np.name:
                continue
            rel = np.relative_to(new)
            cp = cur / rel
            if not cp.is_file():
                n_new += 1
            elif sha(cp) != sha(np):
                n_mod += 1
        only = target_only_files(cur, new, name)
        if n_mod or n_new or only:
            changed.append((name, n_mod, n_new, len(only), only))
    if not changed:
        print(MSG["diff_none"])
        print_retired(root, MSG)
        return 0
    print(MSG["diff_head"])
    for name, m, n, o, only in changed:
        print(MSG["diff_row"].format(name=name, m=m, n=n, o=o))
        for path in only:
            print(MSG["target_only_row"].format(path=f"{name}/{path}"))
    print()
    print_retired(root, MSG)
    print(MSG["diff_tail"])
    return 0


def cmd_receipts(root, MSG):
    rows, bad = _receipt_rows(root)
    if rows:
        print(MSG["receipts_head"])
        for row in rows:
            print(MSG["receipts_row"].format(
                rid=row["receipt_id"], created=row.get("created_utc", "?"),
                operation=row.get("operation", "?"), target=row["target"]))
    else:
        print(MSG["receipts_empty"])
    for name, err in bad:
        print(MSG["receipts_bad"].format(name=name, err=err))
    return 0


def _current_paths(root, target):
    base = root / pathlib.PurePosixPath(target)
    if base.is_symlink():
        return [target]
    if base.is_file():
        return [target]
    if not base.is_dir():
        return []
    out = []
    for path in sorted(base.rglob("*"), key=lambda value: value.as_posix()):
        rel = path.relative_to(base).as_posix()
        if _is_transient(target, rel, path):
            continue
        if path.is_file() or path.is_symlink():
            out.append(f"{target}/{rel}")
    return out


def cmd_receipt_diff(root, token, path_arg, MSG):
    if not token:
        print(MSG["receipt_needs_id"]); return 1
    try:
        data = _resolve_receipt(root, token)
    except ReceiptError as e:
        print(MSG["receipt_invalid"].format(rid=token, err=e)); return 2
    if data is None:
        print(MSG["receipt_unknown"].format(rid=token)); return 1
    rid = data["receipt_id"]
    target = data["target"]
    files = _receipt_files(data)
    try:
        shown = _safe_rel(path_arg) if path_arg else target
    except ReceiptError:
        print(MSG["receipt_path_bad"].format(path=path_arg, target=target)); return 1
    if not _under_target(shown, target):
        print(MSG["receipt_path_bad"].format(path=shown, target=target)); return 1
    if path_arg and shown not in files:
        print(MSG["receipt_path_not_saved"].format(path=shown, rid=rid)); return 1

    p = _git(root, ["diff", "--no-ext-diff", "--no-renames", "--no-color",
                    data["ref"], "--", shown])
    if p.returncode != 0:
        print(MSG["receipt_invalid"].format(
            rid=rid, err=(p.stderr or "git diff failed").strip())); return 2
    print(MSG["receipt_diff_head"].format(rid=rid, path=shown))
    if p.stdout:
        print(p.stdout, end="" if p.stdout.endswith("\n") else "\n")
    saved = set(files)
    new_paths = [] if path_arg else sorted(set(_current_paths(root, target)) - saved)
    if new_paths:
        print(MSG["receipt_new_head"])
        for rel in new_paths:
            print(MSG["receipt_new_row"].format(path=rel))
    if not p.stdout and not new_paths:
        print(MSG["receipt_no_diff"])
    return 0


def cmd_restore(root, token, path_arg, MSG):
    if not token:
        print(MSG["receipt_needs_id"]); return 1
    if not path_arg:
        print(MSG["restore_needs_path"]); return 1
    try:
        data = _resolve_receipt(root, token)
    except ReceiptError as e:
        print(MSG["receipt_invalid"].format(rid=token, err=e)); return 2
    if data is None:
        print(MSG["receipt_unknown"].format(rid=token)); return 1
    rid = data["receipt_id"]
    try:
        rel = _safe_rel(path_arg)
    except ReceiptError:
        print(MSG["receipt_path_bad"].format(path=path_arg, target=data["target"])); return 1
    if not _under_target(rel, data["target"]):
        print(MSG["receipt_path_bad"].format(path=rel, target=data["target"])); return 1
    entry = _receipt_files(data).get(rel)
    if entry is None:
        print(MSG["receipt_path_not_saved"].format(path=rel, rid=rid)); return 1
    current = root / pathlib.PurePosixPath(rel)
    if current.is_symlink() or not current.is_file():
        print(MSG["restore_current_missing"].format(path=rel)); return 1
    if _worktree_matches(root, entry):
        print(MSG["restore_noop"].format(path=rel, rid=rid)); return 0

    print(MSG["restore_cp_first"])
    checkpoint_program = _checkpoint_program(root)
    if checkpoint_program is None:
        print(MSG["checkpoint_peer_missing"]); return 2
    rc = subprocess.run([sys.executable, str(checkpoint_program),
                         "--root", str(root), "--mode", "tool",
                         "--tool-id", "upgrade",
                         "--operation", f"restore-{pathlib.PurePosixPath(rel).name}"]).returncode
    if rc != 0:
        print(MSG["restore_cp_failed"].format(rc=rc)); return 2
    p = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    undo_commit = (p.stdout or "").strip()
    if p.returncode != 0 or len(undo_commit) < 7:
        print(MSG["restore_receipt_failed"].format(err="cannot read undo checkpoint")); return 2
    try:
        undo = _create_receipt(root, undo_commit, rel, [rel], [],
                               "restore-undo", True)
    except ReceiptError as e:
        print(MSG["restore_receipt_failed"].format(err=e)); return 2
    undo_id = undo["receipt_id"]

    restored = _git(root, ["restore", f"--source={data['ref']}", "--worktree", "--", rel])
    if restored.returncode != 0:
        print(MSG["restore_git_failed"].format(path=rel, rc=restored.returncode,
                                                undo=undo_id)); return 2
    if not _worktree_matches(root, entry):
        print(MSG["restore_verify_failed"].format(path=rel, rid=rid, undo=undo_id)); return 2
    print(MSG["restore_done"].format(path=rel, rid=rid, undo=undo_id))
    return 0


def cmd_apply(root, src, target, MSG):
    if target in RETIRED_DIRS:
        v, into = RETIRED_DIRS[target]
        print(MSG["retired_target"].format(t=target, v=v, into=into)); return 1
    if target in NEVER_TOUCH:
        print(MSG["never"].format(t=target)); return 1
    if target not in FRAMEWORK_DIRS and target not in FRAMEWORK_FILES:
        print(MSG["not_framework"].format(t=target,
              ok=" ".join(FRAMEWORK_DIRS + FRAMEWORK_FILES))); return 1
    s = src / target
    if not s.exists():
        print(MSG["missing_in_upgrade"].format(t=target, src=src)); return 1
    if not _same_edition(root, src, MSG):
        return 1

    dst = root / target
    only = target_only_files(dst, s, target)
    if only:
        print(MSG["target_only_block"].format(t=target))
        for path in only:
            print(MSG["target_only_row"].format(path=f"{target}/{path}"))
        return 1

    # ⛔ R-33 的位置：檢查點失敗 ⛔ 不得往下覆蓋。
    print(MSG["cp_first"])
    # 🔴 **`--mode tool` must be passed explicitly.**
    #    ⚠️ **v1.4.1 and v1.4.2 did not pass it, so this fell to the human default —
    #    one upgrade moved the `reviewed` tag to the pre-upgrade commit and printed
    #    "I have looked at this".**
    #    **⇒ AI work the user had not reviewed vanished from the pending list.**
    # Prefer the peer beside the running upgrader; only a compatible project copy
    # may be used as fallback. Probe by reading the exact API marker, never by execution.
    checkpoint_program = _checkpoint_program(root)
    if checkpoint_program is None:
        print(MSG["checkpoint_peer_missing"]); return 2
    rc = subprocess.run([sys.executable, str(checkpoint_program),
                         "--root", str(root), "--mode", "tool",
                         "--tool-id", "upgrade",
                         "--operation", f"apply-{target}"]).returncode
    if rc != 0:
        print(MSG["cp_failed"].format(rc=rc)); return 2

    # A commit id by itself is not a receipt: ignored files and index flags can leave
    # the commit older than the bytes about to be deleted. Verify each pre-image with
    # Git's filters, pin the commit with a private ref, and persist a checked manifest.
    p = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    cp = (p.stdout or "").strip()
    if p.returncode != 0 or len(cp) < 7:
        print(MSG["no_receipt"].format(rc=p.returncode)); return 2
    try:
        paths, omitted = _preimage_paths(root, dst, s, target)
        receipt = _create_receipt(root, cp, target, paths, omitted,
                                  f"apply-{target}", dst.exists() or dst.is_symlink())
    except PreimageError as e:
        rows = "\n".join(f"       ⛔ {path}" for path in e.paths)
        print(MSG["receipt_unprotected"].format(paths=rows)); return 2
    except ReceiptError as e:
        print(MSG["receipt_create_failed"].format(err=e)); return 2

    # Close the check/use gap: no file may change or appear between receipt creation
    # and the destructive replacement.
    try:
        paths_now, omitted_now = _preimage_paths(root, dst, s, target)
        if (sorted(paths_now) != sorted(entry["path"] for entry in receipt["files"])
                or sorted(omitted_now) != sorted(receipt["omitted_transient"])
                or target_only_files(dst, s, target)):
            raise PreimageError(sorted(set(paths_now) ^
                                       {entry["path"] for entry in receipt["files"]})
                                or [target])
        _verified_entries(root, cp, paths_now)
    except PreimageError as e:
        rows = "\n".join(f"       ⛔ {path}" for path in e.paths)
        print(MSG["receipt_unprotected"].format(paths=rows)); return 2
    except ReceiptError as e:
        print(MSG["receipt_create_failed"].format(err=e)); return 2

    if s.is_dir():
        if dst.is_dir():
            shutil.rmtree(dst)
        shutil.copytree(s, dst)
    else:
        shutil.copy2(s, dst)
    print(MSG["applied"].format(t=target))
    print(MSG["receipt"].format(rid=receipt["receipt_id"], cp=cp, target=target))
    print(MSG["applied_tail"].format(rid=receipt["receipt_id"]))
    # ⚠️ **也印在這裡，⛔ 而不是只印在 `check`／`diff`。**
    #    🔴 **理由：退役提示只存在於新版程式裡，而使用者是用舊版程式跑 `diff` 的**——
    #    **⇒ 他能看到這則訊息的最早時機，就是換完 `scripts` 的這一刻。**
    print_retired(root, MSG)
    return 0


def main(MSG):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("action", nargs="?", default="check",
                    choices=("check", "diff", "apply", "receipts", "receipt-diff", "restore"))
    ap.add_argument("target", nargs="?", default=None)
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(MSG["usage"]); return 0
    if ((a.action in ("check", "diff", "receipts") and (a.target or a.path))
            or (a.action == "apply" and a.path)):
        ap.error("too many arguments for this action")
    root = pathlib.Path(a.root).resolve() if a.root else \
        pathlib.Path(__file__).resolve().parents[2]
    if not (root / "governance/AGENTS.md").is_file():
        print(MSG["wrong_folder"].format(root=root)); return 1

    print("=" * 46); print(MSG["title"]); print("=" * 46); print()
    if a.action == "check":
        return cmd_check(root, MSG)
    if a.action == "receipts":
        return cmd_receipts(root, MSG)
    if a.action == "receipt-diff":
        return cmd_receipt_diff(root, a.target, a.path, MSG)
    if a.action == "restore":
        return cmd_restore(root, a.target, a.path, MSG)

    src = root / "_upgrade"
    if not src.is_dir():
        print(MSG["no_upgrade_dir"]); return 1
    # 允許 _upgrade/ 底下多包一層（下載 zip 常會如此）
    inner = [p for p in src.iterdir() if p.is_dir() and (p / "governance").is_dir()]
    if (not (src / "governance").is_dir()) and len(inner) == 1:
        src = inner[0]

    if a.action == "diff":
        return cmd_diff(root, src, MSG)
    if not a.target:
        print(MSG["apply_needs_target"]); return 1
    return cmd_apply(root, src, a.target, MSG)


if __name__ == "__main__":
    raise SystemExit(main(MSG))
