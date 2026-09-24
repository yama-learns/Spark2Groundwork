#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository and Launcher Hygiene Checker for Spark2Groundwork v1.4.5 (CI-0 r6).

Verifies mandatory repository structure, line endings, launcher contracts,
reachability and token-level argument mapping, shell script syntax,
Python 3.9 AST syntax compatibility, worktree cleanliness,
exact 186 selftest case sets, named-case fault propagation regression,
dual aggregate+direct sensor execution, and fresh launcher reachability diagnostics with exit 0/1/2 propagation (not authentication).
"""
import ast
import argparse
import hashlib
import json
import os
import pathlib
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

EXPECTED_ZH_LAUNCHERS = {
    "儲存進度",
    "同步規則",
    "查看變更",
    "檢查專案",
    "檢查更新",
    "記錄快照",
}

EXPECTED_EN_LAUNCHERS = {
    "save_progress",
    "sync_rules",
    "review_changes",
    "check_project",
    "check_update",
    "snapshot",
}

EXPECTED_SENSORS = {
    "sensor_conjecture_ledger.py",
    "sensor_claim_ledger.py",
    "sensor_self_certification.py",
    "sensor_governance_text.py",
    "sensor_scope_and_t0.py",
    "sensor_reference_integrity.py",
    "sensor_clause_sync.py",
    "sensor_my_rules.py",
    "sensor_my_index.py",
    "sensor_version_consistency.py",
}

LAUNCHER_CONTRACT = {
    "Spark2Groundwork_zh": {
        "儲存進度": ("zh", "save"),
        "同步規則": ("zh", "sync"),
        "查看變更": ("zh", "review"),
        "檢查專案": ("zh", "check"),
        "檢查更新": ("zh", "update"),
        "記錄快照": ("zh", "reviewed"),
    },
    "Spark2Groundwork_en": {
        "save_progress": ("en", "save"),
        "sync_rules": ("en", "sync"),
        "review_changes": ("en", "review"),
        "check_project": ("en", "check"),
        "check_update": ("en", "update"),
        "snapshot": ("en", "reviewed"),
    },
}

REQUIRED_ZH_TESTS = [
    "反證條件為空須告警",
    "競爭解釋為空須 FAIL",
    "正確台帳不誤報",
    "UPG-REC-12",
    "相符 peer 缺失時 restore 不執行舊工具",
]

REQUIRED_EN_TESTS = [
    "empty falsification condition warns",
    "empty rival hypothesis FAILs",
    "correct ledger does not false-alarm",
    "UPG-REC-12",
    "restore with no compatible peer skips the old tool",
]

EXPECTED_ZH_TEST_CASES = frozenset([
    'CHECKPOINT-STAT：同時間大小的內容變更仍保存且不移動 reviewed',
    '反證條件為空須告警',
    '競爭解釋為空須 FAIL',
    '正確台帳不誤報',
    '填了字但未裁決仍須告警',
    '狀態不在六種之內須 FAIL',
    '已除役與休眠不誤報',
    '🟢／🔴 缺依據須 FAIL',
    '引用台帳中不存在的編號須 FAIL',
    '引用存在的編號不誤報',
    '提案檔豁免引用檢查，且豁免須印出',
    '刻意留白並附理由須改報已聲明',
    '錨點查無須 FAIL',
    '連字與跨行斷字不誤報',
    '正確錨點不誤報',
    '空的提取資料夾不算「查不了」',
    '有提取物但無 manifest 仍是 INCOMPLETE',
    '來源無法解析須 INCOMPLETE 絕不放寬',
    '同作者同年多篇來源歧義須 INCOMPLETE',
    '明示檔名與年份區分不誤報',
    'manifest 非陣列格式錯誤須 INCOMPLETE',
    '姓氏子字串比對不可偷換論文須 INCOMPLETE',
    '全部主張未進入查證時須 INCOMPLETE',
    '實質文字提到樣板符號時不得被當成空樣板',
    '作者欄唯一命中的推論須可見',
    '自我背書須抓到',
    '閘門式要求與誠實揭露皆不誤報',
    '整體性好評須告警',
    '跨檔重複長句須告警',
    '句中結束的重複長句須告警',
    '懸空章節引用會告警',
    '懸空的短式引用會告警',
    '可解析的短式引用不誤報',
    '住在 .py 檔頭的短式引用會告警',
    '圍籬區塊內的標題不計入',
    '治理文本乾淨不誤報',
    '寫入 deny 範圍須 FAIL',
    'deny 含 T0 時，改 T0 須 FAIL',
    '🔴 deny ⛔ 不含 T0 時，改 T0 ⛔ 不得 FAIL（設定關得掉）',
    '🔴 單人專案改台帳：須列出，⛔ 但不得 FAIL',
    '單人專案改一般檔案：⛔ 不得出現那筆 WARN',
    '_human 涵蓋時不誤報，但豁免筆數須印出',
    '範圍內的變更不誤報',
    '提交後越界變更仍須檢出',
    '提交後還原的變更仍留下歷史觸及紀錄',
    '基準後零變更時不誤報',
    '改名跨越界限（allowed至denied）須 FAIL',
    '改名跨越界限（denied至allowed）兩端皆納入檢查須 FAIL',
    '雙端皆合法之改名不誤報',
    '特殊路徑字元（中文、空格、方括號、開頭減號）正確解析不誤報',
    '跨子樹改名移入專案能檢出目標端',
    '缺 reviewed 基準時須 INCOMPLETE 且不得宣稱通過',
    'reviewed 非 HEAD 祖先時須 INCOMPLETE 且不得宣稱通過',
    '感測器執行保持 HEAD 與 reviewed 唯讀不變',
    'assume-unchanged 變更內容須 INCOMPLETE',
    'assume-unchanged 內容未改仍須 INCOMPLETE 且移除旗標後恢復',
    'skip-worktree 變更內容與未改皆須 INCOMPLETE',
    'deny 內新檔被 ignore 須 INCOMPLETE',
    '既有 ignore 內檔在 deny 內須 INCOMPLETE',
    'scope 外檔被 ignore 須 INCOMPLETE 且普通研究附件與快取不誤報',
    'deny 與排除衝突時須明示配置矛盾且專案外旗標與 ignore 不污染',
    '跨 prompt 指涉須 FAIL',
    '未組裝的區塊佔位符須 FAIL',
    '自足的 prompt 不誤報',
    '引述禁令不誤報，且豁免須印出',
    '內容槽不誤報',
    'generic 不執行 DR 條款表',
    'deep-research 執行 DR 條款表',
    '產出物無型號欄須 FAIL',
    '只寫家族名須 FAIL',
    '寫平台名須 FAIL',
    '具體型號不誤報',
    '正確宣告「無法讀取」不得判為缺陷',
    '引用不存在的檔案須 FAIL',
    '引用跳出本資料夾須 FAIL',
    '資料夾內的相對引用不得誤報',
    '引用存在的檔案不誤報',
    '格式佔位符不誤報',
    '明示未隨附者豁免，且豁免須印出',
    '目錄不存在：只告警',
    '目錄剛建好還空著：只告警',
    '目錄有東西但沒一個符合 glob：INCOMPLETE',
    '條款清單一字之差須 FAIL',
    '順序不同但集合相同不得誤報',
    '定義處不存在須 INCOMPLETE',
    '執行期與解析期崩潰都判為 INCOMPLETE（不是 FAIL）',
    '公版有而 MY_RULES 沒有的條，須 FAIL',
    '兩邊一致時⛔ 不得誤報',
    '正文被改而未標覆寫，須 FAIL',
    '🔴 覆寫標記寫在條文那一行，須 FAIL（⛔ 不得當成有理由）',
    '覆寫標記自成一行且有理由時，⛔ 不得 FAIL',
    'MY_RULES 不存在時須 INCOMPLETE（⛔ 不是 PASS）',
    '🔴 打錯的設定鍵須報錯並建議正確鍵名',
    '正確的設定鍵⛔ 不得報錯',
    '底線開頭的鍵是給人看的，⛔ 不得報錯',
    '🔴 git 說成功卻沒輸出：判 INCOMPLETE，⛔ 不崩潰、⛔ 不誤診',
    '🔴 專案在 repo 子目錄：看得到子樹內，⛔ 看不到子樹外',
    '🔴 subprocess 解碼一律指定 encoding（掃了 27 支，0 筆例外）',
    '🔴 CP-09／tool：原本沒有 reviewed，程式跑完仍然沒有',
    'CP-09／tool：⛔ 不得印出人工審閱的橫幅',
    '🔴 CP-10／tool：既有的 reviewed 指向⛔ 不得改變',
    '🔴 CP-09／ai：原本沒有 reviewed，程式跑完仍然沒有',
    'CP-09／ai：⛔ 不得印出人工審閱的橫幅',
    '🔴 CP-10／ai：既有的 reviewed 指向⛔ 不得改變',
    'human 模式仍然移動 reviewed（⛔ 這個區分是刻意的）',
    'tool 模式缺 --tool-id／--operation 必須拒絕（⛔ 匿名工具與人分不開）',
    '🔴 CP-14：reviewed 標籤建不起來時，人工檢查點⛔ 不得 exit 0',
    '🔴 CP-14：標籤沒動就⛔ 不得印「基準已移到」',
    'CP-14：必須明說標籤沒有移動',
    'CP-14：提交本身仍然要建立（⛔ 不得弄丟工作）',
    '🔴 CP-12：upgrade.py 呼叫 checkpoint 時必須明確傳 --mode tool',
    '🔴 CP-15：upgrade.py 必須印出持久收據 ID 與 checkpoint 提交',
    '🔴 CP-15：讀不回收據時⛔ 不得開始覆蓋',
    '🔴 CP-15：復原須使用內建收據命令，⛔ 不得叫使用者輸入 raw git checkout',
    '🔴 路徑排序一律指定 key（掃了 26 支，0 筆例外）',
    '判準抓得到 v1.4.1 那一行原始寫法',
    '🔴 會算雜湊的模組一律固定行尾（掃了 3 支，0 筆例外）',
    '判準對一個假的寫入點會報 FAIL（⛔ 反證條件成立）',
    '⛔ 不算雜湊的模組⛔ 不在判準範圍內（⛔ 不製造噪音）',
    '各包同版時不得報任何東西',
    '專案 D 那個狀態（profiles 落後一版）會被抓到',
    '缺一包是 WARN 的來源，⛔ 不得混進版本不一致',
    '讀不到版本是 INCOMPLETE 的來源，⛔ 不得當成一致',
    'v1.9.0 與 v1.10.0 並存時必須報 VERSION_MISMATCH',
    '🔴 訊息⛔ 不宣稱該補到哪一版（感測器看不到升級來源）',
    'version_packages 與 upgrade.FRAMEWORK_DIRS 是同一組名字',
    'SYNC-01：只有缺少的條目時附加，且明說沒有覆蓋任何既有文字',
    'SYNC-02：只有漂移時零寫入',
    '🔴 SYNC-02：印出實際差異行（`+`／`-` 開頭）',
    'SYNC-02：告訴使用者要把 `+` 那幾行貼進去，⛔ 且不得整份取代',
    '🔴 SYNC-03：同時有 missing 與 drift 時，附加要真的發生',
    '🔴 SYNC-03：⛔ 不得一面寫入一面宣稱「沒有修改」',
    'SYNC-03：漂移仍然要被報告',
    'SYNC-05a：合法覆寫不動，訊息說「已標」',
    '🔴 SYNC-05b：覆寫沒寫理由時要說感測器會 FAIL',
    'SYNC-06：沒有東西要做時零寫入，且說明那是算過的結果',
    '🔴 SYNC-07：`--adopt` 已退回，必須被拒絕且零寫入',
    '🔴 SYNC-08：現行操作說明裡沒有已退回的旗標（掃了 29 個檔案）',
    'SYNC-08：掃描本身對一段假說明會報 FAIL（⛔ 反證條件成立）',
    '退役清單與可替換清單⛔ 不重疊',
    '專案裡還有 `policy/` 時必須列出來',
    '新專案沒有 `policy/` 時⛔ 不得出現退役提示',
    '空的孤兒資料夾一樣要列出（它仍讓人以為框架在維護它）',
    '索引還沒產生過須 INCOMPLETE（⛔ 不是 PASS）',
    '剛產生的索引⛔ 不得誤報',
    '🔴 使用者自己開的資料夾必須出現在索引裡（⛔ 不是白名單）',
    '產生之後又多了一個檔：須報過期',
    '說明指向不存在的檔案：須 FAIL',
    '🔴 檔案在、只是被索引排除：⛔ 不得說成「檔案不存在」',
    '說明檔壞掉：須 INCOMPLETE（⛔ 不得當成「沒有說明」）',
    '🔴 索引依字串排序（跨平台一致）',
    '根層 glob 留在專案根目錄，不受相鄰專案檔案污染',
    '覆蓋崩潰的遞迴檢查也排除 _upgrade（文字與啟動器）',
    '非排除目錄確有同副檔名檔時仍判為覆蓋崩潰',
    'Windows 專案沒有 .command 不得告警',
    'macOS 專案沒有 .bat 不得告警',
    '中英 Windows-only／macOS-only／雙平台簽名皆可唯一辨認',
    '名字不同的自建 .bat／.command 不參與語言判定（⛔ 撞名的會參與，⇒ 見下一項）',
    '跨語言、混合、來源或專案缺簽名皆在檢查點前零寫入拒絕',
    '撞名的自建啟動器被擋下時，訊息指名了 `snapshot.bat`',
    'tool_my_index.py --help 不寫入索引',
    'tool_my_index.py 未知參數退出 2 且不寫入索引',
    'tool_sync_my_rules.py --help 不寫任何專案',
    '規則同步工具未知參數退出 2 且零寫入',
    '--root A 只補 A，不會改工具所在的 B',
    'scripts/harness/harness_status.json 是精確暫存例外',
    'scripts 其他位置的同名檔仍會阻擋替換',
    '非 scripts 套件的同路徑檔也不享有例外',
    'UPG-REC-10：暫存例外綁定精確套件與路徑',
    'UPG-REC-11：目標端獨有空目錄會阻擋整包替換',
    'target-only 檔會在檢查點與替換前被列名阻擋',
    '🔴 讀不回檢查點編號時⛔ 不覆蓋（收據閘門）',
    '舊專案工具拒絕時仍由下載版 checkpoint 完成 bootstrap，根目錄想法原封不動',
    '🔴 升級成功訊息交出持久還原收據與安全介面',
    '舊專案＋下載版＋非 scripts 套件可 restore，且先建立反向收據',
    '例行 diff 略過缺少的外平台啟動器，但明確 apply 仍可安裝',
    'UPG-REC-03：被 ignore 的同路徑手改會阻擋替換',
    'UPG-REC-04：assume-unchanged 與 skip-worktree 無法藏起 pre-image',
    'UPG-REC-05：apply 留下可驗證的 manifest 與 private Git ref',
    'UPG-REC-08：正常受追蹤的手改在 apply 前已被保存',
    'UPG-REC-06：差異與單檔還原成立，且有反向收據、reviewed 不動',
    'UPG-REC-07：路徑逃逸與目前檔案缺少時拒絕還原，且零收據寫入',
    'UPG-REC-09：CRLF 正規化依 Git 語意判斷，不會誤擋',
    'UPG-REC-12：遭竄改的 manifest 在使用前被拒絕',
    '相符 peer 缺失時 restore 不執行舊工具、零寫入，並指示重下載同版套件',
    '工具不認得的資料夾會被拒絕，且原封不動',
])

EXPECTED_EN_TEST_CASES = frozenset([
    'CHECKPOINT-STAT: same-stat content is saved without moving reviewed',
    'empty falsification condition warns',
    'empty rival hypothesis FAILs',
    'correct ledger does not false-alarm',
    'filled but unadjudicated still warns',
    'state outside the six FAILs',
    'retired and dormant do not false-alarm',
    '🟢/🔴 without basis FAILs',
    'citing an ID absent from the ledger FAILs',
    'citing an existing ID does not false-alarm',
    'a proposal file is exempted, and the exemption is printed',
    'deliberate blank with a reason reports as declared',
    'missing anchor FAILs',
    'ligatures and hyphenation do not false-alarm',
    'correct anchor does not false-alarm',
    "an empty extraction folder is not 'could not check'",
    'extractions with no manifest are INCOMPLETE',
    'unresolvable source citation must INCOMPLETE',
    'ambiguous multi-paper citation must INCOMPLETE',
    'explicit filename and year distinction do not false-alarm',
    'non-array manifest format error must INCOMPLETE',
    'substring author match must not confuse papers and must INCOMPLETE',
    'all claims skipping verification must INCOMPLETE',
    'substantive text mentioning the template marker must not be treated as blank',
    'author-field-only inference must be visible',
    'self-certification is caught',
    'gate-style requirements and honest disclosure do not false-alarm',
    'global appraisal warns',
    'duplicated long sentence across files warns',
    'duplicated sentence ending mid-line warns',
    'dangling section citation warns',
    'dangling short-form citation warns',
    'resolvable short-form citation does not false-alarm',
    'short-form citation in a .py header warns',
    'a heading inside a fenced block is not counted',
    'clean governance text does not false-alarm',
    'writing into deny FAILs',
    'with T0 in deny, editing a T0 FAILs',
    '🔴 with T0 ⛔ not in deny, editing a T0 must ⛔ NOT fail (it is switchable)',
    '🔴 solo project edits a ledger: must be listed, ⛔ must not FAIL',
    'solo project edits an ordinary file: ⛔ that WARN must not appear',
    'covered by _human: no false alarm, and the count is printed',
    'an in-scope change does not false-alarm',
    'committed out-of-scope modification FAILs',
    'committed and reverted change still leaves historical touch record',
    'zero changes after reviewed baseline does not false-alarm',
    'rename from allowed to denied FAILs',
    'rename from denied to allowed includes both endpoints and FAILs',
    'rename with both endpoints allowed does not false-alarm',
    'special path characters like Chinese, spaces, brackets, leading minus parse correctly',
    'cross-subtree move into project detects destination endpoint',
    'missing reviewed benchmark must INCOMPLETE and never claim pass',
    'reviewed not ancestor of HEAD must INCOMPLETE and never claim pass',
    'sensor execution keeps HEAD and reviewed strictly read-only',
    'assume-unchanged modified file must INCOMPLETE',
    'assume-unchanged unmodified file must INCOMPLETE and restore normal pass after flag removed',
    'skip-worktree modified and unmodified files must both INCOMPLETE',
    'new file in deny ignored by gitignore must INCOMPLETE',
    'pre-existing ignored file in deny must INCOMPLETE',
    'out of scope file ignored must INCOMPLETE while regular research attachments and caches pass',
    'conflict between deny and exclusion must explicitly report configuration conflict and external flags do not contaminate',
    'cross-prompt reference FAILs',
    'unassembled block slot FAILs',
    'a self-contained prompt does not false-alarm',
    'quoted prohibition does not false-alarm, and the exemption is printed',
    'content slot does not false-alarm',
    'generic does not run the DR clause list',
    'deep-research runs the DR clause list',
    'an artefact with no model field FAILs',
    'a family name alone FAILs',
    'a platform name FAILs',
    'a concrete model does not false-alarm',
    "a correct 'cannot read' declaration is not a defect",
    'a reference to a missing file FAILs',
    'reference climbing out of the folder FAILs',
    'relative reference inside the folder does not false-alarm',
    'a reference to an existing file does not false-alarm',
    'a format placeholder does not false-alarm',
    'an explicitly not-shipped reference is exempted, and printed',
    'directory absent: warn only',
    'directory freshly created and empty: warn only',
    'directory holds files but none match the glob: INCOMPLETE',
    'a one-character difference in the list FAILs',
    'same set in a different order does not false-alarm',
    'missing home is INCOMPLETE',
    'runtime and parse-time crashes are judged INCOMPLETE, not FAIL',
    'a framework rule missing from MY_RULES FAILs',
    'identical copies ⛔ must not false-alarm',
    'edited text with no override marker FAILs',
    "🔴 marker on the rule's own line FAILs (⛔ never counts as a reason)",
    'marker on its own line with a reason ⛔ must not FAIL',
    'a missing MY_RULES is INCOMPLETE (⛔ not a PASS)',
    '🔴 a misspelled key errors out and names the closest valid key',
    'a valid key ⛔ must not error',
    'an underscore key is for people and ⛔ must not error',
    '🔴 git says success with no output: INCOMPLETE, ⛔ no crash, ⛔ no misdiagnosis',
    '🔴 project inside a repo subdirectory: subtree seen, ⛔ outside not seen',
    '🔴 every subprocess decode names its encoding (27 files scanned, 0 exceptions)',
    '🔴 CP-09/tool: there was no reviewed tag, and there still is none',
    'CP-09/tool: ⛔ must not print the human-review banner',
    '🔴 CP-10/tool: an existing reviewed tag ⛔ must not move',
    '🔴 CP-09/ai: there was no reviewed tag, and there still is none',
    'CP-09/ai: ⛔ must not print the human-review banner',
    '🔴 CP-10/ai: an existing reviewed tag ⛔ must not move',
    'human mode still moves reviewed (⛔ the distinction is deliberate)',
    'tool mode without --tool-id/--operation must be refused (⛔ an anonymous tool is indistinguishable from a person)',
    '🔴 CP-14: when the reviewed tag cannot be created, human checkpoint ⛔ must not exit 0',
    "🔴 CP-14: ⛔ must not print the 'baseline moved' banner when it did not move",
    'CP-14: must say the baseline did not move',
    'CP-14: the commit itself is still made (⛔ no work is lost)',
    '🔴 CP-12: upgrade.py must pass --mode tool explicitly when calling checkpoint',
    '🔴 CP-15: upgrade.py must print a durable receipt id and checkpoint commit',
    '🔴 CP-15: upgrade.py ⛔ must not overwrite when the receipt is unreadable',
    '🔴 CP-15: recovery uses built-in receipt commands, ⛔ not raw git checkout',
    '🔴 every path sort passes an explicit key (scanned 26, 0 exceptions)',
    'the criterion catches the original v1.4.1 line',
    '🔴 every hashing module fixes its line endings (3 scanned, 0 exceptions)',
    'the criterion does FAIL a planted write site (⛔ falsifiable)',
    'a non-hashing module is ⛔ out of scope (⛔ no noise)',
    'packages on one version must report nothing',
    "Project D's state (profiles one version behind) is caught",
    'a missing package is a WARN, ⛔ never a version mismatch',
    'an unreadable marker is INCOMPLETE, ⛔ never a pass',
    'v1.9.0 alongside v1.10.0 must report VERSION_MISMATCH',
    '🔴 the message names ⛔ no target version (the sensor cannot see the source)',
    'version_packages matches upgrade.FRAMEWORK_DIRS',
    'SYNC-01: appends missing entries and states nothing existing was overwritten',
    'SYNC-02: drift alone writes nothing',
    '🔴 SYNC-02: prints real diff lines (starting `+` or `-`)',
    'SYNC-02: tells the user to paste the `+` lines, ⛔ never to replace the whole file',
    '🔴 SYNC-03: with both missing and drift, the append really happens',
    '🔴 SYNC-03: ⛔ must never write and claim nothing changed',
    'SYNC-03: the drift is still reported',
    'SYNC-05a: a valid override is untouched and reported as marked',
    '🔴 SYNC-05b: a marker with no reason must say the sensor will FAIL',
    'SYNC-06: nothing to do writes nothing and says it was computed',
    '🔴 SYNC-07: `--adopt` was ruled out; it must be rejected with zero write',
    '🔴 SYNC-08: no withdrawn flag survives in current instructions (29 files scanned)',
    'SYNC-08: the scan does FAIL a fake instruction (⛔ falsifiable)',
    'the retired list and the replaceable list ⛔ do not overlap',
    'a project that still has `policy/` gets it listed',
    'a new project without `policy/` ⛔ gets no retirement notice',
    'an empty orphan is still listed (it still reads as maintained)',
    'a never-generated index is INCOMPLETE (⛔ not a PASS)',
    'a freshly generated index ⛔ must not false-alarm',
    '🔴 a folder the user invented must appear in the index (⛔ not a whitelist)',
    'a file added after generation: must report stale',
    'a description pointing at a missing file: FAIL',
    '🔴 the file is there and merely excluded: ⛔ must not be called missing',
    "a broken notes file: INCOMPLETE (⛔ never 'there are no descriptions')",
    '🔴 the index is sorted by string (identical across platforms)',
    'a root glob stays at project root; a neighbouring project cannot contaminate it',
    'recursive collapse checks also exclude _upgrade (text and launcher)',
    'a real same-suffix file outside exclusions still means coverage collapse',
    'a Windows project may omit .command without an alarm',
    'a macOS project may omit .bat without an alarm',
    'Chinese and English Windows-only, macOS-only, and dual signatures resolve uniquely',
    'differently named project-owned .bat/.command files do not affect edition detection (⛔ colliding names do — see the next case)',
    'cross-edition, mixed, and missing signatures all fail before checkpoint with zero writes',
    'a colliding project-owned launcher is named in the refusal: `記錄快照.bat`',
    'tool_my_index.py --help does not write the index',
    'an unknown tool_my_index.py option exits 2 without writing',
    'tool_sync_my_rules.py --help writes to neither project',
    'an unknown rule-sync option exits 2 with zero writes',
    "--root A updates only A, never the tool's own project B",
    'scripts/harness/harness_status.json is the exact transient exception',
    'a namesake elsewhere under scripts still blocks replacement',
    'the same path outside the scripts package gets no exception',
    'UPG-REC-10: the transient exception is bound to exact package and path',
    'UPG-REC-11: a target-only empty directory blocks wholesale replacement',
    'target-only files are named and blocked before checkpoint or replacement',
    '🔴 no overwrite when the checkpoint id cannot be read back (receipt gate)',
    'the downloaded checkpoint bootstraps replacement while the old project tool refuses, and the root idea survives',
    '🔴 the completion message hands over a durable restore receipt and safe interface',
    'old project + download + non-scripts package restores with an undo receipt',
    'routine diff omits an absent foreign launcher, but explicit apply installs it',
    'UPG-REC-03: an ignored same-path hand edit blocks replacement',
    'UPG-REC-04: assume-unchanged and skip-worktree cannot hide a pre-image',
    'UPG-REC-05: apply persists a verifiable manifest and private Git ref',
    'UPG-REC-08: a normal tracked hand edit is captured before apply',
    'UPG-REC-06: diff and single-file restore work, with an undo receipt and stable reviewed tag',
    'UPG-REC-07: path escape and missing-current restore fail with zero receipt writes',
    'UPG-REC-09: CRLF normalization follows Git semantics without a false block',
    'UPG-REC-12: a tampered manifest is rejected before use',
    'restore with no compatible peer skips the old tool, writes nothing, and says to redownload',
    'a folder the tool does not recognise is refused and left untouched',
])

def check_mandatory_structure(root: pathlib.Path) -> list:
    """Verify mandatory 2-language entrypoints, per-language file counts, and source directories exist."""
    errors = []
    zh_dir = root / "Spark2Groundwork_zh"
    en_dir = root / "Spark2Groundwork_en"

    if not zh_dir.is_dir():
        errors.append("Mandatory directory missing: Spark2Groundwork_zh")
    if not en_dir.is_dir():
        errors.append("Mandatory directory missing: Spark2Groundwork_en")

    if errors:
        return errors

    # Check harness entrypoints
    mandatory_entries = [
        zh_dir / "scripts" / "harness" / "run_selftest.py",
        zh_dir / "scripts" / "harness" / "run_all_sensors.py",
        en_dir / "scripts" / "harness" / "run_selftest.py",
        en_dir / "scripts" / "harness" / "run_all_sensors.py",
    ]
    for ep in mandatory_entries:
        if not ep.is_file():
            errors.append(f"Mandatory harness entrypoint missing: {ep.relative_to(root).as_posix()}")

    # Check per-language launcher counts: exactly 6 .bat + 6 .command in zh, 6 .bat + 6 .command in en
    zh_bats = list(zh_dir.glob("*.bat"))
    zh_cmds = list(zh_dir.glob("*.command"))
    en_bats = list(en_dir.glob("*.bat"))
    en_cmds = list(en_dir.glob("*.command"))

    if len(zh_bats) != 6:
        errors.append(f"Spark2Groundwork_zh: expected exactly 6 .bat launchers, found {len(zh_bats)}")
    if len(zh_cmds) != 6:
        errors.append(f"Spark2Groundwork_zh: expected exactly 6 .command launchers, found {len(zh_cmds)}")
    if len(en_bats) != 6:
        errors.append(f"Spark2Groundwork_en: expected exactly 6 .bat launchers, found {len(en_bats)}")
    if len(en_cmds) != 6:
        errors.append(f"Spark2Groundwork_en: expected exactly 6 .command launchers, found {len(en_cmds)}")

    zh_bat_stems = {p.stem for p in zh_bats}
    zh_cmd_stems = {p.stem for p in zh_cmds}
    en_bat_stems = {p.stem for p in en_bats}
    en_cmd_stems = {p.stem for p in en_cmds}

    if zh_bat_stems != EXPECTED_ZH_LAUNCHERS:
        errors.append(f"Spark2Groundwork_zh .bat launcher stems mismatch: expected {EXPECTED_ZH_LAUNCHERS}, got {zh_bat_stems}")
    if zh_cmd_stems != EXPECTED_ZH_LAUNCHERS:
        errors.append(f"Spark2Groundwork_zh .command launcher stems mismatch: expected {EXPECTED_ZH_LAUNCHERS}, got {zh_cmd_stems}")
    if en_bat_stems != EXPECTED_EN_LAUNCHERS:
        errors.append(f"Spark2Groundwork_en .bat launcher stems mismatch: expected {EXPECTED_EN_LAUNCHERS}, got {en_bat_stems}")
    if en_cmd_stems != EXPECTED_EN_LAUNCHERS:
        errors.append(f"Spark2Groundwork_en .command launcher stems mismatch: expected {EXPECTED_EN_LAUNCHERS}, got {en_cmd_stems}")

    return errors


def check_line_endings(root: pathlib.Path) -> list:
    """Verify line endings according to platform & .gitattributes contract:
    - .bat: MUST be strictly CRLF (every \n MUST be preceded by \r, no standalone LF)
    - .command, .sh, .py: MUST be strictly LF (zero \r bytes anywhere)
    - docs/*.md: MUST be strictly LF (zero \r bytes anywhere)
    """
    errors = []
    bat_count = 0
    lf_count = 0

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in (".git", "__pycache__", ".pytest_cache", "venv") for part in p.parts):
            continue

        ext = p.suffix.lower()
        if ext == ".bat":
            bat_count += 1
            content = p.read_bytes()
            if not content:
                errors.append(f"{rel}: .bat file is empty")
                continue
            if b"\r\n" not in content:
                errors.append(f"{rel}: .bat file missing CRLF line endings")
                continue
            # Byte-by-byte check: every \n (0x0A) must be preceded by \r (0x0D)
            standalone_lf = 0
            for i, b in enumerate(content):
                if b == 0x0A:
                    if i == 0 or content[i - 1] != 0x0D:
                        standalone_lf += 1
            if standalone_lf > 0:
                errors.append(f"{rel}: .bat file contains {standalone_lf} standalone LF character(s) without preceding CR; MUST be strictly CRLF")
        elif ext in (".command", ".sh", ".py"):
            lf_count += 1
            content = p.read_bytes()
            if b"\r" in content:
                cr_count = content.count(b"\r")
                errors.append(f"{rel}: file ({ext}) contains {cr_count} CR character(s); MUST be strictly LF")
        elif ext == ".md" and "docs/" in rel:
            content = p.read_bytes()
            if b"\r" in content:
                cr_count = content.count(b"\r")
                errors.append(f"{rel}: docs markdown file contains {cr_count} CR character(s); MUST be strictly LF")

    if bat_count == 0:
        errors.append("No .bat files found to check line endings")
    if lf_count == 0:
        errors.append("No .command/.sh/.py files found to check line endings")

    return errors


def _validate_command_tokens(line: str, exp_lang: str, exp_action: str) -> tuple[bool, str]:
    """Tokenize and validate Python invocation line in a .command shell script."""
    try:
        tokens = shlex.split(line, posix=True)
    except Exception as e:
        return False, f"shlex split failed: {e}"
    if not tokens:
        return False, "empty invocation line"

    first = tokens[0].strip('"\'')
    if first not in ("$PY", "python", "python3", "${PY}"):
        return False, f"invalid interpreter token: {first}"
    if "-I" not in tokens or "-B" not in tokens:
        return False, "missing -I or -B isolation flags"
    if not any("check_environment.py" in t for t in tokens):
        return False, "target script is not check_environment.py"

    lang_indices = [i for i, t in enumerate(tokens) if t == "--lang"]
    if len(lang_indices) != 1:
        return False, f"expected exactly one --lang flag, found {len(lang_indices)}"
    idx_l = lang_indices[0]
    if idx_l + 1 >= len(tokens):
        return False, "missing argument for --lang"
    act_lang = tokens[idx_l + 1].strip('"\'')
    if act_lang != exp_lang:
        return False, f"invalid --lang argument: expected '{exp_lang}', got '{act_lang}'"

    action_indices = [i for i, t in enumerate(tokens) if t == "--action"]
    if len(action_indices) != 1:
        return False, f"expected exactly one --action flag, found {len(action_indices)}"
    idx_a = action_indices[0]
    if idx_a + 1 >= len(tokens):
        return False, "missing argument for --action"
    act_action = tokens[idx_a + 1].strip('"\'')
    if act_action != exp_action:
        return False, f"invalid --action argument: expected '{exp_action}', got '{act_action}'"

    return True, "ok"


def _validate_bat_tokens(line: str, exp_lang: str, exp_action: str) -> tuple[bool, str]:
    """Tokenize and validate Python invocation line in a .bat script."""
    try:
        tokens = shlex.split(line, posix=False)
    except Exception as e:
        return False, f"shlex split failed: {e}"
    clean_tokens = [t.strip('"\'') for t in tokens]
    if not clean_tokens:
        return False, "empty invocation line"

    first = clean_tokens[0].lower()
    if first not in ("%py%", "python", "python3", "%python%"):
        return False, f"invalid interpreter token: {first}"
    if "-I" not in clean_tokens or "-B" not in clean_tokens:
        return False, "missing -I or -B isolation flags"
    if not any("check_environment.py" in t for t in clean_tokens):
        return False, "target script is not check_environment.py"

    lang_indices = [i for i, t in enumerate(clean_tokens) if t == "--lang"]
    if len(lang_indices) != 1:
        return False, f"expected exactly one --lang flag, found {len(lang_indices)}"
    idx_l = lang_indices[0]
    if idx_l + 1 >= len(clean_tokens):
        return False, "missing argument for --lang"
    act_lang = clean_tokens[idx_l + 1]
    if act_lang != exp_lang:
        return False, f"invalid --lang argument: expected '{exp_lang}', got '{act_lang}'"

    action_indices = [i for i, t in enumerate(clean_tokens) if t == "--action"]
    if len(action_indices) != 1:
        return False, f"expected exactly one --action flag, found {len(action_indices)}"
    idx_a = action_indices[0]
    if idx_a + 1 >= len(clean_tokens):
        return False, "missing argument for --action"
    act_action = clean_tokens[idx_a + 1]
    if act_action != exp_action:
        return False, f"invalid --action argument: expected '{exp_action}', got '{act_action}'"

    return True, "ok"


def check_launchers(root: pathlib.Path) -> list:
    """Verify launcher contracts:
    - .command shebang must be #!/bin/bash with LF
    - .command / .bat argument containment: only --no-pause accepted; no unchecked passthrough (%* or "$@")
    - Reachability: no unconditional exit statement prior to the Python execution line
    - Tokenization: exact token matching for --lang and --action (rejects corruptions like zhx / savex)
    - Python invocation must include -I -B and target check_environment.py
    """
    errors = []

    for edition, mapping in LAUNCHER_CONTRACT.items():
        ed_dir = root / edition
        if not ed_dir.is_dir():
            errors.append(f"Launcher check cannot find edition directory: {edition}")
            continue

        for stem, (exp_lang, exp_action) in mapping.items():
            cmd_file = ed_dir / f"{stem}.command"
            bat_file = ed_dir / f"{stem}.bat"

            # Check .command
            if not cmd_file.is_file():
                errors.append(f"Missing expected .command launcher: {cmd_file.relative_to(root).as_posix()}")
            else:
                rel = cmd_file.relative_to(root).as_posix()
                content_bytes = cmd_file.read_bytes()
                first_line = content_bytes.split(b"\n")[0]
                if first_line != b"#!/bin/bash":
                    errors.append(f"{rel}: invalid shebang: expected b'#!/bin/bash', got {first_line!r}")

                text = content_bytes.decode("utf-8", errors="replace")
                if '"$@"' in text or ' $*' in text or ' $@' in text:
                    errors.append(f"{rel}: forbidden unvalidated argument passthrough ($@ or $*) detected")
                if "--no-pause" not in text:
                    errors.append(f"{rel}: missing --no-pause argument handler")

                # Parse lines for reachability and valid invocation
                in_func = False
                if_depth = 0
                unconditional_exit = None
                valid_invocation_found = False

                for lineno, line in enumerate(text.splitlines(), start=1):
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    if "() {" in s or s.endswith("()"):
                        in_func = True
                        continue
                    if in_func:
                        if s == "}":
                            in_func = False
                        continue
                    if s.startswith("if ") or s.startswith("if ["):
                        if not s.endswith("; fi") and " fi" not in s:
                            if_depth += 1
                    elif s == "fi" or s.endswith("; fi"):
                        if if_depth > 0:
                            if_depth -= 1

                    if if_depth == 0 and not in_func and not valid_invocation_found:
                        # Check redirection writing to files or json
                        if re.search(r'>\s*"?scripts[\\/]', s) or re.search(r'>\s*"?.*\.json', s):
                            errors.append(f"{rel}: forbidden file write redirection prior to Python invocation at line {lineno}: {s}")
                        # Check early success exit before Python
                        if re.search(r'\bexit\s+0\b', s):
                            errors.append(f"{rel}: forbidden early exit with code 0 prior to Python invocation at line {lineno}: {s}")
                            unconditional_exit = (lineno, s)
                        # Check tautological conditions
                        if re.search(r'if\s+\[\s*(?:1\s+-eq\s+1|"([^"]+)"\s*=\s*"\1"|true)\s*\]', s):
                            errors.append(f"{rel}: forbidden tautological condition prior to Python invocation at line {lineno}: {s}")
                            unconditional_exit = (lineno, s)
                        if s == "exit" or s.startswith("exit ") or s.startswith("exit;"):
                            if unconditional_exit is None:
                                unconditional_exit = (lineno, s)

                    # Look for Python invocation
                    if ("$PY" in s or "python" in s) and "check_environment.py" in s:
                        if unconditional_exit is not None:
                            errors.append(
                                f"{rel}: unreachable python invocation at line {lineno}; "
                                f"unconditional exit statement encountered earlier at line {unconditional_exit[0]}: {unconditional_exit[1]}"
                            )
                            break
                        ok, reason = _validate_command_tokens(s, exp_lang, exp_action)
                        if not ok:
                            errors.append(f"{rel}: invalid invocation at line {lineno}: {reason}")
                        else:
                            valid_invocation_found = True
                            break

                if not valid_invocation_found and unconditional_exit is None:
                    errors.append(f"{rel}: missing valid executable Python invocation for check_environment.py --lang {exp_lang} --action {exp_action} with -I -B")

            # Check .bat
            if not bat_file.is_file():
                errors.append(f"Missing expected .bat launcher: {bat_file.relative_to(root).as_posix()}")
            else:
                rel = bat_file.relative_to(root).as_posix()
                text = bat_file.read_text(encoding="utf-8", errors="replace")
                if "%*" in text:
                    errors.append(f"{rel}: forbidden unvalidated argument passthrough (%*) detected")
                if "--no-pause" not in text:
                    errors.append(f"{rel}: missing --no-pause argument handler")

                unconditional_exit = None
                valid_invocation_found = False
                in_label = False

                for lineno, line in enumerate(text.splitlines(), start=1):
                    s = line.strip()
                    if not s or s.startswith("::") or s.lower().startswith("rem "):
                        continue
                    if s.startswith(":"):
                        in_label = True
                        continue

                    if not in_label and not valid_invocation_found:
                        s_lower = s.lower()
                        # Check redirection writing to files or json
                        if re.search(r'>\s*"?scripts[\\/]', s, re.IGNORECASE) or re.search(r'>\s*"?.*\.json', s, re.IGNORECASE):
                            errors.append(f"{rel}: forbidden file write redirection prior to Python invocation at line {lineno}: {s}")
                        # Check tautological conditions (e.g. if 1==1 or if a==a)
                        if re.search(r'\bif\s+([^\s=]+)==\1\b', s_lower):
                            errors.append(f"{rel}: forbidden tautological condition prior to Python invocation at line {lineno}: {s}")
                            unconditional_exit = (lineno, s)
                        # Check early success exit before Python
                        if re.search(r'\bexit(?:\s*\/b)?\s+0\b', s_lower):
                            errors.append(f"{rel}: forbidden early exit with code 0 prior to Python invocation at line {lineno}: {s}")
                            unconditional_exit = (lineno, s)
                        if not s_lower.startswith("if "):
                            if s_lower == "exit" or s_lower.startswith("exit ") or s_lower.startswith("exit/b") or s_lower.startswith("goto "):
                                if unconditional_exit is None:
                                    unconditional_exit = (lineno, s)

                    if ("%py%" in s.lower() or "python" in s.lower()) and "check_environment.py" in s:
                        if unconditional_exit is not None:
                            errors.append(
                                f"{rel}: unreachable python invocation at line {lineno}; "
                                f"unconditional exit statement encountered earlier at line {unconditional_exit[0]}: {unconditional_exit[1]}"
                            )
                            break
                        ok, reason = _validate_bat_tokens(s, exp_lang, exp_action)
                        if not ok:
                            errors.append(f"{rel}: invalid invocation at line {lineno}: {reason}")
                        else:
                            valid_invocation_found = True
                            break

                if not valid_invocation_found and unconditional_exit is None:
                    errors.append(f"{rel}: missing valid executable Python invocation for check_environment.py --lang {exp_lang} --action {exp_action} with -I -B")

    return errors


def check_bash_syntax(root: pathlib.Path) -> tuple:
    """Run bash -n on all .command and .sh files if bash is available with timeout=15.
    Returns: (errors, status_message, is_incomplete)
    """
    errors = []
    bash_path = shutil.which("bash")
    if not bash_path:
        return errors, "INCOMPLETE: bash not found in PATH (shell syntax cannot be verified)", True

    scripts = list(root.rglob("*.command")) + list(root.rglob("*.sh"))
    if not scripts:
        return ["No shell scripts (.command / .sh) found to syntax check"], "FAIL: zero shell scripts found", False

    checked = 0
    for p in scripts:
        rel = p.relative_to(root).as_posix()
        try:
            r = subprocess.run([bash_path, "-n", str(p)], capture_output=True, text=True, timeout=15)
            if r.returncode != 0:
                errors.append(f"{rel}: bash syntax error:\n{r.stderr}")
        except subprocess.TimeoutExpired as e:
            errors.append(f"{rel}: bash syntax check timed out after 15s (cmd: {e.cmd})")
        checked += 1
    return errors, f"PASSED ({checked} shell scripts syntax-checked)", False


def check_python_ast(root: pathlib.Path) -> list:
    """Verify that all Python files parse cleanly and do not use syntax unsupported by Python 3.9."""
    errors = []
    checked = 0
    for p in root.rglob("*.py"):
        if any(part in (".git", "__pycache__", ".pytest_cache", "venv") for part in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p), feature_version=(3, 9))
        except SyntaxError as e:
            errors.append(f"{rel}:{e.lineno or '?'}: Python SyntaxError (incompatible with Python 3.9): {e.msg}")
            continue

        match_types = tuple(
            getattr(ast, name)
            for name in ("Match", "match_case")
            if hasattr(ast, name)
        )
        for node in ast.walk(tree):
            if match_types and isinstance(node, match_types):
                errors.append(f"{rel}:{node.lineno}: structural pattern matching (match statement) is unsupported in Python 3.9")
        checked += 1

    if checked == 0:
        errors.append("No Python files found to parse for AST syntax compatibility")
    return errors


def check_cleanliness(root: pathlib.Path) -> list:
    """Ensure no uncataloged bytecode, pytest caches, or runtime files exist in worktree."""
    errors = []
    forbidden_names = {".pytest_cache", "__pycache__", "harness_status.json"}
    for p in root.rglob("*"):
        if any(part in (".git", "venv") for part in p.parts):
            continue
        if p.name in forbidden_names or p.name.endswith(".pyc"):
            errors.append(f"Forbidden build/cache/status artifact found in repository tree: {p.relative_to(root).as_posix()}")
    return errors



# Six existing negative-fixture families. This samples regression propagation,
# not security against a program that can inspect and forge the probe itself.
FAULT_CASES = {'zh': {'sensor_conjecture_ledger.py': {'case': '競爭解釋為空須 FAIL', 'code': 1, 'fixture': 'conj_norival'}, 'sensor_claim_ledger.py': {'case': '錨點查無須 FAIL', 'code': 1, 'fixture': 'claim_ghost'}, 'sensor_self_certification.py': {'case': '自我背書須抓到', 'code': 1, 'fixture': 'selfcert_bad'}, 'sensor_model_attribution.py': {'case': '產出物無型號欄須 FAIL', 'code': 1, 'fixture': 'attrib_missing'}, 'sensor_reference_integrity.py': {'case': '引用不存在的檔案須 FAIL', 'code': 1, 'fixture': 'ref_dangling'}, 'sensor_clause_sync.py': {'case': '條款清單一字之差須 FAIL', 'code': 1, 'fixture': 'sync_drift'}}, 'en': {'sensor_conjecture_ledger.py': {'case': 'empty rival hypothesis FAILs', 'code': 1, 'fixture': 'conj_norival'}, 'sensor_claim_ledger.py': {'case': 'missing anchor FAILs', 'code': 1, 'fixture': 'claim_ghost'}, 'sensor_self_certification.py': {'case': 'self-certification is caught', 'code': 1, 'fixture': 'selfcert_bad'}, 'sensor_model_attribution.py': {'case': 'an artefact with no model field FAILs', 'code': 1, 'fixture': 'attrib_missing'}, 'sensor_reference_integrity.py': {'case': 'a reference to a missing file FAILs', 'code': 1, 'fixture': 'ref_dangling'}, 'sensor_clause_sync.py': {'case': 'a one-character difference in the list FAILs', 'code': 1, 'fixture': 'sync_drift'}}}


def check_fault_propagation(target, lang, baseline_output, env):
    """Require a named passing case to fail after a loaded sensor is changed.

    The selector and diagnostic receipt are observable to the child. Neither is
    an authentication mechanism. Review runner/checker changes independently.
    """
    errors, records = [], []
    sensor = secrets.choice(sorted(FAULT_CASES[lang]))
    case = FAULT_CASES[lang][sensor]
    if ('✅ ' + case['case']) not in baseline_output:
        return ['FAULT_REGRESSION_FAILURE: named baseline case did not pass'], records
    with tempfile.TemporaryDirectory(prefix='ci0_') as scratch:
        fault = pathlib.Path(scratch) / 'project'
        shutil.copytree(target, fault)
        mutant = fault / 'scripts/harness' / sensor
        loaded = pathlib.Path(scratch) / 'loaded.jsonl'
        if not mutant.is_file():
            return ['FAULT_REGRESSION_FAILURE: missing sensor ' + sensor], records
        before = hashlib.sha256(mutant.read_bytes()).hexdigest()
        # Two controlled wrong return codes, both distinct from the expected one.
        wrong_code = secrets.choice((0, 3))
        code = ("import json, pathlib, sys\n"
                + "with pathlib.Path(" + repr(str(loaded)) + ").open('a', encoding='utf-8') as f:\n"
                + "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                + "raise SystemExit(" + str(wrong_code) + ")\n")
        mutant.write_text(code, encoding='utf-8')
        argv = [sys.executable, '-B', str(fault / 'scripts/harness/run_selftest.py')]
        try:
            r = subprocess.run(argv, cwd=fault / 'scripts/harness', env=env,
                               capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=180)
        except subprocess.TimeoutExpired as exc:
            return ['FAULT_REGRESSION_FAILURE: selftest timed out'], [{
                'step': 'fault_' + lang, 'argv': argv, 'returncode': -1,
                'stdout': exc.stdout or b'', 'stderr': exc.stderr or b''}]
        invocations = []
        try:
            invocations = [json.loads(line) for line in loaded.read_text('utf-8').splitlines()]
        except (OSError, ValueError):
            pass
        fixture = str(fault / 'scripts/harness/selftest' / case['fixture'])
        was_loaded = ['--root', fixture] in invocations
        marker = (' (expected exit ' if lang == 'en' else '（期望 exit ')
        detail = (f"{case['code']}, got {wrong_code}" if lang == 'en'
                  else f"{case['code']}，實得 {wrong_code}")
        expected_failure = '❌ ' + case['case'] + marker + detail
        named_failure = any(line.strip().startswith(expected_failure)
                            for line in r.stdout.splitlines())
        still_passes = any(line.strip() == '✅ ' + case['case']
                           for line in r.stdout.splitlines())
        success = r.returncode == 1 and was_loaded and named_failure and not still_passes
        records.append({'step': 'fault_' + lang, 'argv': argv, 'returncode': r.returncode,
                        'stdout': r.stdout, 'stderr': r.stderr, 'sensor': sensor,
                        'case': case, 'injected_exit': wrong_code,
                        'before_sha256': before,
                        'after_sha256': hashlib.sha256(mutant.read_bytes()).hexdigest(),
                        'invocations': invocations, 'named_failure': named_failure,
                        'loaded_selected_fixture': was_loaded, 'passed': success})
        if not success:
            errors.append('FAULT_REGRESSION_FAILURE: ' + sensor + ': expected loaded '
                          'fixture and named case failure, not generic failure text')
    return errors, records


def check_disposable_projects(root: pathlib.Path) -> tuple:
    """Run bilingual selftests, aggregate sensors, direct individual sensors,
    and platform native launchers in clean temporary disposable git worktrees.
    Returns: (errors, stats, execution_records)
    """
    errors = []
    stats = {}
    records = []

    for dirname, lang in [("Spark2Groundwork_zh", "zh"), ("Spark2Groundwork_en", "en")]:
        src = root / dirname
        if not src.is_dir():
            errors.append(f"Disposable project test: directory missing: {src}")
            continue

        tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"ci0_{lang}_"))
        try:
            target = tmp_dir / dirname
            shutil.copytree(src, target)

            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")

            # Git initialization sequence - check every step with timeout=30
            git_steps = [
                ["git", "init"],
                ["git", "config", "user.name", "CI-0 Runner"],
                ["git", "config", "user.email", "ci0@example.com"],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit"],
                ["git", "tag", "reviewed"],
            ]
            git_failed = False
            for cmd in git_steps:
                try:
                    r = subprocess.run(cmd, cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30)
                    records.append({"step": "git", "argv": cmd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr})
                    if r.returncode != 0:
                        errors.append(f"{dirname} git step failed: {' '.join(cmd)} (code {r.returncode}):\n{r.stderr}")
                        git_failed = True
                        break
                except subprocess.TimeoutExpired as e:
                    errors.append(f"{dirname} git step timed out after 30s: {' '.join(cmd)}")
                    records.append({"step": "git", "argv": cmd, "returncode": -1, "stdout": e.stdout or "", "stderr": e.stderr or ""})
                    git_failed = True
                    break

            if git_failed:
                continue

            # Run selftest with timeout=180
            selftest_py = target / "scripts" / "harness" / "run_selftest.py"
            if not selftest_py.exists():
                errors.append(f"{dirname} missing harness selftest script: {selftest_py}")
                continue

            cmd_st = [sys.executable, "-B", str(selftest_py)]
            try:
                r_st = subprocess.run(cmd_st, cwd=selftest_py.parent, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=180)
                records.append({"step": f"selftest_{lang}", "argv": cmd_st, "returncode": r_st.returncode, "stdout": r_st.stdout, "stderr": r_st.stderr})
            except subprocess.TimeoutExpired as e:
                errors.append(f"{dirname} run_selftest.py timed out after 180s (cmd: {cmd_st})")
                records.append({"step": f"selftest_{lang}", "argv": cmd_st, "returncode": -1, "stdout": e.stdout or "", "stderr": e.stderr or ""})
                continue

            if r_st.returncode != 0:
                errors.append(f"{dirname} run_selftest.py failed with exit code {r_st.returncode}:\n{r_st.stdout}\n{r_st.stderr}")

            # Structured parsing of selftest stdout
            out_st = r_st.stdout or ""
            if "NO TESTS EXECUTED" in out_st or not out_st.strip():
                errors.append(f"{dirname} run_selftest.py produced empty or fake execution output (detected NO TESTS EXECUTED)")
            else:
                if lang == "zh":
                    m = re.search(r"通過\s+(\d+)\s+項｜失敗\s+(\d+)\s+項", out_st)
                    has_pass = "結果：自測全數通過" in out_st
                else:
                    m = re.search(r"passed\s+(\d+)\s+\|\s+failed\s+(\d+)", out_st)
                    has_pass = "Result: all self-tests passed" in out_st

                if not m or not has_pass:
                    errors.append(f"{dirname} run_selftest.py structured pass marker missing or unparseable in stdout")
                else:
                    passed_cnt = int(m.group(1))
                    failed_cnt = int(m.group(2))
                    stats[f"{lang}_selftest_passed"] = passed_cnt
                    stats[f"{lang}_selftest_failed"] = failed_cnt
                    if failed_cnt > 0:
                        errors.append(f"{dirname} run_selftest.py reported {failed_cnt} failed tests")
                    # Exact 186 contract (kills under_run_165)
                    if passed_cnt != 186:
                        errors.append(f"{dirname} run_selftest.py under-run or count mismatch: expected EXACTLY 186 tests, parsed {passed_cnt}")

                    # Verify individual item test lines (each test prints ✅ on pass)
                    passed_items = []
                    failed_items = []
                    for line in out_st.splitlines():
                        s = line.strip()
                        if s.startswith("✅"):
                            passed_items.append(s[1:].strip())
                        elif s.startswith("❌"):
                            failed_items.append(s[1:].strip())

                    if failed_items:
                        errors.append(f"{dirname} run_selftest.py has {len(failed_items)} failing item(s): {failed_items[:3]}")

                    if len(passed_items) != 186:
                        errors.append(
                            f"{dirname} run_selftest.py individual passed test items count ({len(passed_items)}) "
                            f"is not EXACTLY 186"
                        )
                    elif len(set(passed_items)) != 186:
                        errors.append(
                            f"{dirname} run_selftest.py contains duplicate test executions: "
                            f"{len(passed_items)} total items, but only {len(set(passed_items))} unique"
                        )

                    # Exact set comparison with version-controlled test registry (kills forged_exact_186)
                    exp_cases = EXPECTED_ZH_TEST_CASES if lang == "zh" else EXPECTED_EN_TEST_CASES
                    actual_set = set(passed_items)
                    if actual_set != exp_cases:
                        missing = exp_cases - actual_set
                        unexpected = actual_set - exp_cases
                        errors.append(
                            f"{dirname} run_selftest.py test cases mismatch with expected registry: "
                            f"{len(missing)} missing ({list(missing)[:3]}), "
                            f"{len(unexpected)} unexpected ({list(unexpected)[:3]})"
                        )

                    # Verify required test names/IDs
                    req_list = REQUIRED_ZH_TESTS if lang == "zh" else REQUIRED_EN_TESTS
                    for req in req_list:
                        if not any(req in item for item in passed_items):
                            errors.append(f"{dirname} run_selftest.py missing required test item: {req}")

            # Only a clean baseline can support the negative control.
            if not any(dirname in err and 'run_selftest.py' in err for err in errors):
                fault_errors, fault_records = check_fault_propagation(target, lang, out_st, env)
                errors.extend(dirname + ' ' + err for err in fault_errors)
                records.extend(fault_records)
                stats[lang + '_fault_regression_passed'] = not fault_errors

            # Run aggregate sensors runner with timeout=60
            sensors_py = target / "scripts" / "harness" / "run_all_sensors.py"
            if not sensors_py.exists():
                errors.append(f"{dirname} missing harness sensors script: {sensors_py}")
                continue

            # Pre-clean: delete any existing harness_status.json to avoid stale status reuse
            status_file = target / "scripts" / "harness" / "harness_status.json"
            if status_file.exists():
                status_file.unlink()

            cmd_sn = [sys.executable, "-B", str(sensors_py)]
            try:
                r_sn = subprocess.run(cmd_sn, cwd=sensors_py.parent, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
                records.append({"step": f"sensors_{lang}", "argv": cmd_sn, "returncode": r_sn.returncode, "stdout": r_sn.stdout, "stderr": r_sn.stderr})
            except subprocess.TimeoutExpired as e:
                errors.append(f"{dirname} run_all_sensors.py timed out after 60s (cmd: {cmd_sn})")
                records.append({"step": f"sensors_{lang}", "argv": cmd_sn, "returncode": -1, "stdout": e.stdout or "", "stderr": e.stderr or ""})
                continue

            if r_sn.returncode != 0:
                errors.append(f"{dirname} run_all_sensors.py failed with exit code {r_sn.returncode}:\n{r_sn.stdout}\n{r_sn.stderr}")

            out_sn = r_sn.stdout or ""
            sensors_run = 0
            if "NO TESTS EXECUTED" in out_sn or not out_sn.strip():
                errors.append(f"{dirname} run_all_sensors.py produced empty or fake execution output")
            else:
                if lang == "zh":
                    m_sn = re.search(r"✅\s+總結：PASS（(\d+)\s+支已執行）", out_sn)
                else:
                    m_sn = re.search(r"✅\s+SUMMARY:\s+PASS\s+\((\d+)\s+sensors run\)", out_sn)

                if not m_sn:
                    errors.append(f"{dirname} run_all_sensors.py PASS summary marker missing in stdout:\n{out_sn}")
                else:
                    sensors_run = int(m_sn.group(1))
                    stats[f"{lang}_sensors_run"] = sensors_run
                    if sensors_run != 10:
                        errors.append(f"{dirname} run_all_sensors.py executed {sensors_run} sensors; expected EXACTLY 10")

            # Validate newly generated harness_status.json in target
            aggregate_sensor_map = {}
            if not status_file.is_file():
                errors.append(f"{dirname} harness_status.json was not generated by run_all_sensors.py")
            else:
                try:
                    status_data = json.loads(status_file.read_text(encoding="utf-8"))
                    worst = status_data.get("worst")
                    results = status_data.get("results", [])
                    if worst != 0:
                        errors.append(f"{dirname} harness_status.json indicates non-zero worst status: {worst}")
                    if len(results) != 10:
                        errors.append(f"{dirname} harness_status.json recorded {len(results)} sensor results; expected EXACTLY 10")

                    actual_sensors = [r.get("sensor") for r in results if isinstance(r, dict)]
                    if len(actual_sensors) != 10:
                        errors.append(f"{dirname} harness_status.json has invalid entries missing 'sensor' key")
                    elif len(set(actual_sensors)) != 10:
                        errors.append(f"{dirname} harness_status.json contains duplicate sensor names: {actual_sensors}")
                    elif set(actual_sensors) != EXPECTED_SENSORS:
                        unknown = set(actual_sensors) - EXPECTED_SENSORS
                        missing = EXPECTED_SENSORS - set(actual_sensors)
                        errors.append(f"{dirname} harness_status.json sensor mismatch: unknown={unknown}, missing={missing}")

                    for r in results:
                        if isinstance(r, dict) and "sensor" in r:
                            aggregate_sensor_map[r["sensor"]] = r.get("code")

                    if any(r.get("code") != 0 for r in results if isinstance(r, dict)):
                        errors.append(f"{dirname} harness_status.json contains failing sensors: {results}")

                    if sensors_run != 10 or len(results) != 10 or len(EXPECTED_SENSORS) != 10:
                        errors.append(
                            f"{dirname} sensor three-way count mismatch: summary={sensors_run}, "
                            f"json={len(results)}, expected={len(EXPECTED_SENSORS)}"
                        )
                except Exception as ex:
                    errors.append(f"{dirname} harness_status.json invalid JSON: {ex}")

            # Direct individual sensor execution (kills fake run_all_sensors.py self-reporting)
            direct_executed_count = 0
            for sname in sorted(EXPECTED_SENSORS):
                spath = target / "scripts" / "harness" / sname
                if not spath.is_file():
                    errors.append(f"{dirname} individual sensor missing: {spath}")
                    continue
                cmd_single = [sys.executable, "-B", str(spath), "--root", str(target)]
                try:
                    r_ind = subprocess.run(cmd_single, cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30)
                    records.append({"step": f"direct_sensor_{lang}_{sname}", "argv": cmd_single, "returncode": r_ind.returncode, "stdout": r_ind.stdout, "stderr": r_ind.stderr})
                    direct_executed_count += 1
                    if r_ind.returncode != 0:
                        errors.append(f"{dirname} direct execution of {sname} failed with exit code {r_ind.returncode}:\n{r_ind.stderr}")
                    if sname in aggregate_sensor_map and aggregate_sensor_map[sname] != r_ind.returncode:
                        errors.append(f"{dirname} sensor {sname} direct exit code {r_ind.returncode} differs from aggregate status code {aggregate_sensor_map[sname]}")
                except subprocess.TimeoutExpired as e:
                    errors.append(f"{dirname} direct execution of {sname} timed out after 30s")
                    records.append({"step": f"direct_sensor_{lang}_{sname}", "argv": cmd_single, "returncode": -1, "stdout": e.stdout or "", "stderr": e.stderr or ""})

            if direct_executed_count != 10:
                errors.append(f"{dirname} directly executed {direct_executed_count} sensors; expected EXACTLY 10")

            # Platform-native launcher reachability; fresh receipts prevent accidental stale reuse.
            # Same-privilege scripts can forge receipts. Independent code review is required.
            check_env_py = target / "scripts" / "harness" / "check_environment.py"
            legacy_receipt_file = target / "scripts" / "harness" / "launcher_receipt.json"
            if legacy_receipt_file.exists():
                legacy_receipt_file.unlink(missing_ok=True)

            if check_env_py.is_file() and dirname in LAUNCHER_CONTRACT:
                orig_check_env = check_env_py.read_text(encoding="utf-8")
                try:
                    invocations = [(stem, lang_action, expected_exit)
                                   for stem, lang_action in LAUNCHER_CONTRACT[dirname].items()
                                   for expected_exit in (0, 1, 2)]
                    for stem, (exp_l, exp_a), expected_exit in invocations:
                        challenge = secrets.token_hex(16)
                        inv_id = uuid.uuid4().hex
                        receipt_file = target / 'scripts/harness' / f'.receipt_{inv_id}.json'
                        # Embed diagnostics in this invocation's stub, not caller-supplied
                        # env. This prevents accidental stale environment reuse, but a
                        # malicious launcher can still read the stub: not authentication.
                        stub_code = (
                            "import sys, json, pathlib\n"
                            + "pathlib.Path(" + repr(str(receipt_file)) + ").write_text(json.dumps({"
                            + "'challenge': " + repr(challenge) + ", 'invocation_id': " + repr(inv_id)
                            + ", 'argv': sys.argv[1:], 'python': sys.executable, 'version': sys.version"
                            + "}), encoding='utf-8')\n"
                            + "raise SystemExit(" + str(expected_exit) + ")\n"
                        )
                        check_env_py.write_text(stub_code, encoding='utf-8')
                        launcher_env = dict(env)
                        for key in list(launcher_env):
                            if key.startswith('SPARK2GW_LAUNCHER_'):
                                del launcher_env[key]

                        if sys.platform == "win32":
                            bat_path = target / f"{stem}.bat"
                            if not bat_path.is_file():
                                errors.append(f'{dirname} missing native launcher: {stem}.bat')
                                continue
                            run_cmd = [str(bat_path), "--no-pause"]
                        else:
                            cmd_path = target / f"{stem}.command"
                            if not cmd_path.is_file():
                                errors.append(f'{dirname} missing native launcher: {stem}.command')
                                continue
                            bash_bin = shutil.which("bash") or "bash"
                            run_cmd = [bash_bin, str(cmd_path), "--no-pause"]

                        try:
                            r_l = subprocess.run(
                                run_cmd,
                                cwd=target,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                                env=launcher_env,
                                timeout=30,
                            )
                            records.append({
                                "step": f"native_launcher_{lang}_{stem}_{expected_exit}",
                                "expected_exit": expected_exit,
                                "argv": run_cmd,
                                "returncode": r_l.returncode,
                                "stdout": r_l.stdout,
                                "stderr": r_l.stderr,
                            })
                            if r_l.returncode != expected_exit:
                                errors.append(f"{dirname} native launcher {stem} expected exit {expected_exit}, got {r_l.returncode}:\n{r_l.stderr}")

                            # Detect forbidden predictable legacy receipt
                            if legacy_receipt_file.exists():
                                errors.append(
                                    f"{dirname} native launcher {stem} wrote to forbidden legacy/predictable "
                                    f"receipt path 'launcher_receipt.json'; this invocation's fresh receipt was not used"
                                )
                                legacy_receipt_file.unlink(missing_ok=True)

                            # Validate single-use challenge receipt
                            if not receipt_file.is_file():
                                errors.append(
                                    f"{dirname} native launcher {stem} did not produce challenge receipt at {receipt_file.name} "
                                    f"(Python target not reached; early exit detected)"
                                )
                            else:
                                try:
                                    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
                                    # Consume and destroy receipt immediately to prevent replay attacks
                                    receipt_file.unlink(missing_ok=True)

                                    records[-1]['receipt'] = receipt_data
                                    recv_ch = receipt_data.get("challenge")
                                    recv_inv = receipt_data.get("invocation_id")
                                    argv_passed = receipt_data.get("argv", [])

                                    if not recv_ch or recv_ch != challenge:
                                        errors.append(
                                            f"{dirname} native launcher {stem} challenge mismatch or missing: "
                                            f"expected '{challenge}', got '{recv_ch}'"
                                        )
                                    if not recv_inv or recv_inv != inv_id:
                                        errors.append(
                                            f"{dirname} native launcher {stem} invocation_id mismatch: "
                                            f"expected '{inv_id}', got '{recv_inv}'"
                                        )

                                    if "--lang" not in argv_passed or "--action" not in argv_passed:
                                        errors.append(f"{dirname} native launcher {stem} invoked Python without required flags: {argv_passed}")
                                    else:
                                        idx_l = argv_passed.index("--lang")
                                        idx_a = argv_passed.index("--action")
                                        act_l = argv_passed[idx_l + 1] if idx_l + 1 < len(argv_passed) else None
                                        act_a = argv_passed[idx_a + 1] if idx_a + 1 < len(argv_passed) else None
                                        if act_l != exp_l:
                                            errors.append(f"{dirname} native launcher {stem} passed --lang '{act_l}'; expected '{exp_l}'")
                                        if act_a != exp_a:
                                            errors.append(f"{dirname} native launcher {stem} passed --action '{act_a}'; expected '{exp_a}'")
                                        if len(argv_passed) != 4:
                                            extra = [t for i, t in enumerate(argv_passed) if i not in (idx_l, idx_l + 1, idx_a, idx_a + 1)]
                                            errors.append(f"{dirname} native launcher {stem} passed unexpected additional arguments: {extra}")
                                except Exception as ex:
                                    errors.append(f"{dirname} native launcher {stem} produced invalid receipt JSON: {ex}")
                        except subprocess.TimeoutExpired as e:
                            errors.append(f"{dirname} native launcher {stem} timed out after 30s")
                            records.append({"step": f"native_launcher_{lang}_{stem}", "argv": run_cmd, "returncode": -1, "stdout": e.stdout or "", "stderr": e.stderr or ""})
                        finally:
                            if receipt_file.exists():
                                receipt_file.unlink(missing_ok=True)
                finally:
                    check_env_py.write_text(orig_check_env, encoding="utf-8")
                    if legacy_receipt_file.exists():
                        legacy_receipt_file.unlink(missing_ok=True)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return errors, stats, records


def main() -> int:
    parser = argparse.ArgumentParser(description="Repository & Launcher Hygiene Checker (CI-0 r6)")
    parser.add_argument("--root", default=None, help="Root directory of the repository")
    parser.add_argument("--check-structure", action="store_true", help="Check mandatory 2-language directory and launcher counts")
    parser.add_argument("--check-line-endings", action="store_true", help="Check .gitattributes CRLF/LF line endings")
    parser.add_argument("--check-launchers", action="store_true", help="Check launcher shebangs, reachability, and token arguments")
    parser.add_argument("--check-syntax", action="store_true", help="Check shell syntax with bash -n")
    parser.add_argument("--check-ast", action="store_true", help="Check Python 3.9 syntax compatibility")
    parser.add_argument("--check-cleanliness", action="store_true", help="Check for uncataloged cache and .pyc files")
    parser.add_argument("--check-disposable", action="store_true", help="Run selftests, dual sensors, and launchers in disposable git repositories")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    args = parser.parse_args()

    if args.root:
        root = pathlib.Path(args.root).resolve()
    else:
        here = pathlib.Path(__file__).resolve().parent
        if (here.parent / "Spark2Groundwork_zh").exists():
            root = here.parent
        else:
            root = pathlib.Path.cwd().resolve()

    run_all = args.all or not any([
        args.check_structure, args.check_line_endings, args.check_launchers,
        args.check_syntax, args.check_ast, args.check_cleanliness, args.check_disposable
    ])

    total_errors = []
    incomplete = False
    print("=== Spark2Groundwork v1.4.5 Hygiene Check (CI-0 r6) ===")
    print(f"Target Root: {root}\nPython: {sys.version}\nExecutable: {sys.executable}\nPlatform: {sys.platform}")

    # Step 1: Mandatory structure check
    if run_all or args.check_structure or args.check_line_endings or args.check_launchers:
        print("[1/7] Checking mandatory 2-language structure & launcher counts...")
        errs = check_mandatory_structure(root)
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print("  PASS: Mandatory bilingual structure and exactly 24 launchers present (6+6 zh, 6+6 en)")

    # Step 2: Line endings check
    if run_all or args.check_line_endings:
        print("[2/7] Checking line endings according to .gitattributes...")
        errs = check_line_endings(root)
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print("  PASS: All line endings conform (.bat strictly CRLF, .command/.sh/.py strictly LF)")

    # Step 3: Launchers contract check
    if run_all or args.check_launchers:
        print("[3/7] Checking launcher contracts, reachability, and tokenized arguments...")
        errs = check_launchers(root)
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print("  PASS: All 24 launchers satisfy shebang, argument closure, reachability, action mapping, and -I -B invocation")

    # Step 4: Shell syntax check
    if run_all or args.check_syntax:
        print("[4/7] Checking shell script syntax (bash -n)...")
        errs, note, is_inc = check_bash_syntax(root)
        if is_inc:
            print(f"  {note}")
            incomplete = True
        elif errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print(f"  PASS: {note}")

    # Step 5: Python 3.9 AST syntax compatibility
    if run_all or args.check_ast:
        print("[5/7] Checking Python 3.9 AST syntax compatibility...")
        errs = check_python_ast(root)
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print("  PASS: All Python files compatible with Python 3.9 AST")

    # Step 6: Cleanliness check
    if run_all or args.check_cleanliness:
        print("[6/7] Checking worktree cleanliness (zero cache / .pyc)...")
        errs = check_cleanliness(root)
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            print("  PASS: Clean worktree (zero .pyc or uncataloged runtime cache)")

    # Step 7: Disposable projects execution
    if run_all or args.check_disposable:
        print("[7/7] Checking bilingual selftests, dual sensors, & launchers in disposable git repositories...")
        errs, stats, records = check_disposable_projects(root)
        # Keep successful and failed raw execution evidence in the CI job log.
        # bytes arise on TimeoutExpired even with text=True.
        print(json.dumps({'execution_records': records, 'stats': stats}, ensure_ascii=False,
                         default=lambda value: value.decode('utf-8', 'replace')
                         if isinstance(value, bytes) else str(value)))
        if errs:
            for e in errs:
                print(f"  FAIL: {e}")
            total_errors.extend(errs)
        else:
            zh_pass = stats.get("zh_selftest_passed", 0)
            en_pass = stats.get("en_selftest_passed", 0)
            zh_sn = stats.get("zh_sensors_run", 0)
            en_sn = stats.get("en_sensors_run", 0)
            print(f"  PASS: Bilingual selftest (zh: {zh_pass} passed, en: {en_pass} passed), dual sensors (zh: {zh_sn} run, en: {en_sn} run), and launcher reachability/exit propagation checks passed")

    print("\n====================================================")
    if total_errors:
        print(f"FAILED: {len(total_errors)} hygiene violation(s) detected.")
        return 1
    elif incomplete:
        print("INCOMPLETE: Required verification dependencies missing (bash not in PATH). Exit code 2.")
        return 2
    else:
        print("ALL HYGIENE CHECKS PASSED (exit code 0)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
