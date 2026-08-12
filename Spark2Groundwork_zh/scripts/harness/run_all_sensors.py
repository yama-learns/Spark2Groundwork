#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""總執行器（跨平台）

⚠️ **刻意用 Python 而非 shell**：Windows 沒有內建 bash，
而本框架的使用者不一定裝得起 WSL。**一個跑不起來的感測器套件等於沒有感測器套件。**

退出碼：0 PASS｜1 FAIL｜2 INCOMPLETE（⛔ **未完成 ≠ 通過**）
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# 感測器 → 是否為選用
SENSORS = [
    ("sensor_conjecture_ledger.py", False),
    ("sensor_claim_ledger.py", False),
    ("sensor_self_certification.py", False),
    ("sensor_governance_text.py", False),
    ("sensor_scope_and_t0.py", False),
]

# ⚠️ **以下不列入預設套件，因為它們的介面是「一份檔案」而非「整個專案」。**
#    把它們硬塞進總執行器，只會產生一個永遠 INCOMPLETE 的假訊號——
#    而 INCOMPLETE 是本框架最不能被稀釋的一個狀態。
#    用法見 profiles/PROFILE_external_tools.md：
#        python3 scripts/harness/sensor_prompt_self_contained.py <prompt.md>
ON_DEMAND = ["sensor_prompt_self_contained.py", "sensor_model_attribution.py"]


def main() -> int:
    results, worst = [], 0
    for name, optional in SENSORS:
        p = HERE / name
        if not p.exists():
            if not optional:
                print(f"  [INCOMPLETE] SENSOR_MISSING: {name} 不存在——**本項未檢查，不等於通過**")
                worst = max(worst, 2)
            continue
        r = subprocess.run([sys.executable, str(p), "--root", str(ROOT)],
                           capture_output=True, text=True)
        print(r.stdout.rstrip())
        if r.returncode not in (0, 1, 2):
            # ⚠️ 崩潰是「查不了」，不是「查出問題」。混為一談會讓
            #    「感測器壞了」看起來像「文件有問題」，而那會讓人去修一份沒問題的文件。
            print(f"  [INCOMPLETE] SENSOR_CRASHED: {name} 退出碼 {r.returncode}")
            print((r.stderr or "").rstrip()[-600:])
            worst = max(worst, 2)
        else:
            worst = max(worst, r.returncode) if r.returncode != 1 else 1
            if r.returncode == 1:
                worst = 1 if worst != 2 else 2
        results.append({"sensor": name, "code": r.returncode})

    print("\n" + "=" * 48)
    label = {0: "✅ 總結：PASS", 1: "❌ 總結：FAIL",
             2: "⚠️  總結：INCOMPLETE（**未完成 ≠ 通過**）"}[worst]
    print(f"  {label}（{len(results)} 支已執行）")
    print("      ⚠️ 綠燈的範圍僅限已機械化的環節。")
    print("      論證品質、來源實質支持、外推誠實刻意不機械化。")
    (HERE / "harness_status.json").write_text(
        json.dumps({"worst": worst, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return worst


if __name__ == "__main__":
    sys.exit(main())
