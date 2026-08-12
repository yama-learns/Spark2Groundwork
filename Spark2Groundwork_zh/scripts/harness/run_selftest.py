#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成對種入缺陷自測（跨平台）

⚠️ **兩半都必要。**
只測「該抓的有沒有抓到」，無法分辨「感測器有效」與「感測器對每個檔案都報錯」——
先行專案的 harness 曾因此一度全數誤報而看似正常。

⛔ **自測失敗時，先假設是感測器壞了，不是專案文件壞了。**
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "selftest"
PY = sys.executable
ok = bad = 0


def run(sensor, root):
    r = subprocess.run([PY, str(HERE / sensor), "--root", str(root)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def expect(desc, want_code, sensor, fixture, needle=None):
    global ok, bad
    root = FIX / fixture
    if not root.exists():
        print(f"  ❌ {desc}（樣本目錄不存在：{fixture}）"); bad += 1; return
    code, out = run(sensor, root)
    hit = (code == want_code) and (needle is None or needle in out)
    if hit:
        print(f"  ✅ {desc}"); ok += 1
    else:
        extra = f"，且含「{needle}」" if needle else ""
        print(f"  ❌ {desc}（期望 exit {want_code}{extra}，實得 exit {code}）"); bad += 1


print("── 成對種入缺陷自測 ──────────────────────────")

# 猜想台帳
expect("反證條件為空須告警", 0, "sensor_conjecture_ledger.py", "conj_nofalsif", "FALSIFICATION_UNADJUDICATED")
expect("競爭解釋為空須 FAIL", 1, "sensor_conjecture_ledger.py", "conj_norival", "RIVAL_EMPTY")
expect("正確台帳不誤報", 0, "sensor_conjecture_ledger.py", "conj_clean")
expect("填了字但未裁決仍須告警", 0, "sensor_conjecture_ledger.py",
       "conj_filled_unadjudicated", "FALSIFICATION_UNADJUDICATED")

# 主張台帳（錨點）
expect("錨點查無須 FAIL", 1, "sensor_claim_ledger.py", "claim_ghost", "ANCHOR_NOT_IN_SOURCE")
expect("連字與跨行斷字不誤報", 0, "sensor_claim_ledger.py", "claim_ligature")
expect("正確錨點不誤報", 0, "sensor_claim_ledger.py", "claim_clean")

# 自我背書
expect("自我背書須抓到", 1, "sensor_self_certification.py", "selfcert_bad")
expect("閘門式要求不誤報", 0, "sensor_self_certification.py", "selfcert_clean")

# 治理文本
expect("跨檔重複長句須告警", 0, "sensor_governance_text.py", "gov_dup", "DUPLICATE_RULE_TEXT")
expect("懸空章節引用須告警", 0, "sensor_governance_text.py", "gov_badref", "SECTION_REF_UNRESOLVED")
expect("治理文本乾淨不誤報", 0, "sensor_governance_text.py", "gov_clean")

print("\n" + "=" * 48)
print(f"  通過 {ok} 項｜失敗 {bad} 項")
print("  結果：" + ("自測全數通過" if not bad else "自測失敗 — ⛔ 感測器變更不得提交"))
sys.exit(1 if bad else 0)
