# v1.4.5 變更摘要（2026-09-24）

- 修復 Mac 索引／設定相容問題，保留使用者自訂排除。
- 提供檢查、保存、人工已閱快照、差異、更新與規則同步入口；保存不等於人工已閱。
- 缺依賴與工具崩潰回報未完成，改善錯誤說明。
- 增加 [v2 升級準備](V2_PREPARATION.md)，不搬移研究資料。

v1.4.5 的 Mac 自動化程序由 GitHub Actions 驗證；Finder／Gatekeeper／實機雙擊操作另待後續驗證，尚未完成，不視為已通過。

- 範圍檢查現在涵蓋人類已閱快照後的提交與還原紀錄。缺少或不相關的 reviewed 基準會回報 INCOMPLETE；請先實際檢閱專案，再用既有「記錄快照」按鈕建立人類已閱基準，不能只為消除警告而跳過檢閱。單純保存不等於人類已閱。
- 檢查保持唯讀（含 Git index），無法解析 Git 輸出時明報 INCOMPLETE。
- 已知範圍：專案子樹內的 assume-unchanged／skip-worktree 旗標與落在禁區或宣告範圍外的 .gitignore 忽略檔案現在會回報 INCOMPLETE，拒絕靜默通過；移除旗標或修正配置後恢復正常檢查。一般研究附件與框架快取維持安靜。此檢查不認證作者，不防 Git 歷史改寫或 reviewed 基準移動；真正的人類重新檢閱本來就可前移基準。


### E2b 修復：自動產生的檔案與解除方式

scope感測器實際以 `git ls-files --others --ignored --exclude-standard -z` 讀取被忽略路徑。固定豁免僅包含 Finder 的 `.DS_Store`、精確的 `scripts/harness/harness_status.json` 報告與根目錄 `git-checkpoint.log`，並回報豁免數量；在保護資料夾內的系統中繼檔亦適用。若deny直接指名該檔案，仍尊重此明確設定，不豁免。相似檔名、其他JSON／log、使用者任意新增的.gitignore规则不會因此獲得豁免。已追蹤變更與tracked隱藏旗標仍正常檢查。

受保護而被Git忽略的研究檔確實缺乏版本證據：單純推進reviewed不能補出它的內容或歷史。這時INCOMPLETE不是指控AI違規。請AI列出路徑與選項，你不必貼終端指令。經你同意後，AI可將需要保護的檔案納入**本機**版本追蹤（不等於上傳），確認內容後依正常人工覆核流程處理。若確定要保持不追蹤，AI可提議移至保護範圍外並更新引用，待你同意再操作。不要刪研究資料、清空deny或只推進reviewed來消除警告；大型／私有資料的上傳仍須另行同意。

隱藏旗標也先說明再由AI處理；真正的稀疏checkout可能需要完整工作樹才能查證。感測器本身不修改檔案、index、旗標或reviewed。本版不另造一套ignored檔案指紋基準系統。

### E3a 修復：中文猜想台帳感測器跨樹目標配置

修復中文版 `sensor_conjecture_ledger.py` 在跨樹 `--root` 檢查時讀取自身模組層全域配置而非目標專案配置的缺陷。現在完整依目標專案之 `governance_config.json` 解析自訂猜想台帳路徑、提案檔豁免標記及排除目錄。英文版保持原有正確行為；自測與跨樹整合測試全數通過。

### E3b 修復：雙語啟動、初始化、Solo 規範與收工流程矛盾修復

修復既有文件層矛盾（D-1 至 D-6）：
- `PROFILE_solo.md` 與 `Audit_Protocol.md`：澄清單一 AI 專案雖不執行雙模型對抗審計，但自動化檢查器仍依賴 `Audit_Protocol.md` 定義條款與自證規範，指示保留該檔勿刪除；更新 solo 模式說明。
- 專案規則路徑：修正治理 AI 啟動提示，自訂規則提案指向 `my/MY_RULES.md`（非會在升級時被覆蓋之 `governance/RULES.md`）。
- 台帳寫入權限：雙語三角色啟動提示之排除標題統一標記為預設禁區（`**⛔ 預設不可以寫入：**` / `**⛔ Closed to you by default:**`）；三角色與初始化提示對齊憲章 §6.1/§6.3 與 `governance_config.json` 之 `deny` 清單（預設由人維護，經明確授權並自 deny 移除方可寫入，且審計者職司獨立查核不得自行豁免）。
- 初始化與收工儀式：`INITIALIZE_PROMPT.md` 必讀清單補入 `my/MY_RULES.md`，並增補第四步收工儀式（依憲章 §4.2 順序：檢查 → 覆寫備忘 → 產出交接封包 → 提出決策請求）。
- 使用者正常流程：`NEXT_SESSION_MEMO.md` §5 區分 AI 直接執行與使用者雙擊根目錄按鈕，正常流程不需手動貼命令。

### E3b r3 校正：Solo 模式保留清單

實測依舊版 Solo 指南刪除其他三份 profile，雙語完整感測器均因懸空引用失敗。Solo 使用者應保留所有隨附的 profile 檔案；保留檔案不會啟用其他協作模式。必留清單亦補入根目錄 `檢查專案.bat`／`.command` 啟動器。

### V145-REVIEW-BASELINE-1：缺人工已閱基準時停止比較

雙語「查看變更」在沒有 HEAD、沒有有效 `refs/tags/reviewed` 提交、標籤不屬於目前 HEAD 歷史或 Git 查詢失敗時回報 INCOMPLETE／exit 2，不再暫用 HEAD 並輸出「沒有未讀變更」。有效已閱基準時仍列出 AI 保存後的提交、工作樹與未追蹤變更；檢視不移動已閱標籤。
