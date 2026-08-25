# 學術研究神器 · AI 論文發想框架 · Spark2Groundwork

### The Researcher's Power Tool · An AI Framework for Paper Ideation

**Turn a spark of an idea into a research proposal that holds up.**
**把一個發想，變成一份站得住的研究提案。**

[English](Spark2Groundwork_en/README.md) ｜ [繁體中文](Spark2Groundwork_zh/README.md)
｜ [CHANGELOG](CHANGELOG.md)

---

## What this is / 這是什麼

A **file-based governance framework** for developing research ideas with AI assistance.
It assumes the AI will be wrong — and that **it will be wrong where it is most confident**.
Every defence here corresponds to a failure that actually happened.

一套**檔案化的工作流治理框架**，用於在 AI 協作下發展研究構想。
它假設 AI 會出錯，而且**會在最有把握的地方出錯**。
其中每一道防線，都對應一次真實發生過的失效。

| It answers | 它回答 |
|---|---|
| Which page does this sentence rest on? | 這句話的根據在哪一頁？ |
| What would it take to refute this idea? | 這個想法要怎樣才算被推翻？ |
| What did the AI just change, and have I reviewed it? | AI 剛才改了什麼？我看過了沒有？ |

⛔ **It does not guarantee your research is correct.** It guarantees only that
**when it is wrong, the error leaves a trace instead of quietly becoming your conclusion.**

⛔ **它不保證你的研究是對的。** 它只保證：
**當它出錯時，錯誤留下痕跡，而不是靜靜地變成你的結論。**

---

## Quick start / 快速開始

```bash
git clone https://github.com/yama-learns/Spark2Groundwork.git
cd Spark2Groundwork
```

**Then copy the edition you want and rename it to your project:**
**然後複製你要的版本，改名為你的專案：**

```bash
cp -r Spark2Groundwork_en  ~/my-research-project     # English
cp -r Spark2Groundwork_zh  ~/我的研究專案             # 繁體中文
```

👉 **Open `SETUP.md` inside it. 打開裡面的 `SETUP.md`。**

**Requirements:** Git, Python 3.9+, and any AI you already use.
**需要：** Git、Python 3.9+，以及任何你已經在用的 AI。

---

## What's inside / 內容

<p align="center">
  <img src="Spark2Groundwork_en/docs/fig1_architecture.svg" alt="Architecture: what is the framework and what is yours" width="100%">
</p>

```
Spark2Groundwork_en/     Full framework, English
Spark2Groundwork_zh/     完整框架，繁體中文
```

Each edition contains 每個版本各自包含：

| | |
|---|---|
| `SETUP.md` | Setup guide ／ 初始化指導說明書 |
| `INITIALIZE_PROMPT.md` | The prompt you paste to your AI ／ 貼給 AI 的初始化指令 |
| `governance/` | T0 documents, working rules, incident log, audit protocol |
| `ledgers/` | Conjecture Ledger, Claim Ledger |
| `policy/` | Model identity, handoff, sources, external tools |
| `profiles/` | solo ／ multi-agent ／ chat-only ／ external-tools |
| `prompts/` | Parts bin ＋ three templates |
| `PROJECT.md` | 🔴 **The only file you fill in ／ 你唯一需要親筆填的檔案** |
| `scripts/harness/` | Sensors ＋ paired self-tests ／ 感測器與成對自測 |
| Three buttons ／ 三個按鈕 | snapshot ／ review changes ／ check update （`.bat` ＋ `.command`） |

⚠️ **The count is deliberately not written here.** A number in prose drifts the moment a
sensor is added, and a stale number reads exactly like a current one (`R-16`).
To see it: `python3 scripts/harness/run_all_sensors.py` and `run_selftest.py`.

⚠️ **支數刻意不寫在這裡。** 散文裡的數字在下一次增修時就會過期，
而過期的數字與正確的數字長得一模一樣（`R-16`）。查證方式：跑一次上面兩支程式。

**The two editions are independent and equivalent.** Pick one; you do not need both.
**兩個版本各自獨立且對等。** 選一個即可，不需要兩個都要。

---

## How it works / 它怎麼運作

<p align="center">
  <img src="Spark2Groundwork_en/docs/fig2_workflow.svg" alt="Workflow: the evidence chain, who watches it, and the loop" width="100%">
</p>

### The four ideas / 四個核心概念

1. **The evidence chain has links.** ② "is that passage actually in the source" is
   answerable by string comparison at zero cost, and it is the fulcrum of the whole design.
   ⑥⑦ "does it support the claim" and "can you generalise" are **deliberately not mechanised**.

2. **Two ledgers, two jobs.** The Conjecture Ledger governs whether an idea holds up;
   the Claim Ledger governs which passage backs a sentence.

3. **Failures come in families.** Logging one incident is useless — the next will look different.
   You record the mechanism.

4. **The human is the only adjudicator.** Measured across two projects: the user had the
   highest novel-error interception rate of any layer, and their most effective method was
   **supplying external data the AI did not have**.

---

## Versioning / 版本

**Releases are tagged in Git. The directory names carry no version number** —
a version in a folder name breaks every path, bookmark, and clone command on each release.

**版本以 Git tag 標記，資料夾名不帶版本號**——
資料夾名一改，所有路徑引用、書籤與 clone 指令都要跟著改。

See [CHANGELOG.md](CHANGELOG.md) and
[Releases](https://github.com/yama-learns/Spark2Groundwork/releases).

---

## Provenance / 來源

Distilled from **two research projects in actual use**, with forty-odd logged incidents between them.

⚠️ **The `[inherited]`, `[framework's own]` and `[predicted]` failure families in
`governance/Incident_Log.md` have not happened in your project.** They are listed for honesty, not because they are in force —
**you may defend against them, but do not claim immunity because of them.**

⚠️ **`governance/Incident_Log.md` 中標為 `[繼承]`、`[框架自身]`、`[預測]` 的失效家族，在你的專案裡尚未發生。**
**它們列在那裡是為了誠實，不是為了生效。**

---

## Licence

MIT — see [LICENSE](LICENSE).
