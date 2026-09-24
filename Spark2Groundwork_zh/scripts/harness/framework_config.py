#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""框架設定 —— **所有感測器的唯一設定來源**。

## 為什麼設定要集中在一個檔案

兩個先行專案的感測器都把路徑硬編在各自的檔案裡。後果：
**改一個資料夾名稱要改五支程式，而漏改的那一支不會報錯——它只是靜靜地什麼都不掃。**

⚠️ 實測個案（`Incident_Log.md` 「靜默過濾」家族）：某專案的掃描清單中有兩個
**從建立起就命中 0 個檔案**的 glob——一個因為目錄被搬走、一個因為名稱少了一個 s。
**看起來在保護什麼，其實沒有。**

→ 因此本檔除了集中設定，還要求每支感測器**回報命中 0 個檔案的 glob**。

## 怎麼改

**只改本檔。** 改完跑一次 `run_selftest.py` 確認沒改壞。
⛔ 不要在個別感測器裡另外硬編路徑。
"""

import json
import pathlib
import sys

# ── 專案根目錄 ────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[2]

# ── 使用者可覆寫：專案根目錄放一個 governance_config.json 即可 ──
_USER = ROOT / "governance_config.json"

DEFAULTS = {
    # T0 必讀法：全專案各只有一份，子資料夾不得存放副本
    "t0_docs": ["governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"],

    # 治理文件（規則的家）——供跨檔重複與章節引用檢查使用
    # ⚠️ 這是 **glob**，不是硬編清單（R-21：白名單會靜默過濾）
    "governance_globs": ["governance/*.md", "ledgers/*.md", "file_index.md"],

    # 🔴 **你的文件索引**（`tool_my_index.py`、`sensor_my_index.py`）。
    # ⚠️ **實測個案：某專案套用框架後就不再維護自己的檔案索引了——
    #    它的 `file_index.md` 裡⛔ 沒有一條跟研究有關。**
    #    🔴 **`file_index.md` 原本是先行專案用來管研究文件的表，
    #    精煉為框架時內容全變成框架自己的東西，⛔ 而名字沒換。**
    # ⛔ **索引由程式產生（判準＝「框架不擁有的每一樣東西」，⛔ 不是一份要收哪些的清單）；
    #    說明由 AI 維護。⚠️ 分開的理由：程式對 .docx／.pdf 取不到有意義的標題。**
    "my_index": "my/MY_INDEX.md",
    "my_index_notes": "my/MY_INDEX_notes.json",
    # ⚠️ **框架自己產生的檔案：⛔ 它們不是「你的文件」。**
    #    🔴 **實測：跑完一次升級之後，`git-checkpoint.log` 出現在索引的「尚無說明」裡——
    #    ⛔ 一個永遠不會有人去寫說明的檔案，會變成一行永久的雜訊。**
    #    ⛔ **這是排除清單（deny 形態），⛔ 不是「要收哪些」的白名單。**
    "my_index_exclude": ["git-*.log"],

    # 🔴 **公版規則 ↔ 專案規則**（`sensor_my_rules.py`、`tool_sync_my_rules.py`）。
    # ⚠️ **為什麼要有兩份：** `governance/` 在升級時整包替換，
    #    **所以一個往 `RULES.md` 累積自己規則的專案，會在升級時失去那些累積。**
    #    🔴 **v1.4.0 以前確實如此，而 `PROFILE_solo.md` 正在鼓勵使用者那樣做。**
    # ⛔ **兩份拷貝⛔ 不能沒有守望者**——那正是失效家族的軸二。守望者是 `sensor_my_rules.py`。
    "framework_rules": "governance/RULES.md",
    "my_rules": "my/MY_RULES.md",
    # ⚠️ 標了它就不報 `RULE_TEXT_DRIFT`，改為印進統計欄——**豁免要看得見。**
    "override_marker": "[本專案覆寫]",

    # 台帳
    "conjecture_ledger": "ledgers/Conjecture_Ledger.md",
    "claim_ledger": "ledgers/Claim_Ledger.md",

    # 語料庫：程式化提取的全文，錨點比對的對象
    # ⛔ 提取物不得手工編輯（R-14）
    # 🔴 **版本一致性感測器要比對哪幾包**（`sensor_version_consistency.py`）。
    #    ⚠️ **這份清單與 `upgrade.py::FRAMEWORK_DIRS` 是同一組名字，⛔ 而它們是兩份拷貝。**
    #    **⛔ 兩邊不同步時，會出現「升級換得了、感測器卻不比對」的那一包。**
    "version_packages": ["governance", "profiles",
                         "prompts", "scripts", "docs"],
    "version_file": "_VERSION",

    "corpus_dir": "corpus_md",
    "corpus_manifest": "corpus_md/_manifest.json",
    # 原始 PDF 放這裡；tool_pdf_to_md.py 由此讀，⛔ 不得在工具內另行硬編
    # ⚠️ 實測個案：同一個目錄曾在 framework_config（corpus_md）、
    #    tool_pdf_to_md（paper_md）與 anchor_norm 檔頭（paper/）中有三個名字，
    #    而三處都不會報錯——另外兩處只會靜靜地掃 0 個檔案。
    "pdf_dir": "corpus",

    # 🔴 **提案檔標記。** 檔名含其一、且位於 handoffs/ 者，豁免猜想引用存在性檢查。
    #
    # ⚠️ **為什麼需要這個豁免：框架自己的流程與自己的感測器互斥。**
    #    流程是「AI 提案 → 人裁決 → 人寫入台帳」（`governance/AGENTS.md` §5），
    #    於是在「提案已交、裁決未下」的那段期間，**提案檔必然引用尚未存在的編號**，
    #    而 `CITATION_NOT_IN_LEDGER` 必然報 FAIL。實測一輪 12 筆。
    #    → 這正是 `profiles/PROFILE_multi_agent.md` §4 的 G-2 問的
    #      「新規則會不會與某條既有規則在『同時遵守』時互相排斥」。
    #
    # ⛔ **豁免的判準刻意是結構性的（路徑＋檔名），不是一句自由文字的理由。**
    #    ⚠️ 先行專案的教訓：豁免只要求「一句理由」，於是**一句讀起來合理的話
    #    讓感測器對一筆真捏造永久靜默，而儀表板是綠的。**
    # ⛔ **被豁免的檔案一律印出。** 靜默豁免等於「靜默過濾」家族。
    "proposal_markers": ["待套用", "pending-adjudication"],

    # 🔴 **模型歸屬的掃描範圍**（`sensor_model_attribution.py`）。
    # ⚠️ 刻意**只掃 AI 的產出物**，⛔ 不掃專案根目錄。
    #    根目錄的 .md 是框架提供的模板（README／SETUP／file_index …），**本來就不該有作者欄**。
    #    舊版掃根目錄，因此必須靠一張硬編豁免清單壓住自己製造的告警——
    #    **那張白名單是為了補償一個錯的掃描範圍而存在的**（`R-21`）。
    # ⚠️ **v1.4.1：`outputs/` 與 `reports/` 兩個 glob 已移除。**
    #    🔴 **它們從 v1.0.0 起就命中 0 個檔案——那兩個目錄從未存在過，也從未被任何文件定義。**
    #    ⛔ **不補建目錄**：研究產出的落點在 v1.5.0 由 `research/` 定義，
    #    **先建兩個沒有定義的目錄，等於自己製造一次遷移。**
    # 🔴 **已知缺口（⛔ 刻意留著，不假裝已覆蓋）：`MODEL_IDENTITY.md` §3.4 要求
    #    「主文本」的作者欄寫具體型號，⛔ 而本範圍裡不可能有主文本。**
    #    **該節已加註此事。掃描範圍待 `research/` 存在後補上。**
    "attribution_globs": ["handoffs/*.md"],

    # 🔴 **程式碼的掃描範圍**（`sensor_reference_integrity.py`）。
    # ⚠️ `.py` 與 `.sh` 的**檔頭註解**是規則引用的重災區，而在此之前從未被掃過。
    # 🔴 **短式章節引用的錨定詞 → 它指向哪一份檔案。**
    #    `sensor_governance_text` 只解析 `` `<檔名>.md` §N `` 這個長式；
    #    ⛔ **而框架自己有 68 處寫的是短式「憲章 §N」，那些引用沒有任何感測器在查。**
    #    ⚠️ **實測：三筆懸空引用就是這樣活下來的**（`§5.11`／`§8.1`／`§5.8`）。
    #    ⛔ 錨定詞寫在設定裡，不硬編進感測器——**下游專案的簡稱不會跟這裡一樣。**
    "section_ref_aliases": {"憲章": "governance/WORKFLOW_CONSTITUTION.md"},

    "code_globs": ["scripts/**/*.py", "scripts/**/*.sh"],

    # 🔴 **啟動器腳本**（`sensor_reference_integrity.py`）。
    # ⚠️ **實測個案：`.bat` 與根目錄的 `.command` 一度不在任何感測器的掃描範圍內**——
    #    `code_globs` 只寫 `scripts/**`，而這些檔在專案根目錄。
    #    後果：四支 `.bat` 合計帶著 5 種先行專案殘留的懸空引用，長期無人發現。
    #    **與裁決 12／14 同形狀：殘留物被一個錯的掃描範圍藏著。**
    # ⚠️ 本檔曾有一個叫 `enable_bat_checks` 的**死開關**（沒有任何程式讀它）。
    #    ⛔ 這一項是它的相反：一個真的會掃到東西的範圍。
    # ⚠️ ⛔ 這裡不要放 `*.sh`：根目錄沒有 `.sh`，而 `scripts/` 底下有——
    #    覆蓋崩塌判準會因此判定「目錄下有同副檔名的檔，而 glob 一個都沒看到」。
    #    **`.sh` 的掃描範圍是 `code_globs`，⛔ 不是這裡。**
    "launcher_globs": ["*.bat", "*.command"],



    # 🔴 **被抄到別處的條款清單**（`sensor_clause_sync.py`，裁決 18）。
    #
    # ⚠️ **這一項存在的理由是兩條規則互斥：**
    #    `R-24` 要求每份 prompt 完全自足（所以模板**必須**抄一份禁用清單），
    #    而憲章 §3.2 要求每條規則只有一個定義處。**互斥的結果就是漂移。**
    #    實測個案：`TEMPLATE_adversarial.txt` 寫「非常穩健」，
    #    而 `Audit_Protocol.md` §3 寫「非常強健」——**一個字，靠人逐字比對才發現。**
    #
    # ⛔ `home` 是**指標**，不是掃描範圍——副本靠 `marker` 發現，
    #    ⛔ 本框架不維護任何副本檔名清單（`R-21`）。
    "synced_lists": [
        {"id": "禁用語氣詞",
         "home": "governance/Audit_Protocol.md",
         "marker": r"⛔.*禁用"},
    ],
    # 副本可能出現的地方。⚠️ ⛔ 不含 `scripts/`——
    #    變更記錄與感測器原始碼會**描述**這份清單，而描述不是副本。
    "sync_scan_globs": ["第一個想法.md", "prompts/*.txt", "prompts/*.md", "governance/*.md",
                        "profiles/*.md"],

    # 產出物：會被下游引用者，受自我背書檢查
    # ⚠️ 同 `attribution_globs`：`outputs/`／`reports/` 兩個死 glob 已於 v1.4.1 移除。
    "artifact_globs": ["handoffs/*.md"],

    # 掃描時一律排除（⚠️ 以**相對於 root 的路徑**判定，見 R-18）
    #
    # ⚠️ **`excluded_dirs` 與 `write_scopes` 講的是兩件事，⛔ 不要互相推導：**
    #    `excluded_dirs` ＝「掃描時不看這裡」——它管的是**感測器的視野**。
    #    `write_scopes`  ＝「誰可以寫這裡」——它管的是**權限**。
    #    於是 `archive` 可以同時是「不用掃」與「不准動」，這**不是矛盾**。
    # ⛔ **不得讓 write_scopes 的檢查自動略過 excluded_dirs**——
    #    那等於讓排除清單順便取得寫入豁免，而**排除清單是為了省掃描成本設的，不是為了授權。**
        # ⚠️ 這幾個目錄「是什麼」的定義處是憲章 §6.2，⛔ 本處只列名不解釋。
    # ⚠️ **`_upgrade` 是 v1.4.1 補的。** 🔴 **它是升級用的暫存包（`upgrade.py` 讀它），
    #    ⛔ 而它一度被 `tool_my_index.py` 當成「你的文件」列進索引——一次 85 筆。**
    #    **⚠️ 那是實際跑一次升級才看到的，⛔ 不是讀設定看出來的。**
    "excluded_dirs": ["archive", ".git", "__pycache__", "selftest", "scratch",
                      "_to_delete", "_upgrade", "node_modules", ".venv"],

    # 🔴 **AI 的寫入禁區——⚠️ 這是「預設值」，⛔ 不是禁令。**
    #
    # **使用者可以清空它，那就是完整授權**（憲章 §6.3）。
    # ⛔ **本框架沒有立場禁止那件事**——每個專案由該專案的主持人負責。
    #
    # ⚠️ **為什麼預設擋這三個而不擋治理文件：** 判準是**能不能還原**。
    #    `governance/` `prompts/` `scripts/` 壞了可以從 GitHub 重新下載覆蓋；
    #    🔴 **台帳與語料壞了，沒有任何地方可以還原。**
    # ⛔ 這是資訊，不是規勸——**知道差別之後怎麼設定，是使用者的決定。**
    #
    # 🔴 **v1.4.1：T0 兩份現在逐字列在這裡。**
    #    ⚠️ **舊版刻意不列，而感測器在程式裡無條件把它們併進來——⛔ 於是設定關不掉，
    #    而本註解卻寫著「治理 Agent 可以維護它們」。兩處意圖相反。**
    #    ✅ **列在這裡之後，「清空 `deny` 就是完整授權」（憲章 §6.3）第一次是真的。**
    #    ⛔ **要讓治理 AI 能維護 T0，把這兩行刪掉——那是你的裁決，⛔ 不是框架的禁令。**
    #
    # ⚠️ **v1.4.1 起，本項⛔ 不再取決於 `write_scopes` 有沒有設。**
    #    **單人專案（`write_scopes` 為空）得到的是一筆列出檔名的 WARN，⛔ 不是靜默，
    #    也⛔ 不是紅燈**——感測器讀 `git status`，⛔ 分不出人與 AI。
    "deny": ["ledgers", "corpus", "corpus_md",
             "governance/AGENTS.md", "governance/WORKFLOW_CONSTITUTION.md"],

    # 多角色專案才需要：各角色的寫入範圍
    # 單 agent 專案請留空 {}，感測器會自動略過該項檢查
    "write_scopes": {},

    # ⚠️ 這裡曾有 enable_reference_authenticity 與 enable_bat_checks 兩個鍵。
    #    ⛔ 全專案沒有任何程式讀過它們——**看起來有一個功能可以打開，其實打開了不會發生任何事。**
    #    這與本檔開頭警告的死 glob 同型（死開關），故移除。
    #    環⑤ 的守望方式改由 governance/SOURCES.md §3、§5 定義。
}


def load(root=None):
    """讀設定。使用者檔存在時覆寫預設值（淺層合併）。

    ⚠️ **`root` 參數的存在理由：** 舊版一律讀 `ROOT/governance_config.json`，
    而 `ROOT` 是**感測器檔案自己的位置**推得的。於是用 `--root` 指向另一個目錄時，
    **掃描範圍換了，設定卻沒換**——感測器會拿 A 專案的設定去檢查 B 專案，
    ⛔ 而且不會有任何訊息。
    **自測 fixture 因此也無法測任何與設定有關的行為。**
    """
    cfg = dict(DEFAULTS)
    user = (pathlib.Path(root) / "governance_config.json") if root else _USER
    if user.exists():
        try:
            data = json.loads(user.read_text(encoding="utf-8"))
        except Exception as e:                       # noqa: BLE001
            # ⛔ 不得靜默忽略：設定壞掉而感測器照跑，等於在錯誤的範圍上宣告通過
            raise SystemExit(f"[FAIL] governance_config.json 無法解析：{e}")
        # 🔴 **不認得的鍵一律報錯，⛔ 不得靜默吃掉（v1.4.1）。**
        #    ⚠️ **舊版是 `cfg.update(data)`：把 `deny` 打成 `denny`，程式不會有任何反應——**
        #    **`denny` 被加進設定、`deny` 留在預設值，⛔ 而使用者相信自己設定過了。**
        #    **🔴 那是「靜默過濾」家族發生在設定的入口。**
        # ⛔ **不得降級成 WARN：一個被吃掉的設定鍵，畫面上與「設定成功」一模一樣。**
        # ⚠️ 底線開頭的鍵（如 `_說明`）刻意允許——**設定檔要能寫給人看。**
        unknown = [k for k in data if k not in DEFAULTS and not k.startswith("_")]
        if unknown:
            import difflib
            lines = []
            for k in unknown:
                near = difflib.get_close_matches(k, DEFAULTS, n=1)
                lines.append(f"  ⛔ {k}" + (f"　⚠️ 你可能想寫的是：{near[0]}" if near else ""))
            raise SystemExit("[FAIL] governance_config.json 有本框架不認得的設定鍵：\n"
                             + "\n".join(lines)
                             + "\n**⛔ 改對或刪掉它。一個被吃掉的設定鍵，"
                               "與設定成功長得一模一樣。**")
        cfg.update(data)
    return cfg


def excluded(path, root, cfg):
    """路徑是否落在排除清單內。

    ⚠️ **必須用相對路徑**（R-18）。兩個先行專案各踩過一次：
    以絕對路徑的 parts 比對，會把測試樣本目錄下的每一個檔案都排除，
    **造成自測全綠或全紅**，而兩種都看不出是排除邏輯的問題。
    """
    try:
        parts = set(pathlib.Path(path).resolve().relative_to(pathlib.Path(root).resolve()).parts)
    except ValueError:
        return True
    return bool(parts & set(cfg["excluded_dirs"]))


def resolve_globs(globs, root, cfg):
    """展開 glob 並回報命中 0 個檔案者。

    回傳 (檔案清單, 死 glob 清單)。
    ⚠️ **死 glob 必須被回報**——它與死豁免同型：看起來在保護什麼，其實沒有。
    """
    files, dead = [], []
    for g in globs:
        hit = [p for p in root.glob(g) if p.is_file() and not excluded(p, root, cfg)]
        if not hit:
            dead.append(g)
        files.extend(hit)
    return sorted(set(files), key=lambda p: p.as_posix()), dead


def active_launcher_globs(globs, root, platform=None):
    """只要求目前平台的啟動器存在，但仍掃描實際存在的外平台啟動器。"""
    platform = platform or sys.platform
    required = ".bat" if platform == "win32" else (".command" if platform == "darwin" else None)
    active = []
    for g in globs:
        suffix = pathlib.PurePosixPath(g).suffix
        present = any(p.is_file() for p in pathlib.Path(root).glob(g))
        if present or (required and suffix == required):
            active.append(g)
    return active
