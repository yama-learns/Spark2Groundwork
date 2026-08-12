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

## ⚠️ 範本本身會被感測器判 FAIL，那是正確的

```
python scripts/harness/sensor_prompt_self_contained.py prompts/TEMPLATE_prior_art.txt
→ FAIL [REQUIRED_CLAUSE_MISSING]
```

**因為範本裡寫的是 `<<<貼上區塊 B>>>`，而不是區塊 B 的全文。**

**這正是該感測器存在的理由：** 在執行端，`<<<貼上區塊 B>>>` 與「同上」等價——
**被指涉的條款實質上不存在。**

→ **正確用法：先把零件的全文貼進去組裝成品，再跑感測器。**
→ **組裝完仍判 FAIL，才是真的有問題。**
