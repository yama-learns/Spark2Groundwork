# Prompt 庫

**用法：`_COMMON_BLOCKS.md` 是零件盒，`TEMPLATE_*.txt` 是成品。**

⛔ **成品必須完全自足。** 組裝時把零件的**全文**貼進去，不得寫「見零件 A」。
**理由與實測後果見 `policy/EXTERNAL_TOOLS.md` 第 2 條。**

| 檔案 | 用途 |
|---|---|
| `_COMMON_BLOCKS.md` | 可重複使用的段落 |
| `TEMPLATE_decompose.txt` | **把構想拆成可證偽的猜想**（初始化第一步） |
| `TEMPLATE_prior_art.txt` | 先行技術檢索：這件事有沒有人做過 |
| `TEMPLATE_adversarial.txt` | 對抗審計：請攻擊我的產出 |

**收件流程：** 收到外部報告後依 `profiles/PROFILE_external_tools.md` §2 五級分流。

---

## ⚠️ 哪些範本會被感測器判 FAIL，以及為什麼

```
python scripts/harness/sensor_prompt_self_contained.py prompts/TEMPLATE_prior_art.txt
→ FAIL [PROMPT_NOT_ASSEMBLED] ×6
```

| 範本 | 判定 | 原因 |
|---|---|---|
| `TEMPLATE_decompose.txt` | ✅ **PASS** | 它是完整的成品，⛔ **不含任何區塊佔位符** |
| `TEMPLATE_adversarial.txt` | ✅ **PASS** | 同上 |
| `TEMPLATE_prior_art.txt` | ❌ **FAIL** | 它有 6 個 `<<<貼上區塊 X>>>`——**零件還沒貼進去** |

⛔ **這一節先前寫錯了，訂正如下。**

**舊版寫：「範本本身會被感測器判 FAIL，那是正確的」，理由是「範本裡寫的是
`<<<貼上區塊 B>>>`」。⚠️ 那個理由對 `TEMPLATE_prior_art.txt` 成立，
對另外兩份不成立——它們裡面根本沒有區塊佔位符。**

**它們當時之所以 FAIL，是因為感測器把 Deep Research 專用的 8 項條款表
套用到了每一份 prompt 上。而 `TEMPLATE_decompose.txt` 開頭逐字寫著
「⛔ 這一輪不要查文獻」——一份禁止查文獻的 prompt，
不可能也不應該包含雙語檢索條款。它組裝完成之後仍然會 FAIL，永遠。**

> 🔴 **而這一節當時替那個誤報寫好了解釋。**
> **一支對正確文本報警的感測器，加上一份說「這個 FAIL 是正確的」的官方說明——**
> **第二層比第一層危險，因為它把「忽略這支感測器」寫成了制度。**

**現況：**

- **自足性檢查**（跨檔指涉／未組裝的區塊／prompt 汙染）→ **對所有 prompt 執行**
- **DR 專用條款表**（8 項）→ **只在 `--profile deep-research` 下執行**

```
python scripts/harness/sensor_prompt_self_contained.py <組裝好的 DR prompt> --profile deep-research
```

⚠️ **三種 `<<<…>>>` 佔位符只有一種是缺陷：**

| 形態 | 例 | 判定 |
|---|---|---|
| 區塊佔位符 | `<<<貼上區塊 B（列舉，不要摘要）>>>` | ❌ FAIL |
| **內容槽** | `<<<貼上你的構想全文>>>` | ✅ **不是缺陷**，那是你在使用時才填的 |
| 填空槽 | `<<<填空:一句話>>>` | ⚠️ WARN |

→ **正確用法：先把零件的全文貼進去組裝成品，再跑感測器。**
→ **組裝完仍判 FAIL，才是真的有問題。**
