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
       "corpus_empty", "CORPUS_EMPTY", forbid=("CORPUS_MANIFEST_MISSING",))
# ⚠️ 成對的另一半：有提取物卻沒有 manifest，仍然是 INCOMPLETE。
expect("有提取物但無 manifest 仍是 INCOMPLETE", 2, "sensor_claim_ledger.py",
       "corpus_unmanifested", "CORPUS_MANIFEST_MISSING")

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
                "governance": ["governance", "policy"], "_human": ["ledgers"]},
            "deny": deny if deny is not None else ["ledgers"]},
            ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
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
           scopes={"governance": ["governance", "policy"]})
# 🔴 **D1 的成對樣本（v1.4.1）。**
#    ⚠️ **舊版把 `t0_docs` 在程式裡無條件併進 `denied`，於是設定關不掉 T0 的保護——
#    而 `framework_config.py` 的註解同時寫著「治理 Agent 可以維護它們」。**
#    **⛔ 下面兩項必須同時成立，缺一都代表回到了舊行為。**
scope_case("deny 含 T0 時，改 T0 須 FAIL",
           ["governance/AGENTS.md"], 1, "WRITE_TO_DENIED_PATH",
           scopes={"governance": ["governance", "policy"]},
           deny=["ledgers", "governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"])
scope_case("🔴 deny ⛔ 不含 T0 時，改 T0 ⛔ 不得 FAIL（設定關得掉）",
           ["governance/AGENTS.md"], 0,
           scopes={"governance": ["governance", "policy"]},
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
           ["policy/SOURCES.md"], 0, scopes={},
           forbid=("DENIED_PATH_TOUCHED_UNATTRIBUTED",))
scope_case("_human 涵蓋時不誤報，但豁免筆數須印出",
           ["ledgers/Claim_Ledger.md"], 0, "_human", forbid=("WRITE_TO_DENIED_PATH",))
scope_case("範圍內的變更不誤報", ["policy/SOURCES.md"], 0,
           forbid=("WRITE_TO_DENIED_PATH", "WRITE_OUT_OF_SCOPE"))


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
    r = subprocess.run([PY, str(HERE / "_selftest_crasher.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    crashed = r.returncode != 0 and "Traceback (most recent call last)" in (r.stderr or "")
    global ok, bad
    if crashed:
        print("  ✅ 崩潰的感測器須被判為 INCOMPLETE（不是 FAIL）"); ok += 1
    else:
        print("  ❌ 崩潰的感測器須被判為 INCOMPLETE"
              f"（退出碼 {r.returncode}，stderr 有無 traceback："
              f"{'有' if 'Traceback' in (r.stderr or '') else '無'}）"); bad += 1


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
        (proj / "policy").mkdir(parents=True, exist_ok=True)
        (proj / "ledgers").mkdir(parents=True, exist_ok=True)
        (tmp / "別的東西").mkdir(parents=True, exist_ok=True)
        for t0 in ("AGENTS.md", "WORKFLOW_CONSTITUTION.md"):
            (proj / "governance" / t0).write_text("# T0\n", encoding="utf-8")
        (proj / "policy/SOURCES.md").write_text("x\n", encoding="utf-8")
        (proj / "ledgers/Claim_Ledger.md").write_text("x\n", encoding="utf-8")
        (tmp / "別的東西/note.md").write_text("x\n", encoding="utf-8")
        (proj / "governance_config.json").write_text(json.dumps(
            {"write_scopes": {"governance": ["governance", "policy"]},
             "deny": ["ledgers"]}, ensure_ascii=False), encoding="utf-8")
        g = ["git", "-C", str(tmp)]
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
        subprocess.run(g + ["add", "-A"], capture_output=True)
        subprocess.run(g + ["-c", "user.name=t", "-c", "user.email=t@t",
                            "commit", "-q", "-m", "base"], capture_output=True)
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
    for f in sorted(HERE.glob("*.py")):
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
my_index_case("說明檔壞掉：須 INCOMPLETE（⛔ 不得當成「沒有說明」）",
              lambda t: (_gen(t),
                         (t / "my/MY_INDEX_notes.json").write_text("{壞掉", encoding="utf-8"),
                         None)[-1], 2, "INDEX_NOTES_UNREADABLE", regen=False)

upgrade_case()

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
