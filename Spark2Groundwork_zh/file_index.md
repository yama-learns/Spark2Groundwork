# 檔案索引與規則定義處

**文件層級：T1 — 索引。⛔ 只說「哪裡有什麼」，不重述任何規則內容。**

> ⚠️ **本索引不是權威源。** 內容以檔案本身為準。
> **以索引代替查證是失效家族①。**

---

## 0. 每條規則的唯一定義處

**要改一條規則，只改下表指名的那一處**（憲章 §3.2）。

| 規則／判準 | 唯一定義處 |
|---|---|
| 查證等級標記 | `governance/AGENTS.md` §2.1 |
| `[已查證]` 的兩條限制 | `governance/AGENTS.md` §2.2 |
| 裁決性 vs 探索性語彙 | `governance/AGENTS.md` §2.3 |
| 支持與推翻的不對稱 | `governance/AGENTS.md` §2.4 |
| 學術底線 | `governance/AGENTS.md` §3 |
| 拓撲事實 | `governance/WORKFLOW_CONSTITUTION.md` §1 |
| 證據鏈環①–⑦ | `governance/WORKFLOW_CONSTITUTION.md` §2 |
| 文件依更新頻率分層 | `governance/WORKFLOW_CONSTITUTION.md` §3 |
| 文件增生防線 | `governance/WORKFLOW_CONSTITUTION.md` §3 |
| 開工／收工儀式 | `governance/WORKFLOW_CONSTITUTION.md` §4 |
| 決策請求格式 | `governance/WORKFLOW_CONSTITUTION.md` §5 |
| 寫入範圍通則 | `governance/WORKFLOW_CONSTITUTION.md` §6 |
| 感測器變更三關 ／ 誤報處置 ／ 退出碼 | `governance/WORKFLOW_CONSTITUTION.md` §7 |
| 全部工作守則（R-01～R-32） | `governance/RULES.md` |
| 失效家族①–⑦ | `governance/Incident_Log.md` §2 |
| 猜想六狀態 ／ 除役與休眠門檻 | `ledgers/Conjecture_Ledger.md` §0 |
| 主張登錄範圍 ／ 錨點四規則 | `ledgers/Claim_Ledger.md` §0–§1 |
| **錨點正規化函式** | `scripts/harness/anchor_norm.py` |
| **所有感測器的路徑設定** | `scripts/harness/framework_config.py` |
| 交接封包規格 | `policy/HANDOFF.md` |
| 書目與來源 | `policy/SOURCES.md` |
| 外部工具 | `policy/EXTERNAL_TOOLS.md` |
| 模型身分 | `policy/MODEL_IDENTITY.md` |

---

## 1. 文件分類（依更新頻率）

| 類 | 檔案 |
|---|---|
| **狀態**（每輪覆寫） | `NEXT_SESSION_MEMO.md` |
| **規格**（罕有變更） | `governance/*`、`policy/*`、`profiles/*`、`prompts/*` |
| **資料**（只增不改寫） | `ledgers/*`、`handoffs/*`、`SENSOR_CHANGELOG.md` |
| **索引** | `file_index.md`（本檔） |

---

## 2. 感測器

⚠️ **本節刻意不寫支數**——那是狀態（R-16）。查證方式：

```
python scripts/harness/run_all_sensors.py
python scripts/harness/run_selftest.py
```

| 檔案 | 守望什麼 |
|---|---|
| `sensor_claim_ledger.py` | **錨點是否真的在原文裡**（零成本）＋ 提取物是否被竄改 |
| `sensor_conjecture_ledger.py` | 反證條件、競爭假說、欄位完整性 |
| `sensor_self_certification.py` | 產出物自我背書、整體性好評 |
| `sensor_governance_text.py` | 跨檔重複、章節引用可解析、規格文件混入狀態 |
| `sensor_scope_and_t0.py` | T0 唯一性、寫入範圍越界 |
| `anchor_norm.py` | 正規化函式（**單一定義處**） |
| `framework_config.py` | 路徑設定（**單一定義處**） |

### 隨選（**不在預設套件內，因其介面是單一檔案**）

```
python scripts/harness/sensor_prompt_self_contained.py <prompt.md>
python scripts/harness/sensor_model_attribution.py
```

⚠️ **把它們硬塞進總執行器，只會產生一個永遠 INCOMPLETE 的假訊號——
而 INCOMPLETE 是本框架最不能被稀釋的一個狀態。**
