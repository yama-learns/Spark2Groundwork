# External Tools Policy

**Tier: T1 — spec class.**
**Full operating guidance in `profiles/PROFILE_external_tools.md`; this file fixes only the non-negotiables.**

---

1. ⛔ **External tool output ＝ unverified lead. No assertion from it may be cited without checking the original.**
2. ⛔ **External prompts must be fully self-contained**; no cross-prompt references.
3. ⛔ **External output must not enter the corpus** — the corpus is programmatically extracted
   source text, and mixing in AI text turns anchor checking into matching against
   sentences the AI wrote itself.
4. ⛔ **Automated pipelines must not write to ledgers.**
5. **When two models run the same prompt, their disagreements are the highest-value output** —
   a disagreement marks a place where at least one side is wrong.
