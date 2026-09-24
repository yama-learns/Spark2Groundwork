#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成對種入缺陷自測（跨平台）

⚠️ **兩半都必要。**
只測「該抓的有沒有抓到」，無法分辨「感測器有效」與「感測器對每個檔案都報錯」——
先行專案的 harness 曾因此一度全數誤報而看似正常。

⛔ **自測失敗時，先假設是感測器壞了，不是專案文件壞了。**

## 🔴 「不得誤報」那一半為什麼不能只驗退出碼

**觸發個案（他專案實測，本框架實查後確認同樣成立）：**
`WARN` 級的 finding **不改變退出碼**（見 `_common.py` 的 `emit`：只有 FAIL→1、INCOMPLETE→2）。
於是一個只斷言 `exit == 0` 的「不得誤報」測試，**對任意多筆 WARN 級誤報一律印 ✅。**

**本框架的實查結果（修正前）：** 五個「不誤報」樣本中，
`selfcert_clean` 吐 2 筆 WARN、`gov_clean` 吐 3 筆，**而自測對兩者都印 ✅。**

→ 因此 `expect()` 新增 **`forbid`**：列出「這個乾淨樣本裡**絕不該出現**的 finding code」。
⚠️ 判準刻意**不是「不得有任何 WARN」**——
fixture 目錄本來就不含全部 glob，`SCAN_GLOB_MATCHES_NOTHING` 是基礎建設噪音，不是感測器誤報。
**把噪音當誤報，會逼下一個人去加豁免，而豁免會把整套自測挖成盲區。**

⛔ **但容忍必須看得見**：被容忍的 WARN 一律在結尾列印代碼與筆數。
**靜默容忍與沒有容忍，在畫面上長得一樣。**
"""
import os
import pathlib
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ⛔ 輸出編碼必須先固定成 UTF-8，⛔ 否則 Windows 上印到第一個符號就當掉。
#    唯一定義處：`_common._force_utf8`（見該處的實測個案）。
from _common import _force_utf8                            # noqa: E402
from run_all_sensors import _is_python_crash               # noqa: E402
_force_utf8()
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "selftest"
PY = sys.executable
ok = bad = 0
tolerated = Counter()


def run(sensor, root):
    # ⛔ 子行程的輸出一律以 UTF-8 解，並強制子行程也以 UTF-8 印。
    #    ⚠️ 實測：只設其中一半時，`_translate_newlines` 會丟 UnicodeDecodeError——
    #    **自測本身在 Windows 上當掉，而它正是用來證明其他東西沒當掉的那支程式。**
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, str(HERE / sensor), "--root", str(root)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def expect(desc, want_code, sensor, fixture, needle=None, forbid=()):
    """desc：一句話｜want_code：期望退出碼｜needle：輸出中**必須**出現的字串
    forbid：輸出中**絕不得**出現的 finding code（「不得誤報」那一半用）"""
    global ok, bad
    root = FIX / fixture
    if not root.exists():
        print(f"  ❌ {desc}（樣本目錄不存在：{fixture}）"); bad += 1; return
    code, out = run(sensor, root)
    banned = [c for c in forbid if c in out]
    hit = (code == want_code) and (needle is None or needle in out) and not banned
    # 統計被容忍的 WARN。
    # ⚠️ **刻意扣除 needle 指名的那一個代碼**——那是本測試要求它出現的偵測結果，
    #    把它算進「容忍」會讓這個數字失去意義（首版就犯了這個錯，實測 18 → 13）。
    for line in out.splitlines():
        if "[WARN]" not in line:
            continue
        for tok in line.replace("]", " ").replace("[", " ").replace(":", " ").split():
            if tok.isupper() and "_" in tok:
                if not (needle and tok in needle):
                    tolerated[tok] += 1
                break
    if hit:
        print(f"  ✅ {desc}"); ok += 1
    else:
        why = []
        if code != want_code:
            why.append(f"期望 exit {want_code}，實得 {code}")
        if needle and needle not in out:
            why.append(f"輸出未含「{needle}」")
        if banned:
            why.append(f"⛔ **誤報**：乾淨樣本出現 {'、'.join(banned)}")
        print(f"  ❌ {desc}（{'；'.join(why)}）"); bad += 1


print("── 成對種入缺陷自測 ──────────────────────────")

# 猜想台帳
expect("反證條件為空須告警", 0, "sensor_conjecture_ledger.py", "conj_nofalsif", "FALSIFICATION_UNADJUDICATED")
expect("競爭解釋為空須 FAIL", 1, "sensor_conjecture_ledger.py", "conj_norival", "RIVAL_EMPTY")
expect("正確台帳不誤報", 0, "sensor_conjecture_ledger.py", "conj_clean",
       forbid=("FALSIFICATION_UNADJUDICATED", "RIVAL_EMPTY", "RIVAL_PREDICTION_EMPTY",
               "CONJECTURE_FIELD_MISSING", "CONJECTURE_ID_DUPLICATE"))
expect("填了字但未裁決仍須告警", 0, "sensor_conjecture_ledger.py",
       "conj_filled_unadjudicated", "FALSIFICATION_UNADJUDICATED")
expect("狀態不在六種之內須 FAIL", 1, "sensor_conjecture_ledger.py",
       "conj_status_bad", "CONJECTURE_STATUS_INVALID")
# ⚠️ 下面這一項是**回歸測試**，不是新功能測試。
#    ⚫ 已除役與 🟤 休眠是台帳 §0.1 的合法狀態，而舊碼的 VALID_STATUS 只有四種，
#    會對它們判 CONJECTURE_STATUS_INVALID；且舊碼的 `continue` 使它們永遠走不到
#    反證條件檢查——**兩個缺陷互相遮蔽，只修一個會讓另一個當場現形。**
expect("已除役與休眠不誤報", 0, "sensor_conjecture_ledger.py", "conj_retired_dormant",
       forbid=("CONJECTURE_STATUS_INVALID", "FALSIFICATION_UNADJUDICATED",
               "EVIDENCE_MISSING_FOR_STATUS"))
expect("🟢／🔴 缺依據須 FAIL", 1, "sensor_conjecture_ledger.py",
       "conj_evidence_missing", "EVIDENCE_MISSING_FOR_STATUS")
expect("引用台帳中不存在的編號須 FAIL", 1, "sensor_conjecture_ledger.py",
       "conj_citation_ghost", "CITATION_NOT_IN_LEDGER")
expect("引用存在的編號不誤報", 0, "sensor_conjecture_ledger.py", "conj_citation_ok",
       forbid=("CITATION_NOT_IN_LEDGER",))
# 🔴 裁決 8：提案檔豁免。**兩半都必要——**
#    上一項（`conj_citation_ghost`）守的是「豁免不得過寬」：非 handoffs 的檔案照樣 FAIL。
#    這一項守的是「豁免要生效，且必須被印出來」。
#    ⚠️ 豁免的判準刻意是**結構性**（路徑＋檔名），不是一句自由文字的理由——
#    先行專案的教訓：一句讀起來合理的話讓感測器對一筆真捏造永久靜默，而儀表板是綠的。
expect("提案檔豁免引用檢查，且豁免須印出", 0, "sensor_conjecture_ledger.py",
       "conj_citation_proposal", "CITATION_CHECK_EXEMPTED",
       forbid=("CITATION_NOT_IN_LEDGER",))
# ⚠️ 這一組的兩半在**同一個樣本**上：必須報「已聲明」，且**絕不得**報「未裁決／為空」。
#    後者才是重點——舊訊息把「刻意留白並寫下理由」印成「反證條件為空」，
#    **與忘記填一字不差**，於是下一輪的人會去把它填上，而那正是台帳 §0.3 第 1 條想擋的。
expect("刻意留白並附理由須改報已聲明", 0, "sensor_conjecture_ledger.py",
       "conj_declared_unfalsifiable", "FALSIFICATION_DECLARED_UNFALSIFIABLE",
       forbid=("FALSIFICATION_UNADJUDICATED",))

# 主張台帳（錨點）
expect("錨點查無須 FAIL", 1, "sensor_claim_ledger.py", "claim_ghost", "ANCHOR_NOT_IN_SOURCE")
expect("連字與跨行斷字不誤報", 0, "sensor_claim_ledger.py", "claim_ligature",
       forbid=("ANCHOR_NOT_IN_SOURCE", "ANCHOR_EMPTY"))
expect("正確錨點不誤報", 0, "sensor_claim_ledger.py", "claim_clean",
       forbid=("ANCHOR_NOT_IN_SOURCE", "ANCHOR_EMPTY"))
# 🔴 **有三種狀態，不是兩種。** 框架開始隨附一個空的 `corpus_md/`，讓新使用者看得到提取物放哪裡——
#    **於是每一個新專案第一次執行都報 INCOMPLETE。**
#    ⛔ 一開始就狼來了的輸出，正是教會人忽略它的方式。
expect("空的提取資料夾不算「查不了」", 0, "sensor_claim_ledger.py",
       "corpus_empty", "CORPUS_EMPTY",
       forbid=("CORPUS_MANIFEST_MISSING", "未檢查 ≠ 通過"))
# ⚠️ 成對的另一半：有提取物卻沒有 manifest，仍然是 INCOMPLETE。
expect("有提取物但無 manifest 仍是 INCOMPLETE", 2, "sensor_claim_ledger.py",
       "corpus_unmanifested", "CORPUS_MANIFEST_MISSING")
expect("來源無法解析須 INCOMPLETE 絕不放寬", 2, "sensor_claim_ledger.py", "claim_unresolved", "ANCHOR_SOURCE_UNRESOLVED")
expect("同作者同年多篇來源歧義須 INCOMPLETE", 2, "sensor_claim_ledger.py", "claim_ambiguous", "ANCHOR_SOURCE_AMBIGUOUS")
expect("明示檔名與年份區分不誤報", 0, "sensor_claim_ledger.py", "claim_explicit_match",
       forbid=("ANCHOR_NOT_IN_SOURCE", "ANCHOR_SOURCE_UNRESOLVED", "ANCHOR_SOURCE_AMBIGUOUS"))
expect("manifest 非陣列格式錯誤須 INCOMPLETE", 2, "sensor_claim_ledger.py", "corpus_manifest_malformed", "CORPUS_MANIFEST_MALFORMED")
expect("姓氏子字串比對不可偷換論文須 INCOMPLETE", 2, "sensor_claim_ledger.py", "claim_author_substring", "ANCHOR_SOURCE_UNRESOLVED")
# ⚠️ D-20260921-X87 / CLAIM-EXIT-1：有有效主張但全部未進入錨點查證時，
#    退出碼契約為 INCOMPLETE（exit 2），文字與 --json 一致。
expect("全部主張未進入查證時須 INCOMPLETE", 2, "sensor_claim_ledger.py",
       "claim_all_anchors_empty", "CLAIM_NONE_CHECKED")
expect("實質文字提到樣板符號時不得被當成空樣板", 2, "sensor_claim_ledger.py",
       "claim_embedded_marker_mixed", "本次 1 筆有效主張")
# ⚠️ 覆核 B-2：作者欄唯一命中是感測器的推論，不是台帳明說的；必須印出來讓人看見。
expect("作者欄唯一命中的推論須可見", 0, "sensor_claim_ledger.py",
       "claim_noyear_inference", "僅作者欄唯一命中")


# 自我背書
expect("自我背書須抓到", 1, "sensor_self_certification.py", "selfcert_bad")
expect("閘門式要求與誠實揭露皆不誤報", 0, "sensor_self_certification.py", "selfcert_clean",
       forbid=("UNVERIFIABLE_SELF_CERT", "UNSUPPORTED_GLOBAL_APPRAISAL"))
# ⚠️ **觸發個案：一份真實的跨模型審計報告，含 `Audit_Protocol.md` §3 明文禁用的
#    「極高」「堵死」「無待修復」三個詞，而本感測器判 PASS。**
#    根因不是 APPRAISAL 沒抓到，是 SELF 不含「本輪／本次／本專案」。
#    ⛔ 但 SELF 只在 **WARN 分支**放寬——FAIL 分支放寬會誤報誠實揭露，
#    而那正是上一項 fixture 新增那一段要守的東西。
expect("整體性好評須告警", 0, "sensor_self_certification.py", "selfcert_appraisal",
       "UNSUPPORTED_GLOBAL_APPRAISAL", forbid=("UNVERIFIABLE_SELF_CERT",))

# 治理文本
expect("跨檔重複長句須告警", 0, "sensor_governance_text.py", "gov_dup", "DUPLICATE_RULE_TEXT")
# ⚠️ **句子結束在行中央的情況**：`**...first.** Every audit...` 的句號後面是 `*` 不是空白。
#    舊斷句器只認 `。` 與換行，於是英文版只能比對「整行相同」，**這一類重複完全看不見**。
#    fixture 刻意只種這一種缺陷——`gov_dup` 抓得到的那種在這裡不存在。
expect("句中結束的重複長句須告警", 0, "sensor_governance_text.py", "gov_dup_midline",
       "DUPLICATE_RULE_TEXT")
expect("懸空章節引用會告警", 0, "sensor_governance_text.py", "gov_badref", "SECTION_REF_UNRESOLVED")
# 🔴 **短式。** 原本只查長式 `` `<檔名>.md` §N ``，而框架有 68 處寫的是「憲章 §N」——
#    **三筆懸空引用就一直住在那裡，直到發布前用手查出來。**
expect("懸空的短式引用會告警", 0, "sensor_governance_text.py",
       "secref_alias_bad", "SECTION_REF_UNRESOLVED")
expect("可解析的短式引用不誤報", 0, "sensor_governance_text.py",
       "secref_alias_ok", forbid=("SECTION_REF_UNRESOLVED", "ALIAS_TARGET_MISSING"))
# ⚠️ **這一則測的是範圍不是形式：** 引用住在 `.py` 檔頭裡。
#    `sensor_reference_integrity` 就是因為「`.py` 檔頭沒被掃過」而生——⛔ 但它只補了「檔案」引用。
expect("住在 .py 檔頭的短式引用會告警", 0, "sensor_governance_text.py",
       "secref_py", "SECTION_REF_UNRESOLVED")
# ⚠️ **圍籬修正的成對樣本。** `HANDOFF.md` 曾被報成有兩個 `## 3.`，其中一個是圍籬範本裡的一行。
#    ⛔ 範例文字不是標題。
expect("圍籬區塊內的標題不計入", 0, "sensor_governance_text.py",
       "secref_fence", forbid=("SECTION_REF_UNRESOLVED",))
expect("治理文本乾淨不誤報", 0, "sensor_governance_text.py", "gov_clean",
       forbid=("DUPLICATE_RULE_TEXT", "SECTION_REF_UNRESOLVED", "STATE_IN_SPEC_DOC"))


# ── 範圍與 T0：需要一個真的 git repo，故在系統暫存區現建 ──────────────
# ⚠️ **為什麼不用 selftest/ 底下的固定 fixture：** 本感測器讀 `git status`，
#    而在 repo 內再建一個 `.git` 會使它拒絕回報（「位於另一個 repo 之內」），
#    那正是它刻意要擋的東西。**所以測試環境必須在本 repo 之外。**
# ⚠️ 依 `governance/WORKFLOW_CONSTITUTION.md` §7.1：有分支的感測器，每條分支都要有自測走過。本節走「`write_scopes` 已設定」
#    那一條；「未設定」那一條由 `run_all_sensors.py` 每次實跑覆蓋。
# ⚠️ **基礎檔案必須先 commit。** 首版沒有 commit，於是 `governance/AGENTS.md` 與
#    `governance_config.json` 自己也算成本輪變更，**三項測試因此全錯**——
#    是自測當場抓到的，不是我看出來的。
def scope_case(desc, changed_files, want_code, needle=None, forbid=(), scopes=None, deny=None):
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_scope_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance_config.json").write_text(json.dumps({
            "write_scopes": scopes if scopes is not None else {
                "governance": ["governance", "profiles"], "_human": ["ledgers"]},
            "deny": deny if deny is not None else ["ledgers"]},
            ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
        subprocess.run(g + ["tag", "reviewed"], capture_output=True)
        for rel in changed_files:
            f = tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("changed\n", encoding="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("期望 exit " + str(want_code) + "，實得 " + str(r.returncode))
        if needle and needle not in out:
            why.append("輸出未含 " + needle)
        if banned:
            why.append("⛔ 誤報：" + "、".join(banned))
        if why:
            print("  ❌ " + desc + "（" + "；".join(why) + "）"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


scope_case("寫入 deny 範圍須 FAIL", ["ledgers/Claim_Ledger.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "profiles"]})
# 🔴 **D1 的成對樣本（v1.4.1）。**
#    ⚠️ **舊版把 `t0_docs` 在程式裡無條件併進 `denied`，於是設定關不掉 T0 的保護——
#    而 `framework_config.py` 的註解同時寫著「治理 Agent 可以維護它們」。**
#    **⛔ 下面兩項必須同時成立，缺一都代表回到了舊行為。**
scope_case("deny 含 T0 時，改 T0 須 FAIL",
           ["governance/AGENTS.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "profiles"]},
           deny=["ledgers", "governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"])
scope_case("🔴 deny ⛔ 不含 T0 時，改 T0 ⛔ 不得 FAIL（設定關得掉）",
           ["governance/AGENTS.md"], 0,
           scopes={"governance": ["governance", "profiles"]},
           deny=["ledgers"], forbid=("WRITE_TO_DENIED_PATH",))

# 🔴 **D2 的成對樣本（v1.4.1）。**
#    ⚠️ **舊版在 `write_scopes` 為空時整段跳過，⛔ 連 `deny` 一起跳過——
#    而 `PROFILE_solo.md` 要求單人專案把它留空。於是單人專案的 `deny` 從來沒有生效過。**
#    ⛔ **判準是 WARN ＋ 列名，⛔ 不是 FAIL**：主持人本人改台帳是正常的（`R-19`），
#    ⛔ 但也不得靜默（`R-22`）。
scope_case("🔴 單人專案改台帳：須列出，⛔ 但不得 FAIL",
           ["ledgers/Claim_Ledger.md"], 0, "DENIED_PATH_TOUCHED_UNATTRIBUTED",
           scopes={}, forbid=("WRITE_TO_DENIED_PATH", "WRITE_OUT_OF_SCOPE"))
scope_case("單人專案改一般檔案：⛔ 不得出現那筆 WARN",
           ["governance/SOURCES.md"], 0, scopes={},
           forbid=("DENIED_PATH_TOUCHED_UNATTRIBUTED",))
scope_case("_human 涵蓋時不誤報，但豁免筆數須印出",
           ["ledgers/Claim_Ledger.md"], 0, "_human", forbid=("WRITE_TO_DENIED_PATH",))
scope_case("範圍內的變更不誤報", ["governance/SOURCES.md"], 0,
           forbid=("WRITE_TO_DENIED_PATH", "WRITE_OUT_OF_SCOPE"))


# ── V145-E2：範圍檢查不因提交或改名而失去紀錄（8 家族驗收矩陣）────────────────
def scope_matrix_cases():
    global ok, bad
    import json, shutil, subprocess, tempfile

    def report(desc, hit, why=None):
        global ok, bad
        if hit:
            print("  ✅ " + desc); ok += 1
        else:
            print("  ❌ " + desc + ("（" + "；".join(why) + "）" if why else "")); bad += 1

    def run_s(root_dir):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(root_dir)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def setup_base(td, scopes=None, deny=None):
        root = pathlib.Path(td)
        (root / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (root / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (root / "governance_config.json").write_text(json.dumps({
            "write_scopes": scopes if scopes is not None else {"governance": ["governance"]},
            "deny": deny if deny is not None else ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        subprocess.run(["git", "-C", td, "init", "-q"], capture_output=True)
        subprocess.run(["git", "-C", td, "add", "."], capture_output=True)
        subprocess.run(["git", "-C", td, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"], capture_output=True)
        return root

    # 1. 提交後越界變更仍須檢出
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        (root / "ledgers" / "leak.md").write_text("leak\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "commit-leak"], capture_output=True)
        c, o = run_s(root)
        report("提交後越界變更仍須檢出", c == 1 and "WRITE_TO_DENIED_PATH" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 2. 提交後還原的變更仍留下歷史觸及紀錄
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        (root / "ledgers" / "history.md").write_text("orig\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base2"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        (root / "ledgers" / "history.md").write_text("modified\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-aqm", "mod"], capture_output=True)
        (root / "ledgers" / "history.md").write_text("orig\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-aqm", "revert"], capture_output=True)
        c, o = run_s(root)
        report("提交後還原的變更仍留下歷史觸及紀錄", c == 1 and "WRITE_TO_DENIED_PATH" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 3. 基準後零變更時不誤報
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        c, o = run_s(root)
        report("基準後零變更時不誤報", c == 0 and "WRITE_OUT_OF_SCOPE" not in o and "WRITE_TO_DENIED_PATH" not in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 4. 改名跨越界限（allowed至denied）須 FAIL
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "governance" / "f.md").write_text("f\n", encoding="utf-8")
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base2"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "mv", "governance/f.md", "ledgers/f.md"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "rename"], capture_output=True)
        c, o = run_s(root)
        report("改名跨越界限（allowed至denied）須 FAIL", c == 1 and "WRITE_TO_DENIED_PATH" in o and "ledgers/f.md" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 5. 改名跨越界限（denied至allowed）兩端皆納入檢查須 FAIL
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        (root / "ledgers" / "f.md").write_text("f\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base2"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "mv", "ledgers/f.md", "governance/f.md"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "rename"], capture_output=True)
        c, o = run_s(root)
        report("改名跨越界限（denied至allowed）兩端皆納入檢查須 FAIL", c == 1 and "WRITE_TO_DENIED_PATH" in o and "ledgers/f.md" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 6. 雙端皆合法之改名不誤報
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "governance" / "f1.md").write_text("f1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base2"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "mv", "governance/f1.md", "governance/f2.md"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "rename"], capture_output=True)
        c, o = run_s(root)
        report("雙端皆合法之改名不誤報", c == 0 and "WRITE_OUT_OF_SCOPE" not in o and "WRITE_TO_DENIED_PATH" not in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 7. 特殊路徑字元（中文、空格、方括號、開頭減號）正確解析不誤報
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        spec = root / "governance" / "測試 [字面] 空格 -減號.md"
        spec.write_text("spec\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "special"], capture_output=True)
        c, o = run_s(root)
        report("特殊路徑字元（中文、空格、方括號、開頭減號）正確解析不誤報", c == 0 and "WRITE_OUT_OF_SCOPE" not in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 8. 跨子樹改名移入專案能檢出目標端
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        top = pathlib.Path(tmp)
        proj = top / "sub_proj"
        sibling = top / "sibling_proj"
        proj.mkdir(); sibling.mkdir()
        (proj / "governance").mkdir(parents=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps({
            "write_scopes": {"governance": ["governance"]},
            "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        (proj / "ledgers").mkdir()
        (sibling / "out.txt").write_text("out\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "init", "-q"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "mv", "sibling_proj/out.txt", "sub_proj/ledgers/in.txt"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "cross"], capture_output=True)
        c, o = run_s(proj)
        report("跨子樹改名移入專案能檢出目標端", c == 1 and "WRITE_TO_DENIED_PATH" in o and "ledgers/in.txt" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 9. 缺 reviewed 基準時須 INCOMPLETE 且不得宣稱通過
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        c, o = run_s(root)
        report("缺 reviewed 基準時須 INCOMPLETE 且不得宣稱通過", c == 2 and "SCOPE_UNCHECKABLE" in o and "reviewed 基準不存在" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 10. reviewed 非 HEAD 祖先時須 INCOMPLETE 且不得宣稱通過
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        subprocess.run(["git", "-C", str(tmp), "checkout", "-q", "--orphan", "unrelated"], capture_output=True)
        (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "other"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        main_br = "master" if subprocess.run(["git", "-C", str(tmp), "branch", "--list", "master"], capture_output=True).stdout else "main"
        subprocess.run(["git", "-C", str(tmp), "checkout", "-q", main_br], capture_output=True)
        c, o = run_s(root)
        report("reviewed 非 HEAD 祖先時須 INCOMPLETE 且不得宣稱通過", c == 2 and "SCOPE_UNCHECKABLE" in o and "不是 HEAD 的祖先" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 11. 感測器執行保持 HEAD 與 reviewed 唯讀不變
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        hb = subprocess.run(["git", "-C", str(tmp), "rev-parse", "HEAD"], capture_output=True).stdout
        rb = subprocess.run(["git", "-C", str(tmp), "rev-parse", "reviewed"], capture_output=True).stdout
        sb = subprocess.run(["git", "-C", str(tmp), "status", "--porcelain"], capture_output=True).stdout
        c, o = run_s(root)
        ha = subprocess.run(["git", "-C", str(tmp), "rev-parse", "HEAD"], capture_output=True).stdout
        ra = subprocess.run(["git", "-C", str(tmp), "rev-parse", "reviewed"], capture_output=True).stdout
        sa = subprocess.run(["git", "-C", str(tmp), "status", "--porcelain"], capture_output=True).stdout
        unchanged = (hb == ha) and (rb == ra) and (sb == sa)
        report("感測器執行保持 HEAD 與 reviewed 唯讀不變", c == 0 and unchanged, [f"code={c}", f"unchanged={unchanged}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 12. assume-unchanged 變更內容須 INCOMPLETE
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "governance" / "tracked.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-tracked"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--assume-unchanged", "governance/tracked.md"], capture_output=True)
        (root / "governance" / "tracked.md").write_text("tampered\n", encoding="utf-8")
        content_before = (root / "governance" / "tracked.md").read_bytes()
        ls_before = subprocess.run(["git", "-C", str(tmp), "ls-files", "-v"], capture_output=True).stdout
        c, o = run_s(root)
        content_after = (root / "governance" / "tracked.md").read_bytes()
        ls_after = subprocess.run(["git", "-C", str(tmp), "ls-files", "-v"], capture_output=True).stdout
        read_only_ok = (content_before == content_after) and (ls_before == ls_after)
        report("assume-unchanged 變更內容須 INCOMPLETE", c == 2 and "TRACKED_HIDDEN_FLAGS_PRESENT" in o and "governance/tracked.md" in o and read_only_ok, [f"code={c}", f"read_only={read_only_ok}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 13. assume-unchanged 內容未改仍須 INCOMPLETE 且移除旗標後恢復
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "governance" / "tracked.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-tracked"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--assume-unchanged", "governance/tracked.md"], capture_output=True)
        c1, o1 = run_s(root)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--no-assume-unchanged", "governance/tracked.md"], capture_output=True)
        c2, o2 = run_s(root)
        pass_restored = (c2 == 0 and "TRACKED_HIDDEN_FLAGS_PRESENT" not in o2)
        report("assume-unchanged 內容未改仍須 INCOMPLETE 且移除旗標後恢復", c1 == 2 and "TRACKED_HIDDEN_FLAGS_PRESENT" in o1 and pass_restored, [f"code1={c1}", f"code2={c2}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 14. skip-worktree 變更內容與未改皆須 INCOMPLETE
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / "governance" / "sw_unmod.md").write_text("orig1\n", encoding="utf-8")
        (root / "governance" / "sw_mod.md").write_text("orig2\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-sw"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--skip-worktree", "governance/sw_unmod.md", "governance/sw_mod.md"], capture_output=True)
        (root / "governance" / "sw_mod.md").write_text("modified\n", encoding="utf-8")
        c1, o1 = run_s(root)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--no-skip-worktree", "governance/sw_unmod.md", "governance/sw_mod.md"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "checkout", "--", "governance/sw_mod.md"], capture_output=True)
        c2, o2 = run_s(root)
        report("skip-worktree 變更內容與未改皆須 INCOMPLETE", c1 == 2 and "TRACKED_HIDDEN_FLAGS_PRESENT" in o1 and c2 == 0, [f"code1={c1}", f"code2={c2}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 15. deny 內新檔被 ignore 須 INCOMPLETE
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / ".gitignore").write_text("ledgers/ignored_new.txt\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", ".gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        (root / "ledgers" / "ignored_new.txt").write_text("secret\n", encoding="utf-8")
        c, o = run_s(root)
        report("deny 內新檔被 ignore 須 INCOMPLETE", c == 2 and "IGNORED_DENIED_PATH_PRESENT" in o and "ledgers/ignored_new.txt" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 16. 既有 ignore 內檔在 deny 內須 INCOMPLETE
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp))
        (root / ".gitignore").write_text("ledgers/old_ignored.txt\n", encoding="utf-8")
        (root / "ledgers").mkdir(parents=True, exist_ok=True)
        (root / "ledgers" / "old_ignored.txt").write_text("pre-existing\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", ".gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        c, o = run_s(root)
        report("既有 ignore 內檔在 deny 內須 INCOMPLETE", c == 2 and "IGNORED_DENIED_PATH_PRESENT" in o and "ledgers/old_ignored.txt" in o, [f"code={c}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 17. scope 外檔被 ignore 須 INCOMPLETE 且普通研究附件與快取不誤報
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        root = setup_base(str(tmp), scopes={"governance": ["governance"]})
        (root / ".gitignore").write_text("unscoped/*.tmp\nscratch/\nselftest/\nresearch/*.pdf\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", ".gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "add-gitignore"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        (root / "unscoped").mkdir(parents=True, exist_ok=True)
        (root / "unscoped" / "leak.tmp").write_text("leak\n", encoding="utf-8")
        c1, o1 = run_s(root)
        unscoped_ok = (c1 == 2 and "IGNORED_OUT_OF_SCOPE_PRESENT" in o1 and "unscoped/leak.tmp" in o1)

        shutil.rmtree(root / "unscoped", ignore_errors=True)
        (root / "scratch").mkdir(parents=True, exist_ok=True)
        (root / "scratch" / "cache.bin").write_bytes(b"\x00\x01\x02")
        c2, o2 = run_s(root)
        cache_ok = (c2 == 0 and "IGNORED_OUT_OF_SCOPE_PRESENT" not in o2 and "IGNORED_DENIED_PATH_PRESENT" not in o2)

        shutil.rmtree(root / "scratch", ignore_errors=True)
        (root / "governance_config.json").write_text(json.dumps({
            "write_scopes": {},
            "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        (root / "research").mkdir(parents=True, exist_ok=True)
        (root / "research" / "paper.pdf").write_bytes(b"%PDF-1.4\n")
        c3, o3 = run_s(root)
        solo_ok = (c3 == 0 and "IGNORED_OUT_OF_SCOPE_PRESENT" not in o3 and "IGNORED_DENIED_PATH_PRESENT" not in o3)

        report("scope 外檔被 ignore 須 INCOMPLETE 且普通研究附件與快取不誤報", unscoped_ok and cache_ok and solo_ok, [f"c1={c1}", f"c2={c2}", f"c3={c3}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 18. deny 與排除衝突時須明示配置矛盾且專案外旗標與 ignore 不污染
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_matrix_"))
    try:
        top = pathlib.Path(tmp)
        proj = top / "sub_proj"
        sibling = top / "sibling_proj"
        proj.mkdir(); sibling.mkdir()
        (proj / "governance").mkdir(parents=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps({
            "write_scopes": {},
            "deny": ["ledgers", "scratch"]}, ensure_ascii=False), encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "init", "-q"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "reviewed"], capture_output=True)
        c1, o1 = run_s(proj)
        conflict_ok = (c1 == 2 and "CONFIGURATION_CONFLICT" in o1 and "scratch" in o1)

        (proj / "governance_config.json").write_text(json.dumps({
            "write_scopes": {},
            "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        (sibling / "sib_tracked.txt").write_text("sib\n", encoding="utf-8")
        (top / ".gitignore").write_text("sibling_proj/sib_ignored.txt\n", encoding="utf-8")
        (sibling / "sib_ignored.txt").write_text("ignored\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", "."], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "sib-base"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "tag", "-f", "reviewed"], capture_output=True)
        subprocess.run(["git", "-C", str(tmp), "update-index", "--assume-unchanged", "sibling_proj/sib_tracked.txt"], capture_output=True)
        (sibling / "sib_tracked.txt").write_text("sib-changed\n", encoding="utf-8")
        c2, o2 = run_s(proj)
        isolation_ok = (c2 == 0 and "TRACKED_HIDDEN_FLAGS_PRESENT" not in o2 and "IGNORED_DENIED_PATH_PRESENT" not in o2)

        report("deny 與排除衝突時須明示配置矛盾且專案外旗標與 ignore 不污染", conflict_ok and isolation_ok, [f"c1={c1}", f"c2={c2}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


scope_matrix_cases()


# ── Prompt 自足性：兩個 profile 都要有自測（`governance/WORKFLOW_CONSTITUTION.md` §7.1）────────────────────
# ⚠️ **本感測器的介面是「一個檔案」而非「一個根目錄」**，故不能用 expect()。
# 🔴 **同一份 fixture 在兩個 profile 下有不同的期望值——那正是分支測試的重點：**
#    `generic` 只查自足性；`deep-research` 另加 8 項 DR 條款表。
#    **舊版把 ② 對所有 prompt 執行，使框架自己的拆解模板永遠 FAIL。**
def prompt_case(desc, fixture, want_code, needle=None, forbid=(), profile=None):
    global ok, bad
    import subprocess
    f = FIX / "prompts" / (fixture + ".txt")
    if not f.exists():
        print("  ❌ " + desc + "（樣本不存在：" + fixture + "）"); bad += 1; return
    cmd = [PY, str(HERE / "sensor_prompt_self_contained.py"), str(f)]
    if profile:
        cmd += ["--profile", profile]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    banned = [c for c in forbid if c in out]
    why = []
    if r.returncode != want_code:
        why.append("期望 exit " + str(want_code) + "，實得 " + str(r.returncode))
    if needle and needle not in out:
        why.append("輸出未含 " + needle)
    if banned:
        why.append("⛔ 誤報：" + "、".join(banned))
    if why:
        print("  ❌ " + desc + "（" + "；".join(why) + "）"); bad += 1
    else:
        print("  ✅ " + desc); ok += 1


prompt_case("跨 prompt 指涉須 FAIL", "prompt_crossref", 1, "CROSS_PROMPT_REFERENCE")
prompt_case("未組裝的區塊佔位符須 FAIL", "prompt_unassembled", 1, "PROMPT_NOT_ASSEMBLED")
prompt_case("自足的 prompt 不誤報", "prompt_clean", 0,
            forbid=("CROSS_PROMPT_REFERENCE", "PROMPT_NOT_ASSEMBLED", "DR_CLAUSE_MISSING"))
# ⚠️ 回歸測試：⛔ 引述禁令不是違反禁令。舊版把「⛔ 不要寫『見下方』」判成跨檔指涉。
prompt_case("引述禁令不誤報，且豁免須印出", "prompt_quoted_prohibit", 0, "豁免",
            forbid=("CROSS_PROMPT_REFERENCE",))
# ⚠️ 回歸測試：內容槽是使用者的輸入位，⛔ 不是缺陷。
prompt_case("內容槽不誤報", "prompt_content_slot", 0,
            forbid=("CROSS_PROMPT_REFERENCE", "PROMPT_NOT_ASSEMBLED"))
# 🔴 分支測試：同一份 fixture，generic 通過、deep-research 不通過。
prompt_case("generic 不執行 DR 條款表", "prompt_clean", 0, "不適用 ≠ 通過",
            forbid=("DR_CLAUSE_MISSING",))
prompt_case("deep-research 執行 DR 條款表", "prompt_clean", 1, "DR_CLAUSE_MISSING",
            profile="deep-research")


# ── 模型歸屬（裁決 12：整支重寫）──────────────────────────────────
# ⚠️ **舊版在一個全新的乾淨模板上就報三筆 WARN**，因為它掃專案根目錄，
#    而根目錄的 .md 是框架模板、本來就沒有作者欄。
#    **它靠一張硬編白名單壓住自己製造的告警——那張白名單是為了補償錯的掃描範圍。**
expect("產出物無型號欄須 FAIL", 1, "sensor_model_attribution.py", "attrib_missing",
       "MODEL_ATTRIBUTION_MISSING")
expect("只寫家族名須 FAIL", 1, "sensor_model_attribution.py", "attrib_vague",
       "MODEL_ATTRIBUTION_VAGUE")
expect("寫平台名須 FAIL", 1, "sensor_model_attribution.py", "attrib_platform",
       "MODEL_ATTRIBUTION_VAGUE")
expect("具體型號不誤報", 0, "sensor_model_attribution.py", "attrib_clean",
       forbid=("MODEL_ATTRIBUTION_VAGUE", "MODEL_ATTRIBUTION_MISSING"))
# 🔴 這一項是本組最重要的：⛔ 「無法讀取」是 MODEL_IDENTITY §3.6 規則 1 指定的
#    **唯一正確輸出**。判它 FAIL 會逼下一個模型退回寫平台名，
#    而 §3.6 規則 2 說那比留空更糟。**降級的方向必須是「不知道」，不是「比較模糊的名字」。**
expect("正確宣告「無法讀取」不得判為缺陷", 0, "sensor_model_attribution.py",
       "attrib_unreadable", "MODEL_UNREADABLE_DECLARED",
       forbid=("MODEL_ATTRIBUTION_VAGUE", "MODEL_ATTRIBUTION_MISSING"))


# ── 引用完整性（裁決 14：新感測器）────────────────────────────────
# ⚠️ 觸發個案四筆，**全部發生在框架自己身上**，其中一筆是重寫另一支感測器時
#    「把舊白名單的檔名當例子寫進註解」造成的——**描述缺陷時不要實例化它。**
expect("引用不存在的檔案須 FAIL", 1, "sensor_reference_integrity.py", "ref_dangling",
       "DANGLING_FILE_REF")
# ⚠️ **自足性：本資料夾必須能被單獨複製出去使用。**
#    實測個案：說明圖曾放在倉庫根，README 以 `../docs/...` 引用——**在倉庫裡完全正常，
#    複製出去就壞掉。** 這一類依賴在原地永遠不會報錯。
expect("引用跳出本資料夾須 FAIL", 1, "sensor_reference_integrity.py", "ref_escapes",
       "REF_ESCAPES_EDITION")
expect("資料夾內的相對引用不得誤報", 0, "sensor_reference_integrity.py",
       "ref_selfcontained", forbid=("REF_ESCAPES_EDITION", "DANGLING_FILE_REF"))
expect("引用存在的檔案不誤報", 0, "sensor_reference_integrity.py", "ref_ok",
       forbid=("DANGLING_FILE_REF",))
# ⚠️ 回歸測試：格式說明裡的 `<檔名>.md` 是佔位符，⛔ 不是引用。
expect("格式佔位符不誤報", 0, "sensor_reference_integrity.py", "ref_placeholder",
       forbid=("DANGLING_FILE_REF",))
# 🔴 顯式豁免：⛔ 判準是「同一行有標記」，不是一份豁免清單；**而且必須印出來**。
expect("明示未隨附者豁免，且豁免須印出", 0, "sensor_reference_integrity.py",
       "ref_not_shipped", "REF_EXEMPTED_NOT_SHIPPED", forbid=("DANGLING_FILE_REF",))


# ── 覆蓋崩潰（裁決 20：三態，⛔ 不是兩態）────────────────────────────
# ⚠️ 觸發個案（他專案實測）：一輪對抗測試查出**五支感測器**在「比對對象變成 0」時
#    一律印 PASS——**「查無比對對象」與「比對後一致」在輸出上完全相同。**
# ⛔ 但一律升為 exit 2 是錯的：新專案第一次執行就會 INCOMPLETE，
#    而憲章 §4.1.1 對退出碼 2 的處置是「停止並回報」——與 `SETUP.md` 直接打架。
# 🔴 **首版寫成兩態（目錄存在即崩潰），實測當場踩到：框架自己有一個空的 handoffs/。**
#    → 收緊為三態。
expect("目錄不存在：只告警", 0, "sensor_self_certification.py", "collapse_absent",
       "SCAN_GLOB_MATCHES_NOTHING", forbid=("COVERAGE_COLLAPSE",))
expect("目錄剛建好還空著：只告警", 0, "sensor_self_certification.py", "collapse_created",
       "SCAN_GLOB_MATCHES_NOTHING", forbid=("COVERAGE_COLLAPSE",))
expect("目錄有東西但沒一個符合 glob：INCOMPLETE", 2, "sensor_self_certification.py",
       "collapse_empty", "COVERAGE_COLLAPSE")

# ── 條款清單同步（裁決 18）─────────────────────────────────────────
# ⚠️ **三項的分工：** ① 一個字的差別必須 FAIL；② **順序不同不得誤報**——
#    ⛔ 沒有②，下一個人會把判準改成「逐字逐序相同」，而那會對兩版現況報 FAIL；
#    ③ 定義處不見了是**查不了**，⛔ 不是通過。
expect("條款清單一字之差須 FAIL", 1, "sensor_clause_sync.py", "sync_drift",
       "SYNC_LIST_DRIFT")
expect("順序不同但集合相同不得誤報", 0, "sensor_clause_sync.py", "sync_ok",
       forbid=("SYNC_LIST_DRIFT", "SYNC_HOME_MISSING", "SYNC_NO_COPY"))
expect("定義處不存在須 INCOMPLETE", 2, "sensor_clause_sync.py", "sync_home_missing",
       "SYNC_HOME_MISSING")



# ── 崩潰必須判 INCOMPLETE，⛔ 不得判 FAIL（`R-22`、憲章 §7.4）────────
# 🔴 **實測個案：** 繁中 Windows 上兩支感測器因 `UnicodeEncodeError` 當掉，
#    **Python 未捕捉例外一律 exit 1，而 1 的意思是「找到缺陷」**——
#    於是總結印出「整套 FAIL」，而真正發生的是它們根本沒跑完。
# ⛔ **這一項用一支「一定會崩潰」的假感測器來測，⛔ 不是用真感測器**——
#    **真感測器有一天會被修好，而這個測試要測的是執行器的行為。**
def crash_case():
    import os as _os
    env = dict(_os.environ, PYTHONIOENCODING="utf-8")
    runs = [
        subprocess.run([PY, str(HERE / "_selftest_crasher.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env),
        subprocess.run([PY, "-c", "def broken(:\n    pass"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env),
    ]
    crashed = all(_is_python_crash(r.returncode, r.stderr) for r in runs)
    from check_environment import _is_python_crash as button_crash
    findings = ("finding: token SyntaxError: on line 12", "SyntaxError: quoted label",
                "quoted Traceback (most recent call last): text")
    crashed = (crashed and button_crash is _is_python_crash
               and all(not _is_python_crash(1, text) for text in findings)
               and not _is_python_crash(0, "Traceback (most recent call last):"))
    global ok, bad
    if crashed:
        print("  ✅ 執行期與解析期崩潰都判為 INCOMPLETE（不是 FAIL）"); ok += 1
    else:
        details = [(r.returncode, (r.stderr or "")[-120:]) for r in runs]
        print(f"  ❌ 執行期與解析期崩潰都必須判為 INCOMPLETE（{details}）"); bad += 1


crash_case()


# ── 升級工具⛔ 絕不能碰它不認得的資料夾 ──────────────────────
# 🔴 **使用者真正依賴的保證，⛔ 不是那份「你的資料」清單。**
#    ⚠️ 使用者會自己開資料夾——筆記、圖表、投稿版本。
#    ⛔ 那些名字不可能事先列進任何清單，而工具仍然必須放過它們。
#    **做到這件事的是「可替換清單」，不是「保護清單」**：目標只要不是框架項目，一律拒絕。
# **這個測試的存在，是為了讓那句保證變成量得出來的事實，⛔ 而不是說明書裡的一句話。**
def upgrade_case():
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_upg_"))
    try:
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance" / "AGENTS.md").write_text("# A\n", encoding="utf-8")
        shutil.copy(HERE / "checkpoint.py", root / "scripts_stub.py")  # 只要存在即可
        (root / "scripts" / "harness").mkdir(parents=True)
        shutil.copy(HERE / "checkpoint.py", root / "scripts" / "harness" / "checkpoint.py")
        # 使用者自己開的資料夾，工具從來沒聽過它
        mine = root / "my notes"
        mine.mkdir()
        (mine / "keep.md").write_text("do not lose me\n", encoding="utf-8")
        before = (mine / "keep.md").read_text(encoding="utf-8")
        # 升級來源裡剛好有一個同名資料夾
        (tmp / "project" / "_upgrade" / "my notes").mkdir(parents=True)
        (tmp / "project" / "_upgrade" / "my notes" / "keep.md").write_text(
            "REPLACED\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "my notes",
                            "--root", str(root)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env)
        after = (mine / "keep.md").read_text(encoding="utf-8")
        refused = r.returncode == 1
        intact = after == before
        if refused and intact:
            print("  ✅ 工具不認得的資料夾會被拒絕，且原封不動")
            ok += 1
        else:
            print("  ❌ 不認得的資料夾必須被拒絕且原封不動 "
                  f"（exit {r.returncode}，內容{'未變' if intact else '被覆蓋'}）")
            bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



# ── D3／D6 的成對樣本（v1.4.1）──────────────────────────────
# 🔴 **`my/MY_RULES.md` 是框架規則的副本，⛔ 而副本不能沒有守望者。**
#    ⚠️ **「同一個事實有兩份拷貝，而只有一份會被更新」是失效家族的軸二本身。**
def my_rules_case(desc, rules, my_rules, want_code, needle=None, forbid=()):
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_myrules_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance/RULES.md").write_text(rules, encoding="utf-8")
        if my_rules is not None:
            (tmp / "my/MY_RULES.md").write_text(my_rules, encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_my_rules.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("期望 exit " + str(want_code) + "，實得 " + str(r.returncode))
        if needle and needle not in out:
            why.append("輸出未含 " + needle)
        if banned:
            why.append("⛔ 誤報：" + "、".join(banned))
        if why:
            print("  ❌ " + desc + "（" + "；".join(why) + "）"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


_FW = "## A\n\n**R-05** 甲。\n**R-06** 乙。\n"
_HDR = "# 我的規則\n\n## 1. 框架規則\n\n"
_TAIL = "\n<!-- FRAMEWORK_RULES_END -->\n\n---\n\n## 2. 本專案自訂規則\n"

my_rules_case("公版有而 MY_RULES 沒有的條，須 FAIL", _FW,
              _HDR + "**R-05** 甲。\n" + _TAIL, 1, "RULE_MISSING_IN_MY")
my_rules_case("兩邊一致時⛔ 不得誤報", _FW,
              _HDR + "**R-05** 甲。\n**R-06** 乙。\n" + _TAIL, 0,
              forbid=("RULE_MISSING_IN_MY", "RULE_TEXT_DRIFT", "OVERRIDE_WITHOUT_REASON"))
my_rules_case("正文被改而未標覆寫，須 FAIL", _FW,
              _HDR + "**R-05** 甲甲甲。\n**R-06** 乙。\n" + _TAIL, 1, "RULE_TEXT_DRIFT")
# 🔴 **這一項是本感測器自己的回歸測試。**
#    ⚠️ **首版的判準是「標記那一行後面有字」，於是
#    `**R-05** [本專案覆寫] 甲。` 會通過——⛔ 因為那些字是條文本身，不是理由。**
my_rules_case("🔴 覆寫標記寫在條文那一行，須 FAIL（⛔ 不得當成有理由）", _FW,
              _HDR + "**R-05** [本專案覆寫] 甲甲。\n**R-06** 乙。\n" + _TAIL, 1,
              "RULE_TEXT_DRIFT")
my_rules_case("覆寫標記自成一行且有理由時，⛔ 不得 FAIL", _FW,
              _HDR + "**R-05** 甲甲。\n[本專案覆寫] 本專案的文本另有需求。\n"
              + "**R-06** 乙。\n" + _TAIL, 0,
              forbid=("RULE_TEXT_DRIFT", "OVERRIDE_WITHOUT_REASON"))
my_rules_case("MY_RULES 不存在時須 INCOMPLETE（⛔ 不是 PASS）", _FW, None, 2,
              "MY_RULES_MISSING")


# ── D6：未知設定鍵⛔ 不得被靜默吃掉（v1.4.1）──────────────────
# ⚠️ **舊版是 `cfg.update(data)`：`deny` 打成 `denny` ⛔ 不會有任何反應，
#    而使用者相信自己設定過了。⛔ 「靜默過濾」家族發生在設定的入口。**
def config_key_case(desc, cfg_obj, want_ok, needle=None):
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_cfgkey_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "governance_config.json").write_text(
            json.dumps(cfg_obj, ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        # ⚠️ **判準是「有沒有報未知鍵」，⛔ 不是退出碼。**
        #    🔴 **實測（本測試自己抓到）：樣本目錄沒有 git repo，
        #    於是合法設定那兩項會得到 exit 2（`SCOPE_UNCHECKABLE`）——
        #    ⛔ 那是對的行為，而以退出碼當判準會把它誤判成失敗。**
        flag = "不認得的設定鍵" in out
        good = (not flag) if want_ok else flag
        if needle and needle not in out:
            good = False
        if good:
            print("  ✅ " + desc); ok += 1
        else:
            print("  ❌ " + desc + "（exit " + str(r.returncode) + "）"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


config_key_case("🔴 打錯的設定鍵須報錯並建議正確鍵名",
                {"denny": ["ledgers"]}, False, "deny")
config_key_case("正確的設定鍵⛔ 不得報錯", {"deny": ["ledgers"]}, True)
config_key_case("底線開頭的鍵是給人看的，⛔ 不得報錯",
                {"_說明": "給人看的", "deny": ["ledgers"]}, True)


# ── 🔴 git 回報成功卻沒有輸出（v1.4.1，主持人的機器實測）──────────
# **`subprocess.run(..., capture_output=True, text=True)` 回 exit 0 而 stdout 是 `None`，
#  於是 `top.stdout.strip()` 丟 AttributeError，整支感測器崩潰。**
# ⚠️ **這個缺陷從 v1.0.0 起就在，而它到 v1.4.1 才第一次現形**——
#    🔴 **舊版在 `write_scopes` 為空時整段跳過，而單人專案一律留空：
#    ⛔ 那段程式碼在任何真實使用者的機器上從來沒有執行過。**
# ⛔ **本測試⛔ 不重現「stdout 是 None」（那要看平台），
#    它重現的是同一條分支：git 說成功而沒有給東西。⚠️ 兩者走同一個判準。**
def git_blind_case():
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_gitblind_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        shim = tmp / "bin"
        shim.mkdir()
        if sys.platform == "win32":
            (shim / "git.bat").write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        else:
            g = shim / "git"
            g.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            g.chmod(0o755)
        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   PATH=str(shim) + os.pathsep + os.environ.get("PATH", ""))
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        crashed = "Traceback" in out
        # 🔴 **⛔ 「沒有輸出」⛔ 不得被讀成「專案位於另一個 repo 之內」**——
        #    ⚠️ 那是一個讀起來合理而且錯的診斷（`pathlib.Path("")` ＝ 當前目錄）。
        wrong_dx = "另一個 repo" in out
        good = (not crashed) and (not wrong_dx) and r.returncode == 2 \
            and "SCOPE_UNCHECKABLE" in out
        if good:
            print("  ✅ 🔴 git 說成功卻沒輸出：判 INCOMPLETE，⛔ 不崩潰、⛔ 不誤診"); ok += 1
        else:
            why = []
            if crashed:
                why.append("⛔ 崩潰了")
            if wrong_dx:
                why.append("⛔ 誤診為「位於另一個 repo」")
            if r.returncode != 2:
                why.append("期望 exit 2，實得 " + str(r.returncode))
            print("  ❌ git 說成功卻沒輸出（" + "；".join(why) + "）"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


git_blind_case()


# ── 🔴 專案位於 repo 的子目錄（v1.4.1）────────────────────────
# **本框架自己的倉庫就是這個形狀：兩個版本各是一個子目錄。**
# ⚠️ **舊版一律拒絕回報並判 INCOMPLETE——⛔ 那會是一盞永遠亮著的燈（`R-19`）。**
# 🔴 **兩項必須同時成立：子樹內的變更看得到，⛔ 子樹外的變更看不到。**
#    **⛔ 只做第一項就是「對著錯誤的 repo 下判定」，那正是舊版要擋的東西。**
def subrepo_case():
    global ok, bad
    import json, shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_subrepo_"))
    try:
        proj = tmp / "edition_zh"
        (proj / "governance").mkdir(parents=True, exist_ok=True)
        (proj / "profiles").mkdir(parents=True, exist_ok=True)
        (proj / "ledgers").mkdir(parents=True, exist_ok=True)
        (tmp / "別的東西").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "profiles/PROFILE_solo.md").write_text("x\n", encoding="utf-8")
        (proj / "ledgers/Claim_Ledger.md").write_text("x\n", encoding="utf-8")
        (tmp / "別的東西/note.md").write_text("x\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps(
            {"write_scopes": {"governance": ["governance", "profiles"]},
             "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
        subprocess.run(g + ["tag", "reviewed"], capture_output=True)
        # 子樹內動一筆 deny、子樹外動一筆
        (proj / "ledgers/Claim_Ledger.md").write_text("changed\n", encoding="utf-8")
        (tmp / "別的東西/note.md").write_text("changed\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "sensor_scope_and_t0.py"), "--root", str(proj)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        saw_inside = "WRITE_TO_DENIED_PATH" in out and "ledgers/Claim_Ledger.md" in out
        saw_outside = "別的東西" in out
        refused = "SCOPE_UNCHECKABLE" in out
        if saw_inside and not saw_outside and not refused:
            print("  ✅ 🔴 專案在 repo 子目錄：看得到子樹內，⛔ 看不到子樹外"); ok += 1
        else:
            why = []
            if refused:
                why.append("⛔ 仍然拒絕回報")
            if not saw_inside:
                why.append("⛔ 子樹內的 deny 變更沒被抓到")
            if saw_outside:
                why.append("🔴 ⛔ 回報了子樹外的檔案")
            print("  ❌ 專案在 repo 子目錄（" + "；".join(why) + "）"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


subrepo_case()


# ── 🔴 `subprocess.run` 的解碼必須指定，⛔ 不得靠系統地區編碼（v1.4.1）────
#
# **實測（繁中 Windows、Python 3.14.2）：`text=True` 而沒有 `encoding` 時，
#  Python 以 `cp950` 解 git 的 UTF-8 輸出 → `UnicodeDecodeError`。**
# 🔴 **而它在 `subprocess` 的讀取執行緒裡爆掉：執行緒死了、例外不會傳出來、
#    `communicate()` 回 `None`——主程式看到的是「exit 0，而且沒有輸出」。**
# ⛔ **「成功但沒東西」與「成功且真的沒東西」在那裡長得一模一樣。**
#
# ⚠️ **本測試是**靜態檢查**：它讀 harness 的原始碼，⛔ 不執行它們。**
#    🔴 **理由：這個缺陷只在非 UTF-8 地區的機器上會發生，
#    ⛔ 而自測要在任何機器上都跑得出同一個結論。**
#    **⛔ 一個「在我的機器上測不出來」的判準，等於沒有判準。**
def subprocess_encoding_case():
    global ok, bad
    import ast as _ast
    offenders = []
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
        if f.name.startswith("_selftest"):
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ 無法解析（{e}）")
            continue
        for node in _ast.walk(tree):
            if not isinstance(node, _ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, _ast.Attribute) and fn.attr == "run"
                    and isinstance(fn.value, _ast.Name) and fn.value.id == "subprocess"):
                continue
            kw = {k.arg for k in node.keywords if k.arg}
            decodes = "text" in kw or "universal_newlines" in kw
            if decodes and "encoding" not in kw:
                offenders.append(f"{f.name}:{node.lineno}")
    if not offenders:
        # ⚠️ **分母要印出來**（`R-35`）：「0 筆」是盤點的結果，⛔ 不是沒有盤點。
        n = len([f for f in HERE.glob("*.py")])
        print(f"  ✅ 🔴 subprocess 解碼一律指定 encoding（掃了 {n} 支，0 筆例外）"); ok += 1
    else:
        print("  ❌ 有 subprocess.run 會用系統地區編碼解碼：" + "、".join(offenders)); bad += 1


subprocess_encoding_case()


# ── 🔴 reviewed 標籤只有人能移動（v1.4.4，R-H003-05）────────────
# **觸發個案（Codex 覆核，2026-09-02，在 `v1.4.2` 的 tag 上重現）：**
# `upgrade.py` 自 v1.4.1 起以 `checkpoint.py --root <root>` 呼叫，⛔ 沒有傳 `--mode`，
# 於是走 `human` 預設——**一次框架升級就把 `reviewed` 移到升級前的提交，並印「我看過了」。**
#
# 🔴 **真正的後果⛔ 不是標籤變了，是使用者的「還沒看過」被清空：**
# **一筆 AI 寫進台帳、人從未審閱的內容，因為使用者升級框架而從 `review_changes.py` 消失。**
# ⚠️ **`reviewed` 是本框架「人是唯一裁決者」這個宣稱的唯一機械載體。**
#
# ⛔ **⛔ 這一組⛔ 不是只測新工具**——**`CP-12` 測的是 `upgrade.py`，
#    因為已發布版本的缺陷在那裡，⛔ 不在任何新增的東西裡。**
def reviewed_tag_case():
    global ok, bad
    import shutil, tempfile

    def sh(root, *args):
        return subprocess.run(["git", "-C", str(root)] + list(args),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def build():
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rev_"))
        (tmp / "governance").mkdir()
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "scripts/harness").mkdir(parents=True)
        for n in ("checkpoint.py", "_common.py", "framework_config.py"):
            (tmp / "scripts/harness" / n).write_bytes((HERE / n).read_bytes())
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        sh(tmp, "add", "-A"); sh(tmp, "-c", "user.email=a@b", "-c", "user.name=t",
                                 "commit", "-qm", "base")
        return tmp

    def cp(root, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([PY, str(root / "scripts/harness/checkpoint.py"),
                               "--root", str(root)] + list(args),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env)

    def has_reviewed(root):
        return sh(root, "rev-parse", "--verify", "reviewed").returncode == 0

    def check(desc, cond, detail=""):
        global ok, bad
        if cond:
            print(f"  ✅ {desc}"); ok += 1
        else:
            print(f"  ❌ {desc}{detail}"); bad += 1

    for mode_args, label in ((["--mode", "tool", "--tool-id", "t", "--operation", "op"], "tool"),
                             (["--mode", "ai", "--role", "governance",
                               "--model", "claude-opus-5", "--topic", "x"], "ai")):
        # CP-09：原本沒有 reviewed → 之後仍然沒有
        r = build()
        (r / "note.md").write_text("dirty\n", encoding="utf-8")
        res = cp(r, *mode_args)
        check(f"🔴 CP-09／{label}：原本沒有 reviewed，程式跑完仍然沒有",
              res.returncode == 0 and not has_reviewed(r), f"（exit {res.returncode}）")
        check(f"CP-09／{label}：⛔ 不得印出人工審閱的橫幅",
              "我看過了" not in res.stdout and "looked at this" not in res.stdout)
        shutil.rmtree(r, ignore_errors=True)

        # CP-10：原本有 reviewed → 指向完全不變
        r = build()
        sh(r, "tag", "-f", "reviewed")
        before = sh(r, "rev-parse", "reviewed").stdout.strip()
        (r / "note.md").write_text("dirty\n", encoding="utf-8")
        cp(r, *mode_args)
        after = sh(r, "rev-parse", "reviewed").stdout.strip()
        check(f"🔴 CP-10／{label}：既有的 reviewed 指向⛔ 不得改變",
              before == after and before != "", f"（{before[:7]}→{after[:7]}）")
        shutil.rmtree(r, ignore_errors=True)

    # CP-11：human 模式仍然要移動——⛔ 這個區分是刻意的，不得一起關掉
    r = build()
    (r / "note.md").write_text("dirty\n", encoding="utf-8")
    cp(r)
    check("human 模式仍然移動 reviewed（⛔ 這個區分是刻意的）", has_reviewed(r))
    shutil.rmtree(r, ignore_errors=True)

    # CP-13：tool 模式缺少身分參數必須拒絕
    r = build()
    res = cp(r, "--mode", "tool")
    check("tool 模式缺 --tool-id／--operation 必須拒絕（⛔ 匿名工具與人分不開）",
          res.returncode != 0)
    shutil.rmtree(r, ignore_errors=True)

    # CP-14：🔴 `git tag -f reviewed` 會失敗，⛔ 而失敗不得被報成成功。
    #        覆核反例（Codex，2026-09-02）：專案裡存在 `reviewed/child`，
    #        Git 就完全無法建立 `reviewed`。
    r = build()
    sh(r, "tag", "reviewed/child", "HEAD")
    (r / "note.md").write_text("dirty\n", encoding="utf-8")
    res = cp(r)
    check("🔴 CP-14：reviewed 標籤建不起來時，人工檢查點⛔ 不得 exit 0",
          res.returncode != 0, f"（exit {res.returncode}）")
    check("🔴 CP-14：標籤沒動就⛔ 不得印「基準已移到」",
          "基準已移到" not in res.stdout)
    check("CP-14：必須明說標籤沒有移動", "標籤沒有移動" in res.stdout)
    check("CP-14：提交本身仍然要建立（⛔ 不得弄丟工作）",
          sh(r, "log", "--oneline", "-1").stdout.strip().count("snapshot") == 1)
    shutil.rmtree(r, ignore_errors=True)

    # CP-12：🔴 已發布缺陷的所在——upgrade.py 的呼叫形狀
    src = (HERE / "upgrade.py").read_text(encoding="utf-8")
    check("🔴 CP-12：upgrade.py 呼叫 checkpoint 時必須明確傳 --mode tool",
          src.count('"--mode", "tool"') >= 2,
          "——⛔ 沒有傳就會走 human 預設，一次升級就偽造一次人工審閱")

    # CP-15：升級器必須在替換前建立可獨立驗證的持久收據，並透過安全內建介面復原。
    check("🔴 CP-15：upgrade.py 必須印出持久收據 ID 與 checkpoint 提交",
          'MSG["receipt"].format(rid=receipt["receipt_id"], cp=cp' in src)
    check("🔴 CP-15：讀不回收據時⛔ 不得開始覆蓋",
          'MSG["no_receipt"]' in src and src.index('MSG["no_receipt"]') <
          src.index("shutil.rmtree(dst)"))
    check("🔴 CP-15：復原須使用內建收據命令，⛔ 不得叫使用者輸入 raw git checkout",
          "receipt-diff {rid}" in src and "restore {rid}" in src
          and "git checkout {cp} --" not in src)


reviewed_tag_case()


# ── 🔴 路徑排序必須跨平台一致（v1.4.4，`N-8`）──────────────────
# **實測個案（v1.4.1，主持人的機器）：`tool_my_index.py` 用 `sorted(root.rglob("*"))`
#  排 `Path` 物件產生索引，⛔ 而 `WindowsPath` 的比較會先 casefold、`PosixPath` 不會。**
# 🔴 **⇒ 同一個專案在兩台機器上產生的索引順序不同，而索引會被存起來再比對——
#    使用者第一次執行就拿到 `MY_INDEX_STALE`，⛔ 而他什麼都沒做錯。**
#
# ⚠️ **本測試是**靜態檢查**：它讀 harness 的原始碼，⛔ 不執行它們。**
#    🔴 **理由與 `subprocess_encoding_case` 相同：這個差異只在 Windows 上才顯現，
#    ⛔ 而一個「在我的機器上測不出來」的判準等於沒有判準。**
#
# ⚠️ **判準涵蓋範圍：`sorted(...)` 的第一個引數是 `.glob()`／`.rglob()` 的結果
#    （那一定是 `Path`），而該次呼叫沒有 `key=`。**
#    ⛔ **它⛔ 不涵蓋先存進變數再排序的寫法**——那是本判準的已知缺口，寫在這裡不留白。
def path_sort_case():
    global ok, bad
    import ast as _ast
    offenders = []
    scanned = 0
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
        if f.name.startswith("_selftest"):
            continue
        scanned += 1
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ 無法解析（{e}）")
            continue
        for node in _ast.walk(tree):
            if not (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                    and node.func.id == "sorted" and node.args):
                continue
            if any(k.arg == "key" for k in node.keywords):
                continue
            for sub in _ast.walk(node.args[0]):
                if (isinstance(sub, _ast.Call) and isinstance(sub.func, _ast.Attribute)
                        and sub.func.attr in ("glob", "rglob")):
                    offenders.append(f"{f.name}:{node.lineno}")
                    break
    if not offenders:
        # ⚠️ **分母要印出來**（`R-35`）：「0 筆」是盤點的結果，⛔ 不是沒有盤點。
        print(f"  ✅ 🔴 路徑排序一律指定 key（掃了 {scanned} 支，0 筆例外）"); ok += 1
    else:
        print("  ❌ 有 sorted() 直接排 Path，兩個平台順序會不同："
              + "、".join(offenders)); bad += 1

    # ⚠️ **成對的另一半：判準本身要抓得到東西，⛔ 否則它只是永遠印綠燈。**
    src = ('import pathlib\n'
           'def f(root):\n'
           '    return sorted(root.rglob("*"))\n')
    tree = _ast.parse(src)
    caught = False
    for node in _ast.walk(tree):
        if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                and node.func.id == "sorted" and node.args
                and not any(k.arg == "key" for k in node.keywords)):
            for sub in _ast.walk(node.args[0]):
                if (isinstance(sub, _ast.Call) and isinstance(sub.func, _ast.Attribute)
                        and sub.func.attr in ("glob", "rglob")):
                    caught = True
    if caught:
        print("  ✅ 判準抓得到 v1.4.1 那一行原始寫法"); ok += 1
    else:
        print("  ❌ 判準對已知的缺陷寫法靜默——⛔ 它保護不了任何東西"); bad += 1


path_sort_case()


# ── 🔴 會被雜湊的檔案，寫入端必須固定行尾（v1.4.4，`A-20260902-11`）────────
# **實測個案：`tool_pdf_to_md.py` 用 `write_text(..., encoding="utf-8")` 寫提取物，
#  ⛔ 而 Windows 上那會寫出 CRLF；`_manifest.json` 記的就是 CRLF 的雜湊。**
# **⛔ 而 `.gitattributes` 有 `*.md text eol=lf` ⇒ 提交時倉庫內正規化成 LF。**
# 🔴 **⇒ 下一次乾淨簽出，工作區變 LF，`sensor_claim_ledger.py` 每一個檔都報
#    `CORPUS_MD_MODIFIED` FAIL——⛔ 而內容一個字都沒被動過。**
# ⚠️ **三個各自正確的元件合起來產生一個假陽性，⛔ 而假陽性正是 `R-19` 說會教人忽略感測器的那一種。**
#
# ⚠️ **判準（刻意是個過近似）：一個模組只要會算雜湊（`import hashlib`），
#    它的每一個 `write_text` 都要指定 `newline=`。**
#    🔴 **⛔ 已知缺口，寫在這裡不留白：若「寫檔的模組」與「算雜湊的模組」是兩支，
#    本判準抓不到。** ⚠️ 目前框架內沒有那種切分（`tool_pdf_to_md.py` 兩件事都做），
#    **⛔ 而那是現況，不是保證。**
def hash_write_newline_case():
    global ok, bad
    import ast as _ast

    def offenders_in(src, name):
        bad_ = []
        tree = _ast.parse(src)
        if not any(isinstance(n, (_ast.Import, _ast.ImportFrom))
                   and "hashlib" in _ast.dump(n) for n in _ast.walk(tree)):
            return None                       # 不算雜湊 ⇒ 不在判準範圍內
        for node in _ast.walk(tree):
            if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute)
                    and node.func.attr == "write_text"
                    and not any(k.arg == "newline" for k in node.keywords)):
                bad_.append(f"{name}:{node.lineno}")
        return bad_

    offenders, scanned = [], 0
    for f in sorted(HERE.glob("*.py"), key=lambda p: p.as_posix()):
        try:
            hits = offenders_in(f.read_text(encoding="utf-8"), f.name)
        except SyntaxError as e:
            offenders.append(f"{f.name}: ⛔ 無法解析（{e}）"); continue
        if hits is None:
            continue
        scanned += 1
        offenders.extend(hits)
    if not offenders:
        # ⚠️ **分母要印出來**（`R-35`）：掃了幾支是盤點的結果，⛔ 不是沒有盤點。
        print(f"  ✅ 🔴 會算雜湊的模組一律固定行尾（掃了 {scanned} 支，0 筆例外）"); ok += 1
    else:
        print("  ❌ 會算雜湊的模組有 write_text 沒指定 newline：" + "、".join(offenders)); bad += 1

    # ⚠️ **成對的另一半：判準本身要抓得到東西，⛔ 否則它只是永遠印綠燈。**
    probe = ('import hashlib, pathlib\n'
             'def f(p):\n'
             '    p.write_text("x", encoding="utf-8")\n')
    caught = offenders_in(probe, "probe")
    if caught:
        print("  ✅ 判準對一個假的寫入點會報 FAIL（⛔ 反證條件成立）"); ok += 1
    else:
        print("  ❌ 判準對明顯違規沒有反應——⛔ 它是空的"); bad += 1

    # ⚠️ **第三個樣本：⛔ 不算雜湊的模組⛔ 不得被誤報**——
    #    🔴 **否則下一個人會被逼著在幾十個 fixture 寫入點補 `newline=`，
    #    而那種「為了消警報而加的參數」會把判準本身變成噪音。**
    quiet = ('import pathlib\n'
             'def f(p):\n'
             '    p.write_text("x", encoding="utf-8")\n')
    if offenders_in(quiet, "quiet") is None:
        print("  ✅ ⛔ 不算雜湊的模組⛔ 不在判準範圍內（⛔ 不製造噪音）"); ok += 1
    else:
        print("  ❌ 判準把不相干的模組也算進去了"); bad += 1


hash_write_newline_case()


# ── 🔴 版本一致性（v1.4.4，A5b）────────────────────────────
# **觸發個案：專案 D 的 `policy/` 停在 v1.3.0，而其餘五包已是 v1.4.2。**
# 🔴 **感測器全綠、自測全過，⛔ 而那個狀態是靠一次外部稽核才被發現的。**
# ⚠️ **四個分支都要驗：一致（不得誤報）／不一致（該抓到）／缺包（WARN 不是 FAIL）／
#    讀不到（INCOMPLETE 不是 PASS）。**
def version_consistency_case():
    global ok, bad
    import shutil, tempfile
    from sensor_version_consistency import survey
    cfg = {}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_ver_"))
    try:
        def build(spec):
            root = tmp / ("p%d" % len(list(tmp.iterdir())))
            for name, v in spec.items():
                d = root / name
                d.mkdir(parents=True)
                if v is not None:
                    (d / "_VERSION").write_text(v + "\n", encoding="utf-8")
            return root

        five = ["governance", "profiles", "prompts", "scripts", "docs"]

        r = build({n: "v1.4.4" for n in five})
        found, absent, unread = survey(r, cfg)
        if len(set(found.values())) == 1 and not absent and not unread:
            print("  ✅ 各包同版時不得報任何東西"); ok += 1
        else:
            print(f"  ❌ 各包同版卻有發現：{absent} {unread} {set(found.values())}"); bad += 1

        spec = {n: "v1.4.4" for n in five}; spec["profiles"] = "v1.3.0"
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if set(found.values()) == {"v1.4.4", "v1.3.0"}:
            print("  ✅ 專案 D 那個狀態（profiles 落後一版）會被抓到"); ok += 1
        else:
            print(f"  ❌ 落後一包沒有被抓到：{found}"); bad += 1

        spec = {n: "v1.4.4" for n in five if n != "docs"}
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if absent == ["docs"] and len(set(found.values())) == 1:
            print("  ✅ 缺一包是 WARN 的來源，⛔ 不得混進版本不一致"); ok += 1
        else:
            print(f"  ❌ 缺包被算成版本不一致：{absent} {found}"); bad += 1

        spec = {n: "v1.4.4" for n in five}; spec["docs"] = None
        r = build(spec)
        found, absent, unread = survey(r, cfg)
        if unread == ["docs"] and "docs" not in found:
            print("  ✅ 讀不到版本是 INCOMPLETE 的來源，⛔ 不得當成一致"); ok += 1
        else:
            print(f"  ❌ 讀不到的那一包被當成通過：{unread} {found}"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 🔴 **F-04（2026-09-02）：⛔ 不得用字串排序冒充 SemVer。**
    #    ⚠️ **實測 `sorted({'v1.9.0','v1.10.0'})[-1]` → `v1.9.0`**，⛔ 那是比較舊的那一版。
    #    **⇒ 裁決 `A4b: B`：感測器只報不一致，⛔ 不宣稱該補到哪一版。**
    import shutil as _sh, tempfile as _tf, subprocess as _sp, os as _os
    _t = pathlib.Path(_tf.mkdtemp(prefix="s2g_semver_"))
    try:
        for n, v in (("governance", "v1.10.0"), ("profiles", "v1.9.0"),
                     ("prompts", "v1.10.0"), ("scripts", "v1.10.0"), ("docs", "v1.10.0")):
            (_t / n).mkdir(parents=True)
            (_t / n / "_VERSION").write_text(v + "\n", encoding="utf-8")
        _env = dict(_os.environ, PYTHONIOENCODING="utf-8")
        _r = _sp.run([PY, str(HERE / "sensor_version_consistency.py"), "--root", str(_t)],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace", env=_env)
        _o = (_r.stdout or "") + (_r.stderr or "")
        if _r.returncode == 1 and "VERSION_MISMATCH" in _o:
            print("  ✅ v1.9.0 與 v1.10.0 並存時必須報 VERSION_MISMATCH"); ok += 1
        else:
            print(f"  ❌ 版本不一致沒有被抓到（exit {_r.returncode}）"); bad += 1
        if "補到 `v1.9.0`" not in _o and "補到 `v1.10.0`" not in _o:
            print("  ✅ 🔴 訊息⛔ 不宣稱該補到哪一版（感測器看不到升級來源）"); ok += 1
        else:
            print("  ❌ 感測器替使用者判斷了目標版本——⛔ 而字串排序會指錯方向"); bad += 1
    finally:
        _sh.rmtree(_t, ignore_errors=True)

    # 🔴 **兩份拷貝的守望者：`version_packages` 與 `FRAMEWORK_DIRS` 是同一組名字。**
    #    ⛔ **它們不同步時，會出現「升級換得了、感測器卻不比對」的那一包**——
    #    ⚠️ **而那正是 `docs/` 在 v1.3.0～v1.4.0 之間的真實狀態。**
    from framework_config import DEFAULTS
    import upgrade as _up
    if set(DEFAULTS["version_packages"]) == set(_up.FRAMEWORK_DIRS):
        print("  ✅ version_packages 與 upgrade.FRAMEWORK_DIRS 是同一組名字"); ok += 1
    else:
        a = set(DEFAULTS["version_packages"]); b = set(_up.FRAMEWORK_DIRS)
        print(f"  ❌ 兩份清單不同步：只在設定 {a - b}｜只在升級工具 {b - a}"); bad += 1


version_consistency_case()


# ── 🔴 規則同步是唯讀報告（v1.4.4）─────────────────────────────
# **v1.4.4 曾有一個 `--adopt` 會替使用者覆寫漂移的規則；覆核發現它先寫檔才印預覽、
#   無條件宣稱「檢查點還在」、且在檢查點程式明確失敗時仍寫入。⇒ 主持人裁決退回整個寫入路徑。**
#
# 🔴 **⇒ 這一支現在只做兩件事：附加缺少的條目、逐行報告漂移。**
# ⚠️ **`SYNC-03`（同時有 missing 與 drift）是 `R-H003-02` 的直接對應：
#    英文版曾經一面真的寫入、一面印「本輪沒有修改」。**
def sync_report_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_sync_"))

    def build(my_body, second_rule=True):
        root = tmp / ("p%d" % len(list(tmp.iterdir())))
        (root / "governance").mkdir(parents=True)
        (root / "my").mkdir(parents=True)
        (root / "governance/RULES.md").write_text(
            "# 規則\n\n**R-19** 公版的原句。\n\n**R-20** 另一條。\n", encoding="utf-8")
        body = my_body + ("\n\n**R-20** 另一條。" if second_rule else "")
        (root / "my/MY_RULES.md").write_text(
            "# 我的規則\n\n## 1. 框架規則\n\n" + body
            + "\n\n<!-- FRAMEWORK_RULES_END -->\n", encoding="utf-8")
        return root

    def run_(root, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([PY, str(HERE / "tool_sync_my_rules.py"),
                            "--root", str(root)] + list(args),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def check(desc, cond, detail=""):
        global ok, bad
        if cond:
            print(f"  ✅ {desc}"); ok += 1
        else:
            print(f"  ❌ {desc}{detail}"); bad += 1

    DRIFT = "**R-19** 這是舊版的句子。"
    OK19 = "**R-19** 公版的原句。"
    try:
        # SYNC-01：只有 missing → 附加，且訊息承認寫入
        r = build(OK19, second_rule=False); f = r / "my/MY_RULES.md"
        code, out = run_(r)
        check("SYNC-01：只有缺少的條目時附加，且明說沒有覆蓋任何既有文字",
              code == 0 and "**R-20** 另一條。" in f.read_text(encoding="utf-8")
              and "沒有任何既有文字被覆蓋" in out)

        # SYNC-02：只有 drift → 零寫入，印差異行與兩條路
        r = build(DRIFT); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-02：只有漂移時零寫入", code == 0 and f.read_bytes() == b)
        check("🔴 SYNC-02：印出實際差異行（`+`／`-` 開頭）",
              "    -" in out and "    +" in out)
        check("SYNC-02：告訴使用者要把 `+` 那幾行貼進去，⛔ 且不得整份取代",
              "逐字貼進" in out and "不要整份取代" in out)

        # SYNC-03：🔴 同時有 missing 與 drift（R-H003-02 的直接對應）
        r = build(DRIFT, second_rule=False); f = r / "my/MY_RULES.md"
        code, out = run_(r)
        wrote = "**R-20** 另一條。" in f.read_text(encoding="utf-8")
        check("🔴 SYNC-03：同時有 missing 與 drift 時，附加要真的發生", code == 0 and wrote)
        check("🔴 SYNC-03：⛔ 不得一面寫入一面宣稱「沒有修改」",
              wrote and "沒有東西需要附加" not in out)
        check("SYNC-03：漂移仍然要被報告", "RULE_TEXT_DRIFT" in out)

        # SYNC-05a：合法覆寫 → 不動，說「已標」
        r = build("**R-19** 我改過的。\n[本專案覆寫] 本專案的語料是逐字稿，判準要更嚴。")
        f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-05a：合法覆寫不動，訊息說「已標」",
              f.read_bytes() == b and "已標 [本專案覆寫]" in out)

        # SYNC-05b：覆寫但理由不足 → 要說感測器會 FAIL
        r = build("**R-19** 我改過的。\n[本專案覆寫] 忘了")
        f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("🔴 SYNC-05b：覆寫沒寫理由時要說感測器會 FAIL",
              f.read_bytes() == b and "OVERRIDE_WITHOUT_REASON" in out)

        # SYNC-06：都沒有 → 零寫入、誠實回報
        r = build(OK19); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r)
        check("SYNC-06：沒有東西要做時零寫入，且說明那是算過的結果",
              code == 0 and f.read_bytes() == b and "不是沒有算" in out)

        # SYNC-07：🔴 --adopt 這個旗標必須已經不存在
        r = build(DRIFT); f = r / "my/MY_RULES.md"; b = f.read_bytes()
        code, out = run_(r, "--adopt")
        check("🔴 SYNC-07：`--adopt` 已退回，必須被拒絕且零寫入",
              code != 0 and f.read_bytes() == b, f"（exit {code}）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


sync_report_case()


# ── 🔴 已退回的命令列旗標，⛔ 不得留在現行操作說明裡（v1.4.4，`R-H006-05`）──
# 🔴 **實測個案（Codex 覆核，2026-09-02）：`--adopt` 已經從 argparse 移除，
#    而三處現行說明仍然叫使用者去加那個旗標**——
#    兩版 `upgrade.py` 的升級完成訊息、兩版 `sensor_my_rules.py` 的 docstring。
# ⚠️ **當時的成對樣本是 `SYNC-07`：它證明「程式會拒絕」。**
#    ⛔ **而「程式會拒絕」與「沒有人被叫去用它」是兩件事**——
#    **一個照著說明打字的使用者，得到的是一個他不知道為什麼的錯誤。**
# 🔴 **⇒ 退回一個旗標時，要退回的是「旗標」與「說明」兩樣東西。**
#
# ⚠️ **唯一的例外是歷史敘述，而它必須自己說自己是歷史：**
#    **同一個段落內要出現 `[已退回]` 這個標記。**
#    ⛔ **不用字詞白名單**（「曾經」「原本」……）——**那種判準只要換個說法就繞過去了。**
RETIRED_FLAGS = {"--adopt": "v1.4.4"}
RETIRED_MARK = "[已退回]"
# ⚠️ 現行操作說明的範圍。⛔ `SENSOR_CHANGELOG.md` 不在內：那份**就是**歷史紀錄。
#    ⛔ `run_selftest.py` 也不在內：成對樣本必須寫得出那個旗標。
def retired_flag_case():
    global ok, bad
    root = HERE.parents[1]
    surfaces = [root / n for n in ("SETUP.md", "README.md", "INITIALIZE_PROMPT.md")]
    # ⚠️ 依 `p.name` 排序，⛔ 不得直接排 `Path`——`WindowsPath` 比較會 casefold（`N-8`）。
    surfaces += [p for p in sorted(HERE.glob("*.py"), key=lambda q: q.name)
                 if p.name != "run_selftest.py"]
    bad_hits = []
    for p in surfaces:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for para in text.split("\n\n"):
            for flag in RETIRED_FLAGS:
                if flag in para and RETIRED_MARK not in para:
                    first = next(l for l in para.splitlines() if flag in l)
                    bad_hits.append(f"{p.name}: {first.strip()[:70]}")
    if not bad_hits:
        print(f"  ✅ 🔴 SYNC-08：現行操作說明裡沒有已退回的旗標"
              f"（掃了 {len(surfaces)} 個檔案）")
        ok += 1
    else:
        print("  ❌ 🔴 SYNC-08：現行操作說明仍然叫使用者用已退回的旗標")
        for h in bad_hits:
            print(f"       {h}")
        bad += 1
    # ⚠️ **⛔ 這個掃描本身要有反證：一段沒有標記的假說明必須被抓到。**
    #    **⛔ 否則「掃過了、沒事」與「掃描壞掉了」分不出來。**
    probe = "跑 tool_sync_my_rules.py 時加 --adopt 就會自動採用公版原句。"
    caught = any(f in probe and RETIRED_MARK not in probe for f in RETIRED_FLAGS)
    if caught:
        print("  ✅ SYNC-08：掃描本身對一段假說明會報 FAIL（⛔ 反證條件成立）"); ok += 1
    else:
        print("  ❌ SYNC-08：掃描對明顯違規的假說明沒有反應——⛔ 它是空的"); bad += 1


retired_flag_case()


# ── 🔴 已退役的套件（v1.4.4，A3）─────────────────────────────
# **`policy/` 於 v1.4.4 併入 `governance/`。**
# 🔴 **一個被移出 `FRAMEWORK_DIRS` 的資料夾，在既有專案裡會變成孤兒：
#    內容永遠停在退役那一版，⛔ 而沒有任何東西會再碰它。**
# ⚠️ **升級工具⛔ 不刪使用者的東西（憲章 §6.3），但它一定要說出來**——
# **⛔ 一個沒有人知道的孤兒資料夾，與一個過期的框架文件完全一樣。**
def retired_dirs_case():
    global ok, bad
    import shutil, tempfile
    import upgrade as _up

    # ① 🔴 一個名字⛔ 不得同時「可替換」又「已退役」
    both = set(_up.RETIRED_DIRS) & set(_up.FRAMEWORK_DIRS)
    if not both:
        print("  ✅ 退役清單與可替換清單⛔ 不重疊"); ok += 1
    else:
        print(f"  ❌ {both} 同時在兩張清單上——⛔ 判定會取決於程式碼順序"); bad += 1

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_retired_"))
    try:
        # ② 該印到：資料夾還在
        root = tmp / "has"
        (root / "policy").mkdir(parents=True)
        if _up.retired_present(root) == [("policy", "v1.4.4", "governance")]:
            print("  ✅ 專案裡還有 `policy/` 時必須列出來"); ok += 1
        else:
            print("  ❌ 孤兒資料夾沒有被列出——⛔ 靜默等於沒有這個機制"); bad += 1

        # ③ ⛔ 不得誤報：資料夾不存在（＝新專案的正常狀態）
        root = tmp / "clean"
        root.mkdir()
        if _up.retired_present(root) == []:
            print("  ✅ 新專案沒有 `policy/` 時⛔ 不得出現退役提示"); ok += 1
        else:
            print("  ❌ 對一個乾淨的新專案報了退役資料夾——⛔ 常態紅燈"); bad += 1

        # ④ 空的孤兒也算：⚠️ 判準是「資料夾存在」，⛔ 不是「裡面有東西」
        root = tmp / "empty"
        (root / "policy").mkdir(parents=True)
        if _up.retired_present(root):
            print("  ✅ 空的孤兒資料夾一樣要列出（它仍讓人以為框架在維護它）"); ok += 1
        else:
            print("  ❌ 空的孤兒被當成不存在"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


retired_dirs_case()


# ── 🔴 你的文件索引（v1.4.1）──────────────────────────────
# **實測個案：某專案套用框架後就不再維護自己的檔案索引了。**
# 🔴 **關鍵性質：判準是「框架⛔ 不擁有的每一樣東西」，⛔ 不是一份要收哪些的清單——
#    所以使用者自己發明的資料夾必須自動出現在索引裡（`R-21`）。**
def my_index_case(desc, build, want_code, needle=None, forbid=(), regen=True,
                  in_index=None):
    """⚠️ `needle` 查的是**感測器的輸出**；`in_index` 查的是**產生出來的索引檔**。

    🔴 **這兩者⛔ 不是同一個東西，而首版把它們當成同一個：**
    **感測器只印統計，⛔ 不印檔案清單——於是「某個檔有沒有進索引」用 `needle` 永遠查不到。**
    ⚠️ **自測當場抓到，⛔ 而它抓到的是我寫的判準對錯了對象。**
    """
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_myindex_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (tmp / "PROJECT.md").write_text("# p\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        if regen:
            subprocess.run([PY, str(HERE / "tool_my_index.py")], cwd=str(tmp),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        build(tmp)
        r = subprocess.run([PY, str(HERE / "sensor_my_index.py"), "--root", str(tmp)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = (r.stdout or "") + (r.stderr or "")
        banned = [c for c in forbid if c in out]
        why = []
        if r.returncode != want_code:
            why.append("期望 exit " + str(want_code) + "，實得 " + str(r.returncode))
        if needle and needle not in out:
            why.append("輸出未含 " + needle)
        if in_index is not None:
            idxf = tmp / "my/MY_INDEX.md"
            body = idxf.read_text(encoding="utf-8") if idxf.is_file() else ""
            if in_index not in body:
                why.append("索引檔未含 " + in_index)
        if banned:
            why.append("⛔ 誤報：" + "、".join(banned))
        if why:
            print("  ❌ " + desc + "（" + "；".join(why) + "）"); bad += 1
        else:
            print("  ✅ " + desc); ok += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ⚠️ **`tool_my_index.py` 由 `HERE` 執行，而它以自己的位置推專案根目錄——
#    ⛔ 所以樣本不能靠 cwd。改為在樣本目錄裡放一份薄殼呼叫。**
def _gen(tmp):
    import subprocess
    (tmp / "scripts" / "harness").mkdir(parents=True, exist_ok=True)
    for f in ("tool_my_index.py", "framework_config.py", "_common.py", "upgrade.py"):
        (tmp / "scripts" / "harness" / f).write_bytes((HERE / f).read_bytes())
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    subprocess.run([PY, str(tmp / "scripts/harness/tool_my_index.py")],
                   capture_output=True, text=True,
                   encoding="utf-8", errors="replace", env=env)


my_index_case("索引還沒產生過須 INCOMPLETE（⛔ 不是 PASS）",
              lambda t: None, 2, "MY_INDEX_MISSING", regen=False)
my_index_case("剛產生的索引⛔ 不得誤報",
              _gen, 0, forbid=("MY_INDEX_STALE", "INDEX_NOTE_DANGLING",
                               "MY_INDEX_MISSING"), regen=False)
my_index_case("🔴 使用者自己開的資料夾必須出現在索引裡（⛔ 不是白名單）",
              lambda t: (_gen(t), (t / "deepresearch").mkdir(),
                         (t / "deepresearch/草稿.md").write_text("x", encoding="utf-8"),
                         _gen(t),
                         None)[-1], 0, in_index="deepresearch/草稿.md",
              forbid=("MY_INDEX_STALE",), regen=False)
my_index_case("產生之後又多了一個檔：須報過期",
              lambda t: (_gen(t),
                         (t / "新東西.md").write_text("x", encoding="utf-8"),
                         None)[-1], 1, "MY_INDEX_STALE", regen=False)
my_index_case("說明指向不存在的檔案：須 FAIL",
              lambda t: ((t / "my/MY_INDEX_notes.json").write_text(
                             '{"沒有這個檔.md": "x"}', encoding="utf-8"),
                         _gen(t), None)[-1], 1, "INDEX_NOTE_DANGLING", regen=False)
# 🔴 **成對的另一半：「不在掃描結果裡」有兩個原因，⛔ 而它們⛔ 不是同一件事。**
#    **觸發個案（專案 D，2026-09-02）：`archive/` 在排除清單內，⇒ 一個真的存在的檔案
#    被印成「那個檔案不存在」。⚠️ 而照它做（刪掉說明）⛔ 不會出錯 ⇒ 沒有人會發現它說謊。**
my_index_case("🔴 檔案在、只是被索引排除：⛔ 不得說成「檔案不存在」",
              lambda t: ((t / "git-checkpoint.log").write_text("x", encoding="utf-8"),
                         (t / "my/MY_INDEX_notes.json").write_text(
                             '{"git-checkpoint.log": "x"}', encoding="utf-8"),
                         _gen(t), None)[-1], 0, "INDEX_NOTE_EXCLUDED",
              forbid=("INDEX_NOTE_DANGLING",), regen=False)
my_index_case("說明檔壞掉：須 INCOMPLETE（⛔ 不得當成「沒有說明」）",
              lambda t: (_gen(t),
                         (t / "my/MY_INDEX_notes.json").write_text("{壞掉", encoding="utf-8"),
                         None)[-1], 2, "INDEX_NOTES_UNREADABLE", regen=False)


# ── 🔴 索引的排序必須跨平台一致（v1.4.2）─────────────────────
# **實測：`sorted(root.rglob("*"))` 排的是 `Path` 物件，而 `WindowsPath` 的比較會先 casefold。**
# **⇒ `PROJECT.md` 在 Linux 排在 `corpus/` 前面，在 Windows 排在後面。**
# 🔴 **v1.4.1 隨附的索引是在 Linux 產生的，於是它在主持人的 Windows 上跑第一次就報過期——
#    ⛔ 報的不是「索引過期」，是「你的作業系統跟產生它的那台不一樣」。**
#
# ⚠️ **⛔ 誠實說明本測試的效力範圍：它只在「檔名不分大小寫」的平台上會亮
#    （Windows、macOS 預設）。⛔ 在 Linux 上，舊寫法與新寫法的結果相同，所以它抓不到。**
# **⚠️ 保留它的理由：發布程序的第一步就在 Windows 上跑自測。**
def index_order_case():
    global ok, bad
    import shutil, subprocess, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_idxorder_"))
    try:
        (tmp / "governance").mkdir(parents=True, exist_ok=True)
        (tmp / "my").mkdir(parents=True, exist_ok=True)
        (tmp / "apple").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (tmp / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        # 🔴 `Z`（0x5A）< `a`（0x61）：字串排序時 Zed.md 在前；
        #    ⛔ 而 casefold 之後 apple/ 會跑到前面。
        (tmp / "Zed.md").write_text("x", encoding="utf-8")
        (tmp / "apple/x.md").write_text("x", encoding="utf-8")
        (tmp / "scripts" / "harness").mkdir(parents=True, exist_ok=True)
        for f in ("tool_my_index.py", "framework_config.py", "_common.py", "upgrade.py"):
            (tmp / "scripts" / "harness" / f).write_bytes((HERE / f).read_bytes())
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        subprocess.run([PY, str(tmp / "scripts/harness/tool_my_index.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
        body = (tmp / "my/MY_INDEX.md").read_text(encoding="utf-8")
        if "Zed.md" not in body or "apple/x.md" not in body:
            print("  ❌ 索引排序：兩個樣本檔沒有全部進索引"); bad += 1
        elif body.index("Zed.md") < body.index("apple/x.md"):
            print("  ✅ 🔴 索引依字串排序（跨平台一致）"); ok += 1
        else:
            print("  ❌ 索引依平台排序 —— ⛔ 同一個專案在兩台機器上會產生不同的索引"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


index_order_case()


# ── v1.4.4：升級來源與專案必須可證明為同一語言版本 ────────────
_TEST_LAUNCHERS = {
    "zh": {
        "bat": ("查看變更.bat", "檢查更新.bat", "記錄快照.bat"),
        "command": ("查看變更.command", "檢查更新.command", "記錄快照.command"),
    },
    "en": {
        "bat": ("review_changes.bat", "check_update.bat", "snapshot.bat"),
        "command": ("review_changes.command", "check_update.command", "snapshot.command"),
    },
}


def _seed_upgrade_edition(root, src, edition="zh", layout="bat"):
    for base in (root, src):
        base.mkdir(parents=True, exist_ok=True)
        for name in _TEST_LAUNCHERS[edition][layout]:
            (base / name).write_text("launcher\n", encoding="utf-8")


def upgrade_edition_case():
    global ok, bad
    import shutil, tempfile
    from upgrade import _edition_fingerprint
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_edition_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        layouts_ok = True
        for edition in ("zh", "en"):
            for layout in ("bat", "command", "both"):
                sample = tmp / f"{edition}_{layout}"
                sample.mkdir()
                names = ("bat", "command") if layout == "both" else (layout,)
                for platform in names:
                    for name in _TEST_LAUNCHERS[edition][platform]:
                        (sample / name).write_text("x\n", encoding="utf-8")
                layouts_ok = layouts_ok and _edition_fingerprint(sample)[0] == edition
        if layouts_ok:
            print("  ✅ 中英 Windows-only／macOS-only／雙平台簽名皆可唯一辨認"); ok += 1
        else:
            print("  ❌ 合法語言版本簽名無法穩定辨認"); bad += 1

        custom = tmp / "custom"
        _seed_upgrade_edition(custom, custom, "zh", "bat")
        (custom / "研究工具.bat").write_text("x\n", encoding="utf-8")
        (custom / "my.command").write_text("x\n", encoding="utf-8")
        if _edition_fingerprint(custom)[0] == "zh":
            print("  ✅ 名字不同的自建 .bat／.command 不參與語言判定"
                  "（⛔ 撞名的會參與，⇒ 見下一項）"); ok += 1
        else:
            print("  ❌ 自建啟動器污染了語言版本判定"); bad += 1

        cases = []
        for label in ("cross", "mixed", "project_missing", "source_missing"):
            root = tmp / label / "project"
            src = root / "_upgrade"
            (root / "governance").mkdir(parents=True)
            (root / "governance/AGENTS.md").write_text("# OLD\n", encoding="utf-8")
            (src / "governance").mkdir(parents=True)
            (src / "governance/AGENTS.md").write_text("# NEW\n", encoding="utf-8")
            if label == "cross":
                _seed_upgrade_edition(root, root, "zh", "bat")
                _seed_upgrade_edition(src, src, "en", "bat")
            elif label == "mixed":
                _seed_upgrade_edition(root, src, "zh", "bat")
                (root / _TEST_LAUNCHERS["en"]["bat"][0]).write_text("x\n", encoding="utf-8")
            elif label == "project_missing":
                _seed_upgrade_edition(src, src, "zh", "bat")
            else:
                _seed_upgrade_edition(root, root, "zh", "bat")
            before = (root / "governance/AGENTS.md").read_bytes()
            result = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "governance",
                                     "--root", str(root)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", env=env)
            cases.append(result.returncode == 1
                         and (root / "governance/AGENTS.md").read_bytes() == before
                         and not (root / ".git").exists())
        if all(cases):
            print("  ✅ 跨語言、混合、來源或專案缺簽名皆在檢查點前零寫入拒絕"); ok += 1
        else:
            print("  ❌ 語言相容閘門沒有在所有不確定狀態下 fail closed"); bad += 1

        # 🔴 **成對樣本：被擋下時，訊息必須指名它看到的那個檔案。**
        #    ⚠️ **判定只讀這十二個檔名，⛔ 不看是誰放的**——⇒ 一個專案自建的
        #    同名檔案會讓合法專案被判「混合」而整次拒絕。**那是 fail-closed，
        #    ⛔ 而使用者⛔ 無從得知是哪一個檔案造成的。**
        #    **⇒ 本樣本的判準⛔ 不是「有沒有擋」，是「擋的時候有沒有說出原因」。**
        collide = tmp / "collide" / "project"
        csrc = collide / "_upgrade"
        (collide / "governance").mkdir(parents=True)
        (collide / "governance/AGENTS.md").write_text("# OLD\n", encoding="utf-8")
        (csrc / "governance").mkdir(parents=True)
        (csrc / "governance/AGENTS.md").write_text("# NEW\n", encoding="utf-8")
        _seed_upgrade_edition(collide, csrc, "zh", "bat")
        offender = _TEST_LAUNCHERS["en"]["bat"][2]
        (collide / offender).write_text("x\n", encoding="utf-8")
        before = (collide / "governance/AGENTS.md").read_bytes()
        r = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "governance",
                            "--root", str(collide)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        told = offender in ((r.stdout or "") + (r.stderr or ""))
        if (r.returncode == 1 and told
                and (collide / "governance/AGENTS.md").read_bytes() == before):
            print(f"  ✅ 撞名的自建啟動器被擋下時，訊息指名了 `{offender}`"); ok += 1
        else:
            print("  ❌ 撞名被擋下，⛔ 而訊息沒有指名那個檔案 ⇒ 使用者無從修"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：根層 glob 與平台啟動器 ───────────────────────────────
def root_glob_platform_case():
    global ok, bad
    import shutil, tempfile
    from _common import _glob_dir, dead_glob_findings
    from framework_config import active_launcher_globs
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rootglob_"))
    try:
        root = tmp / "project"
        root.mkdir()
        (tmp / "sibling.command").write_text("x", encoding="utf-8")
        findings = dead_glob_findings(["*.command"], "launcher_globs", root)
        bounded = _glob_dir(root, "*.command") == root
        no_parent_false_alarm = all(f[1] != "COVERAGE_COLLAPSE" for f in findings)
        if bounded and no_parent_false_alarm:
            print("  ✅ 根層 glob 留在專案根目錄，不受相鄰專案檔案污染"); ok += 1
        else:
            print("  ❌ 根層 glob 越到父目錄，會把相鄰專案誤判成覆蓋崩潰"); bad += 1

        (root / "_upgrade/nested").mkdir(parents=True)
        (root / "_upgrade/nested/readme.txt").write_text("x", encoding="utf-8")
        (root / "_upgrade/nested/check.command").write_text("x", encoding="utf-8")
        excluded_findings = dead_glob_findings(
            ["*.txt", "*.command"], "excluded_dirs", root)
        if all(f[1] != "COVERAGE_COLLAPSE" for f in excluded_findings):
            print("  ✅ 覆蓋崩潰的遞迴檢查也排除 _upgrade（文字與啟動器）"); ok += 1
        else:
            print("  ❌ _upgrade 內的檔案仍會製造假的覆蓋崩潰"); bad += 1

        (root / "notes").mkdir()
        (root / "notes/real.txt").write_text("x", encoding="utf-8")
        real_findings = dead_glob_findings(["*.txt"], "real_child", root)
        if any(f[1] == "COVERAGE_COLLAPSE" for f in real_findings):
            print("  ✅ 非排除目錄確有同副檔名檔時仍判為覆蓋崩潰"); ok += 1
        else:
            print("  ❌ 排除修正過寬，連真正的覆蓋崩潰也放過了"); bad += 1

        (root / "check.bat").write_text("x", encoding="utf-8")
        globs = ["*.bat", "*.command"]
        win = active_launcher_globs(globs, root, "win32")
        if win == ["*.bat"]:
            print("  ✅ Windows 專案沒有 .command 不得告警"); ok += 1
        else:
            print(f"  ❌ Windows 外平台啟動器被誤列為必需：{win}"); bad += 1
        (root / "check.bat").unlink()
        (root / "check.command").write_text("x", encoding="utf-8")
        mac = active_launcher_globs(globs, root, "darwin")
        if mac == ["*.command"]:
            print("  ✅ macOS 專案沒有 .bat 不得告警"); ok += 1
        else:
            print(f"  ❌ macOS 外平台啟動器被誤列為必需：{mac}"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：索引工具參數先驗證，才允許寫檔 ───────────────────────
def my_index_cli_safety_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_idxcli_"))
    try:
        (tmp / "my").mkdir()
        idx = tmp / "my/MY_INDEX.md"
        idx.write_text("SENTINEL\n", encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        help_run = subprocess.run([PY, str(HERE / "tool_my_index.py"), "--root", str(tmp), "--help"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", env=env)
        help_safe = help_run.returncode == 0 and idx.read_text(encoding="utf-8") == "SENTINEL\n"
        if help_safe:
            print("  ✅ tool_my_index.py --help 不寫入索引"); ok += 1
        else:
            print("  ❌ --help 在顯示說明前改寫了索引"); bad += 1
        unknown = subprocess.run([PY, str(HERE / "tool_my_index.py"), "--root", str(tmp), "--not-an-option"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        unknown_safe = unknown.returncode == 2 and idx.read_text(encoding="utf-8") == "SENTINEL\n"
        if unknown_safe:
            print("  ✅ tool_my_index.py 未知參數退出 2 且不寫入索引"); ok += 1
        else:
            print(f"  ❌ 未知參數必須拒絕且不寫檔（exit {unknown.returncode}）"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：規則同步工具必須先解析參數，且只寫指定根目錄 ────────
def sync_my_rules_cli_safety_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_rulescli_"))
    try:
        a_root, b_root = tmp / "A", tmp / "B"
        for project in (a_root, b_root):
            (project / "governance").mkdir(parents=True)
            (project / "my").mkdir()
        rules = "**R-01** 第一條。\n\n**R-02** 第二條。\n"
        a_my = "**R-01** 第一條。\n\n<!-- FRAMEWORK_RULES_END -->\n"
        b_my = rules + "\n<!-- FRAMEWORK_RULES_END -->\n"
        for project in (a_root, b_root):
            (project / "governance/RULES.md").write_text(rules, encoding="utf-8")
        (a_root / "my/MY_RULES.md").write_text(a_my, encoding="utf-8")
        (b_root / "my/MY_RULES.md").write_text(b_my, encoding="utf-8")
        harness = b_root / "scripts/harness"
        harness.mkdir(parents=True)
        for name in ("tool_sync_my_rules.py", "sensor_my_rules.py", "_common.py",
                     "framework_config.py"):
            (harness / name).write_bytes((HERE / name).read_bytes())
        tool = harness / "tool_sync_my_rules.py"
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        before_a = (a_root / "my/MY_RULES.md").read_bytes()
        before_b = (b_root / "my/MY_RULES.md").read_bytes()

        help_run = subprocess.run([PY, str(tool), "--root", str(a_root), "--help"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", env=env)
        if (help_run.returncode == 0
                and (a_root / "my/MY_RULES.md").read_bytes() == before_a
                and (b_root / "my/MY_RULES.md").read_bytes() == before_b):
            print("  ✅ tool_sync_my_rules.py --help 不寫任何專案"); ok += 1
        else:
            print("  ❌ 規則同步工具 --help 觸發了寫入"); bad += 1

        unknown = subprocess.run([PY, str(tool), "--root", str(a_root), "--not-an-option"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        if (unknown.returncode == 2
                and (a_root / "my/MY_RULES.md").read_bytes() == before_a
                and (b_root / "my/MY_RULES.md").read_bytes() == before_b):
            print("  ✅ 規則同步工具未知參數退出 2 且零寫入"); ok += 1
        else:
            print(f"  ❌ 規則同步工具未知參數未安全拒絕（exit {unknown.returncode}）"); bad += 1

        rooted = subprocess.run([PY, str(tool), "--root", str(a_root)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        after_a = (a_root / "my/MY_RULES.md").read_text(encoding="utf-8")
        after_b = (b_root / "my/MY_RULES.md").read_bytes()
        if rooted.returncode == 0 and "**R-02** 第二條。" in after_a and after_b == before_b:
            print("  ✅ --root A 只補 A，不會改工具所在的 B"); ok += 1
        else:
            print(f"  ❌ --root 沒有精確限定寫入專案（exit {rooted.returncode}）"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：暫存檔例外必須綁定套件與精確相對路徑 ──────────────
def upgrade_transient_scope_case():
    global ok, bad
    import shutil, tempfile
    from upgrade import target_only_files
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_transient_"))
    try:
        cur, new = tmp / "current", tmp / "new"
        (cur / "harness").mkdir(parents=True)
        (cur / "custom").mkdir()
        (cur / "empty-owned").mkdir()
        new.mkdir()
        (cur / "harness/harness_status.json").write_text("framework", encoding="utf-8")
        (cur / "custom/harness_status.json").write_text("project", encoding="utf-8")
        scripts_only = target_only_files(cur, new, "scripts")
        if "harness/harness_status.json" not in scripts_only:
            print("  ✅ scripts/harness/harness_status.json 是精確暫存例外"); ok += 1
        else:
            print("  ❌ 框架自己的 harness 狀態檔被當成專案檔"); bad += 1
        if "custom/harness_status.json" in scripts_only:
            print("  ✅ scripts 其他位置的同名檔仍會阻擋替換"); ok += 1
        else:
            print("  ❌ 只看檔名的例外會靜默刪除專案檔"); bad += 1
        profiles_only = target_only_files(cur, new, "profiles")
        if "harness/harness_status.json" in profiles_only:
            print("  ✅ 非 scripts 套件的同路徑檔也不享有例外"); ok += 1
        else:
            print("  ❌ 暫存例外未綁定 scripts 套件"); bad += 1
        if ("harness/harness_status.json" not in scripts_only
                and "custom/harness_status.json" in scripts_only
                and "harness/harness_status.json" in profiles_only):
            print("  ✅ UPG-REC-10：暫存例外綁定精確套件與路徑"); ok += 1
        else:
            print("  ❌ UPG-REC-10：暫存例外逸出精確範圍"); bad += 1
        if "empty-owned/" in scripts_only:
            print("  ✅ UPG-REC-11：目標端獨有空目錄會阻擋整包替換"); ok += 1
        else:
            print("  ❌ UPG-REC-11：整包替換會靜默刪除空目錄"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：整包替換前攔住 target-only 檔 ─────────────────────────
def upgrade_target_only_case():
    global ok, bad
    import shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_targetonly_"))
    try:
        portable = tmp / "download" / "scripts" / "harness"
        portable.mkdir(parents=True)
        for name in ("upgrade.py", "_common.py", "framework_config.py"):
            (portable / name).write_bytes((HERE / name).read_bytes())
        portable_checkpoint = portable / "checkpoint.py"
        portable_checkpoint.write_text(
            'CHECKPOINT_TOOL_API = "spark2groundwork-checkpoint-tool-v1"\n'
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('checkpoint_called').write_text('yes')\n"
            "sys.exit(0)\n", encoding="utf-8")
        upgrade_tool = portable / "upgrade.py"
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        checkpoint_body = (
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('checkpoint_called').write_text('yes')\n"
            "sys.exit(0)\n")
        (root / "scripts/harness/checkpoint.py").write_text(checkpoint_body, encoding="utf-8")
        (root / "_upgrade/scripts/harness").mkdir(parents=True)
        (root / "_upgrade/scripts/harness/checkpoint.py").write_text(checkpoint_body, encoding="utf-8")
        (root / "prompts").mkdir()
        (root / "prompts/base.txt").write_text("old\n", encoding="utf-8")
        custom = root / "prompts/TEMPLATE_decompose.txt"
        custom.write_text("MY IDEA\n", encoding="utf-8")
        (root / "_upgrade/prompts").mkdir(parents=True)
        (root / "_upgrade/prompts/base.txt").write_text("new\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade",
                              layout="command" if sys.platform == "darwin" else "bat")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        args = [PY, str(upgrade_tool), "apply", "prompts", "--root", str(root)]
        blocked = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        untouched = (custom.read_text(encoding="utf-8") == "MY IDEA\n"
                     and (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n")
        before_checkpoint = not (root / "checkpoint_called").exists()
        listed = "prompts/TEMPLATE_decompose.txt" in ((blocked.stdout or "") + (blocked.stderr or ""))
        if blocked.returncode == 1 and untouched and before_checkpoint and listed:
            print("  ✅ target-only 檔會在檢查點與替換前被列名阻擋"); ok += 1
        else:
            print("  ❌ target-only 阻擋不完整（必須列名、零寫入、尚未建檢查點）"); bad += 1

        idea = root / "第一個想法.md"
        custom.replace(idea)

        # 🔴 **收據閘門（v1.4.4，`R-H006-02`）：檢查點說成功，⛔ 而還原點指不出來。**
        #    ⚠️ **這裡的替身檢查點只 exit 0，⛔ 沒有建立任何 git 歷史**——
        #    **⇒ `upgrade.py` 讀不回 pre-image 的提交編號。**
        #    🔴 **⛔ 這種情況不得覆蓋：一個說不出還原點在哪的還原點，不是還原點。**
        #    ⚠️ **成對樣本的另一半就在下面：補上 git 之後，同一個指令必須成功。**
        norepo = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        kept = (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n"
        if norepo.returncode == 2 and kept:
            print("  ✅ 🔴 讀不回檢查點編號時⛔ 不覆蓋（收據閘門）"); ok += 1
        else:
            print(f"  ❌ 🔴 收據閘門失效：exit {norepo.returncode}、"
                  f"內容{'未' if kept else '已'}被覆蓋"); bad += 1

        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=t",
                        "commit", "-qm", "base"], capture_output=True)

        # 從這裡起換成下載包內真正的同版 peer；專案內版本刻意保持不相容。
        portable_checkpoint.write_bytes((HERE / "checkpoint.py").read_bytes())

        # 目前專案可能仍是舊 checkpoint CLI；bootstrap 必須使用下載包內 v1.4.4 的同伴程式。
        (root / "checkpoint_called").unlink(missing_ok=True)
        (root / "scripts/harness/checkpoint.py").write_text(
            "import sys\nsys.exit(9)\n", encoding="utf-8")

        applied = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        replaced = (root / "prompts/base.txt").read_text(encoding="utf-8") == "new\n"
        survived = idea.read_text(encoding="utf-8") == "MY IDEA\n"
        if applied.returncode == 0 and replaced and survived and not (root / "checkpoint_called").exists():
            print("  ✅ 舊專案工具拒絕時仍由下載版 checkpoint 完成 bootstrap，根目錄想法原封不動"); ok += 1
        else:
            detail = ((applied.stdout or "") + (applied.stderr or "")).strip().replace("\n", " | ")
            print(f"  ❌ 搬出專案檔後的整包替換失敗"
                  f"（exit {applied.returncode}：{detail}）"); bad += 1
        # 🔴 畫面上必須交出持久收據與安全復原介面。
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace").stdout.strip()
        out_all = (applied.stdout or "") + (applied.stderr or "")
        if head and head in out_all and "收據：    upg-" in out_all and "receipt-diff" in out_all:
            print("  ✅ 🔴 升級成功訊息交出持久還原收據與安全介面"); ok += 1
        else:
            print("  ❌ 🔴 升級成功訊息沒有交出可用的還原點"); bad += 1

        import re
        found = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}", out_all)
        restored = subprocess.run([PY, str(upgrade_tool), "restore",
                                   found.group(0) if found else "missing", "prompts/base.txt",
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        if (restored.returncode == 0
                and (root / "prompts/base.txt").read_text(encoding="utf-8") == "old\n"
                and "upg-" in ((restored.stdout or "") + (restored.stderr or ""))):
            print("  ✅ 舊專案＋下載版＋非 scripts 套件可 restore，且先建立反向收據"); ok += 1
        else:
            print(f"  ❌ bootstrap 後 restore 未使用下載版 peer 安全往返（exit {restored.returncode}）"); bad += 1

        foreign = "記錄快照.bat" if sys.platform == "darwin" else "記錄快照.command"
        (root / "_upgrade" / foreign).write_text("foreign launcher\n", encoding="utf-8")
        routine = subprocess.run([PY, str(upgrade_tool), "diff", "--root", str(root)],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=env)
        explicit = subprocess.run([PY, str(upgrade_tool), "apply", foreign,
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        omitted = foreign not in ((routine.stdout or "") + (routine.stderr or ""))
        installed = (root / foreign).read_text(encoding="utf-8") == "foreign launcher\n"
        if routine.returncode == 0 and omitted and explicit.returncode == 0 and installed:
            print("  ✅ 例行 diff 略過缺少的外平台啟動器，但明確 apply 仍可安裝"); ok += 1
        else:
            print("  ❌ 外平台啟動器的例行略過或明確套用出口失效"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- v1.4.4: durable upgrade receipts must prove and recover the exact pre-image --
def upgrade_receipt_case():
    global ok, bad
    import json, re, shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_receipts_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    def git(root, *args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    def build(name, ignored=False):
        root = tmp / name
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        # A minimal tool-mode checkpoint: commit the worktree, never move `reviewed`.
        (root / "scripts/harness/checkpoint.py").write_text(
            "import pathlib, subprocess, sys\n"
            "r=pathlib.Path(__file__).resolve().parents[2]\n"
            "a=subprocess.run(['git','-C',str(r),'add','-A'])\n"
            "if a.returncode: sys.exit(a.returncode)\n"
            "d=subprocess.run(['git','-C',str(r),'diff','--cached','--quiet'])\n"
            "if d.returncode==1:\n"
            " p=subprocess.run(['git','-C',str(r),'-c','user.email=a@b','-c','user.name=t','commit','-qm','tool checkpoint'])\n"
            " sys.exit(p.returncode)\n"
            "sys.exit(0 if d.returncode==0 else d.returncode)\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "_upgrade/docs").mkdir(parents=True)
        (root / "_upgrade/docs/fig.svg").write_text("NEW\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade")
        if ignored:
            (root / ".gitignore").write_text("/docs/fig.svg\n", encoding="utf-8")
        else:
            (root / "docs/fig.svg").write_text("OLD\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        git(root, "add", "-A")
        git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "base")
        if ignored:
            (root / "docs/fig.svg").write_text("IGNORED HAND EDIT\n", encoding="utf-8")
        return root

    def apply(root):
        return subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "docs",
                               "--root", str(root)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env)

    def receipt_id(result):
        m = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}",
                      (result.stdout or "") + (result.stderr or ""))
        return m.group(0) if m else None

    try:
        ignored = build("ignored", ignored=True)
        result = apply(ignored)
        kept = (ignored / "docs/fig.svg").read_text(encoding="utf-8") == "IGNORED HAND EDIT\n"
        if result.returncode == 2 and kept and receipt_id(result) is None:
            print("  ✅ UPG-REC-03：被 ignore 的同路徑手改會阻擋替換"); ok += 1
        else:
            print("  ❌ UPG-REC-03：被 ignore 的同路徑內容未受保護"); bad += 1

        hidden_ok = True
        for flag, clear in (("--assume-unchanged", "--no-assume-unchanged"),
                            ("--skip-worktree", "--no-skip-worktree")):
            root = build(flag.lstrip("-").replace("-", "_"))
            git(root, "update-index", flag, "--", "docs/fig.svg")
            (root / "docs/fig.svg").write_text(f"HIDDEN {flag}\n", encoding="utf-8")
            result = apply(root)
            hidden_ok = hidden_ok and result.returncode == 2 and \
                (root / "docs/fig.svg").read_text(encoding="utf-8") == f"HIDDEN {flag}\n"
            git(root, "update-index", clear, "--", "docs/fig.svg")
        if hidden_ok:
            print("  ✅ UPG-REC-04：assume-unchanged 與 skip-worktree 無法藏起 pre-image"); ok += 1
        else:
            print("  ❌ UPG-REC-04：index 旗標繞過了 pre-image 驗證"); bad += 1

        root = build("roundtrip")
        reviewed = git(root, "rev-parse", "HEAD").stdout.strip()
        git(root, "tag", "reviewed", reviewed)
        (root / "docs/fig.svg").write_text("HAND EDIT\n", encoding="utf-8")
        result = apply(root)
        rid = receipt_id(result)
        listed = subprocess.run([PY, str(HERE / "upgrade.py"), "receipts", "--root", str(root)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env)
        ref = git(root, "rev-parse", f"refs/spark2groundwork/restore/{rid}") if rid else None
        store_raw = git(root, "rev-parse", "--git-path", "spark2groundwork/receipts").stdout.strip()
        store = pathlib.Path(store_raw)
        if not store.is_absolute():
            store = root / store
        manifest = store / f"{rid}.json" if rid else store / "missing.json"
        manifest_data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
        durable = (result.returncode == 0 and rid and manifest.is_file()
                   and ref.returncode == 0 and rid in listed.stdout
                   and manifest_data["ref"].endswith(rid))
        if durable:
            print("  ✅ UPG-REC-05：apply 留下可驗證的 manifest 與 private Git ref"); ok += 1
        else:
            print("  ❌ UPG-REC-05：收據未持久保存或無法列出"); bad += 1

        captured = git(root, "show", f"refs/spark2groundwork/restore/{rid}:docs/fig.svg") \
            if rid else None
        if captured and captured.returncode == 0 and captured.stdout == "HAND EDIT\n":
            print("  ✅ UPG-REC-08：正常受追蹤的手改在 apply 前已被保存"); ok += 1
        else:
            print("  ❌ UPG-REC-08：受追蹤的 pre-image 未被保存"); bad += 1

        diffed = subprocess.run([PY, str(HERE / "upgrade.py"), "receipt-diff", rid or "missing",
                                 "docs/fig.svg", "--root", str(root)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", env=env)
        restored = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                   "docs/fig.svg", "--root", str(root)], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", env=env)
        receipt_count = len(list(store.glob("*.json")))
        roundtrip = (diffed.returncode == 0 and "-HAND EDIT" in diffed.stdout and "+NEW" in diffed.stdout
                     and restored.returncode == 0
                     and (root / "docs/fig.svg").read_text(encoding="utf-8") == "HAND EDIT\n"
                     and receipt_count == 2
                     and git(root, "rev-parse", "refs/tags/reviewed").stdout.strip() == reviewed
                     and git(root, "diff", "--cached", "--quiet").returncode == 0)
        if roundtrip:
            print("  ✅ UPG-REC-06：差異與單檔還原成立，且有反向收據、reviewed 不動"); ok += 1
        else:
            detail = (f"diff={diffed.returncode}, restore={restored.returncode}, "
                      f"receipts={receipt_count}, current={repr((root / 'docs/fig.svg').read_text(encoding='utf-8'))}, "
                      f"diff_out={repr(diffed.stdout)}, restore_out={repr(restored.stdout)}, "
                      f"restore_err={repr(restored.stderr)}")
            print(f"  ❌ UPG-REC-06：receipt diff／restore 往返不安全（{detail}）"); bad += 1

        before_count = len(list(store.glob("*.json")))
        outside = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                  "../outside", "--root", str(root)], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", env=env)
        (root / "docs/fig.svg").unlink()
        missing = subprocess.run([PY, str(HERE / "upgrade.py"), "restore", rid or "missing",
                                  "docs/fig.svg", "--root", str(root)], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", env=env)
        after_count = len(list(store.glob("*.json")))
        if outside.returncode == 1 and missing.returncode == 1 and before_count == after_count:
            print("  ✅ UPG-REC-07：路徑逃逸與目前檔案缺少時拒絕還原，且零收據寫入"); ok += 1
        else:
            print("  ❌ UPG-REC-07：restore 路徑限制或 fail-closed 行為退化"); bad += 1

        crlf = build("crlf")
        (crlf / ".gitattributes").write_text("docs/*.svg text eol=lf\n", encoding="utf-8")
        git(crlf, "add", ".gitattributes")
        git(crlf, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "attributes")
        (crlf / "docs/fig.svg").write_bytes(b"OLD\r\n")
        normalized = apply(crlf)
        if (normalized.returncode == 0
                and (crlf / "docs/fig.svg").read_text(encoding="utf-8") == "NEW\n"):
            print("  ✅ UPG-REC-09：CRLF 正規化依 Git 語意判斷，不會誤擋"); ok += 1
        else:
            print("  ❌ UPG-REC-09：只有位元組不同的 CRLF 造成誤擋"); bad += 1

        if manifest.is_file():
            tampered = json.loads(manifest.read_text(encoding="utf-8"))
            tampered["files"][0]["blob"] = "0" * 40
            manifest.write_text(json.dumps(tampered), encoding="utf-8")
        invalid = subprocess.run([PY, str(HERE / "upgrade.py"), "receipt-diff", rid or "missing",
                                  "--root", str(root)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", env=env)
        if invalid.returncode == 2:
            print("  ✅ UPG-REC-12：遭竄改的 manifest 在使用前被拒絕"); ok += 1
        else:
            print("  ❌ UPG-REC-12：收據完整性檢查接受了遭竄改的 manifest"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── v1.4.4：找不到相符 checkpoint peer 時，restore 必須零寫入拒絕 ──
def upgrade_peer_fail_case():
    global ok, bad
    import re, shutil, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="s2g_peerfail_"))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        root = tmp / "project"
        (root / "governance").mkdir(parents=True)
        (root / "governance/AGENTS.md").write_text("# A\n", encoding="utf-8")
        (root / "governance/WORKFLOW_CONSTITUTION.md").write_text("# W\n", encoding="utf-8")
        (root / "scripts/harness").mkdir(parents=True)
        # 舊版程式若被執行就會留下痕跡；它刻意沒有相容 API 標記。
        (root / "scripts/harness/checkpoint.py").write_text(
            "import pathlib, sys\n"
            "r=pathlib.Path(sys.argv[sys.argv.index('--root')+1])\n"
            "r.joinpath('UNEXPECTED').write_text('x')\n",
            encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs/fig.svg").write_text("OLD\n", encoding="utf-8")
        (root / "_upgrade/docs").mkdir(parents=True)
        (root / "_upgrade/docs/fig.svg").write_text("NEW\n", encoding="utf-8")
        _seed_upgrade_edition(root, root / "_upgrade")
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=t",
                        "commit", "-qm", "base"], capture_output=True)
        applied = subprocess.run([PY, str(HERE / "upgrade.py"), "apply", "docs",
                                  "--root", str(root)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", env=env)
        found = re.search(r"upg-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}",
                          (applied.stdout or "") + (applied.stderr or ""))
        portable = tmp / "standalone"
        portable.mkdir()
        for name in ("upgrade.py", "_common.py", "framework_config.py"):
            (portable / name).write_bytes((HERE / name).read_bytes())
        store_raw = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path",
                                    "spark2groundwork/receipts"], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace").stdout.strip()
        store = pathlib.Path(store_raw)
        if not store.is_absolute():
            store = root / store
        before_count = len(list(store.glob("*.json")))
        before = (root / "docs/fig.svg").read_bytes()
        restored = subprocess.run([PY, str(portable / "upgrade.py"), "restore",
                                   found.group(0) if found else "missing", "docs/fig.svg",
                                   "--root", str(root)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env)
        out = (restored.stdout or "") + (restored.stderr or "")
        safe = (applied.returncode == 0 and found is not None
                and restored.returncode == 2
                and (root / "docs/fig.svg").read_bytes() == before
                and len(list(store.glob("*.json"))) == before_count
                and not (root / "UNEXPECTED").exists()
                and "同語言、同版本" in out)
        if safe:
            print("  ✅ 相符 peer 缺失時 restore 不執行舊工具、零寫入，並指示重下載同版套件"); ok += 1
        else:
            print("  ❌ 相符 peer 缺失時 restore 沒有 fail closed"); bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

root_glob_platform_case()
upgrade_edition_case()
my_index_cli_safety_case()
sync_my_rules_cli_safety_case()
upgrade_transient_scope_case()
upgrade_target_only_case()
upgrade_receipt_case()
upgrade_peer_fail_case()
upgrade_case()


def checkpoint_same_stat_case():
    global ok, bad
    import tempfile
    label = "CHECKPOINT-STAT：同時間大小的內容變更仍保存且不移動 reviewed"
    try:
        with tempfile.TemporaryDirectory(prefix="s2g_stat_") as temp:
            root = pathlib.Path(temp)
            def git(*args):
                p = subprocess.run(["git", "-C", str(root), *args],
                                   capture_output=True, timeout=30)
                if p.returncode:
                    raise RuntimeError(p.stderr.decode("utf-8", "replace"))
                return p.stdout.strip()
            git("init", "-q")
            git("config", "user.name", "selftest")
            git("config", "user.email", "selftest@local")
            git("config", "core.trustctime", "false")
            git("config", "core.checkStat", "minimal")
            (root / "governance").mkdir()
            for name in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
                (root / "governance" / name).write_text("fixture\n", encoding="utf-8")
            (root / ".gitignore").write_text("git-checkpoint.log\n", encoding="utf-8")
            path = root / "sample.txt"
            path.write_bytes(b"old\n")
            os.utime(path, (1600000000, 1600000000))
            git("add", "."); git("commit", "-qm", "base"); git("tag", "reviewed")
            reviewed = git("rev-parse", "reviewed")
            path.write_bytes(b"new\n")
            os.utime(path, (1600000000, 1600000000))
            expected = git("hash-object", "--path=sample.txt", "--", str(path))
            p = subprocess.run([PY, "-B", str(HERE / "checkpoint.py"), "--root", str(root),
                                "--mode", "tool", "--tool-id", "selftest", "--operation", "stat"],
                               capture_output=True, timeout=30,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1"))
            if p.returncode != 0 or git("rev-parse", "HEAD:sample.txt") != expected or git("rev-parse", "reviewed") != reviewed:
                raise RuntimeError("checkpoint exit/content/reviewed mismatch: " + repr((p.returncode, p.stdout, p.stderr)))
        print("  ✅ " + label); ok += 1
    except Exception as exc:
        print("  ❌ " + label + ": " + str(exc)); bad += 1

checkpoint_same_stat_case()

print("\n" + "=" * 48)
print(f"  通過 {ok} 項｜失敗 {bad} 項")
if tolerated:
    total = sum(tolerated.values())
    print(f"  ⚠️ 本次容忍 {total} 筆 WARN（**容忍 ≠ 沒有**）：")
    for code, n in sorted(tolerated.items()):
        print(f"      {code} ×{n}")
    print("      理由：fixture 目錄不含全部 glob，此類 WARN 是基礎建設噪音而非感測器誤報。")
    print("      ⛔ 若這裡出現的代碼與被測感測器的職責有關，那就是誤報，不是噪音。")
print("  結果：" + ("自測全數通過" if not bad else "自測失敗 — ⛔ 感測器變更不得提交"))
sys.exit(1 if bad else 0)
