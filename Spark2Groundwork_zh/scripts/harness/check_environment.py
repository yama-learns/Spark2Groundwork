#!/usr/bin/env python3
"""User check button: diagnose this interpreter, then call the existing sensor runner.
Exit 0: checks passed; 1: checks found a problem; 2: incomplete.
Check mode makes no research writes. Explicit save/reviewed/sync actions can write.
No installation or permissions changes.
"""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_diagnostics import is_python_crash as _is_python_crash

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=("zh", "en"), default="en")
    parser.add_argument("--diagnose-only", action="store_true")
    parser.add_argument("--action", choices=("check", "save", "reviewed", "review", "update", "sync"), default="check")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    def say(zh, en):
        print(zh if args.lang == "zh" else en, flush=True)
    def incomplete(zh, en):
        say("[INCOMPLETE] " + zh, "[INCOMPLETE] " + en)
        say("請開啟 docs/START_HERE.html，依畫面說明處理後再雙擊檢查。",
            "Open docs/START_HERE.html, follow its steps, then double-click Check Project again.")
        return 2
    say("環境確認與專案檢查", "Environment and project check")
    print("Python:", sys.version.split()[0], "|", sys.executable)
    print("Environment:", platform.system(), platform.machine())
    print("Project:", ROOT)
    say("這是執行端的環境；AI 的遠端或虛擬機結果不代表你的電腦。",
        "This describes the executing environment. An AI VM or remote host is not your computer.")
    if sys.version_info < (3, 9):
        return incomplete("Python 版本過舊；需要 3.9 以上。", "Python is too old; 3.9 or newer is required.")
    if not (ROOT / "PROJECT.md").is_file() or not (ROOT / "governance_config.json").is_file():
        return incomplete("專案檔案缺漏，請保全資料並重新取得完整單語資料夾。",
                          "Project files are missing. Preserve your data and obtain the complete single-language folder.")
    git = shutil.which("git")
    if not git and sys.platform == "win32":
        for parent in (os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
            if parent:
                candidate = Path(parent) / ("Git/cmd/git.exe" if parent == os.environ.get("ProgramFiles") else "Programs/Git/cmd/git.exe")
                if candidate.is_file():
                    git = str(candidate)
                    break
    if not git:
        return incomplete("找不到 Git；先依說明頁安裝，研究文件仍可編寫。",
                          "Git was not found. Use the installation guide; research documents remain editable.")
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = str(Path(git).parent) + os.pathsep + env.get("PATH", "")
    try:
        # Apple's git stub can open an installer; diagnose first without invoking it.
        if sys.platform == "darwin" and git == "/usr/bin/git":
            selected = subprocess.run(["/usr/bin/xcode-select", "-p"], capture_output=True,
                                      encoding="utf-8", errors="replace", timeout=10, env=env)
            if selected.returncode:
                return incomplete("Apple 開發工具尚未就緒；請看說明頁的 Git 安裝方式。",
                                  "Apple developer tools are not ready. See Git installation in the guide.")
        version = subprocess.run([git, "--version"], capture_output=True,
                                 encoding="utf-8", errors="replace", timeout=10, env=env)
        if version.returncode or not version.stdout.startswith("git version "):
            return incomplete("Git 無法正常執行。", "Git could not run successfully.")
        print("Git:", version.stdout.strip(), "|", git)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return incomplete("Git 確認未完成：" + str(exc), "Git check did not finish: " + str(exc))
    if args.diagnose_only:
        say("[ENVIRONMENT_OK] 工具可執行；尚未檢查專案內容。",
            "[ENVIRONMENT_OK] Tools can run; project contents have NOT been checked.")
        return 0
    if args.action != "check":
        return perform_action(args.action, env, say, incomplete)
    runner = ROOT / "scripts/harness/run_all_sensors.py"
    if not runner.is_file():
        return incomplete("檢查程式缺漏。", "The project check program is missing.")
    say("開始既有專案檢查。這不建立快照，也不表示研究內容已獲證實。",
        "Running the existing project checks. This creates no checkpoint and does not verify scientific truth.")
    try:
        result = subprocess.run([sys.executable, "-I", "-B", str(runner)], cwd=ROOT, env=env,
                                capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return incomplete("檢查未完成；子檢查可能仍在執行，請保留畫面而勿連續重按：" + str(exc),
                          "Checks did not finish; a subcheck may still be running. Keep the result and avoid repeated clicks: " + str(exc))
    if _is_python_crash(result.returncode, result.stderr):
        return incomplete("檢查程式發生錯誤；不是研究文件已判定失敗。",
                          "The checker crashed; this is not a finding against your research documents.")
    if result.returncode not in (0, 1, 2):
        return incomplete("檢查程式異常退出：" + str(result.returncode),
                          "Unexpected check exit: " + str(result.returncode))
    if result.returncode == 2:
        say("部分檢查未完成。新下載尚無快照時，請依 SETUP 的快照步驟處理；不要把缺證改成通過。",
            "Some checks are incomplete. A new download without a checkpoint needs SETUP's snapshot step; missing evidence is not PASS.")
    return result.returncode


def perform_action(action, env, say, incomplete):
    """Fixed user-button actions; no arbitrary script or shell command forwarding."""
    def invoke(script, *args):
        try:
            result = subprocess.run([sys.executable, "-I", "-B",
                str(ROOT / "scripts/harness" / script), *args], cwd=ROOT,
                env=env, capture_output=True, encoding="utf8", errors="replace", timeout=120)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return incomplete("操作未完成；請保留畫面，勿連按或清除鎖：" + str(exc),
                "Operation incomplete. Keep the output; do not repeat or remove locks: " + str(exc))
        print(result.stdout, end="")
        if result.stderr: print(result.stderr, file=sys.stderr, end="")
        if result.returncode not in (0, 1, 2) or _is_python_crash(result.returncode, result.stderr):
            return incomplete("操作程式異常退出。", "The operation program crashed.")
        return result.returncode
    if action == "save":
        say("儲存進度，不表示你已閱讀；已閱基準不移動。", "Save progress only; the reviewed baseline will not move.")
        return invoke("checkpoint.py", "--mode", "tool", "--tool-id", "user-save", "--operation", "save-progress")
    if action == "reviewed":
        say("人工已閱確認：你按下此按鈕，會把已閱基準移到目前內容；AI不得代按。",
            "Human review confirmation: this button moves the reviewed baseline to current contents. AI must not press it for you.")
        return invoke("checkpoint.py", "--mode", "human")
    if action == "review":
        return invoke("review_changes.py")
    if action == "sync":
        say("先保存還原點，再補缺少的規則；既有自訂文字不覆寫。",
            "Save a restore point before appending missing rules; existing custom text is not overwritten.")
        saved = invoke("checkpoint.py", "--mode", "tool", "--tool-id", "rule-sync", "--operation", "before-sync")
        if saved: return saved
        rc = invoke("tool_sync_my_rules.py")
        if rc: return rc
        return invoke("sensor_my_rules.py", "--root", str(ROOT))
    if action == "update":
        rc = invoke("upgrade.py", "check")
        if rc:
            say("新版查詢未完成，不表示已是最新版。檢查網路／DNS／憑證與系統時間；不要停用TLS驗證。",
                "Latest-version lookup incomplete, not proof you are up to date. Check network/DNS/certificates and clock; never disable TLS verification.")
        if (ROOT / "_upgrade").is_dir():
            rc = max(rc, invoke("upgrade.py", "diff"))
        say("本按鈕不套用更新。請開docs/UPDATE.md，依逐包替換步驟操作。",
            "This button does not apply updates. Open docs/UPDATE.md for one-package-at-a-time replacement.")
        return rc
    return incomplete("未知操作。", "Unknown operation.")


if __name__ == "__main__":
    sys.exit(main())
