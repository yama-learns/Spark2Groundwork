# Prompt Parts Bin

⛔ **When assembling, paste the full text. Do not write "see block A".**

---

## Block A — Hallucination guard

```
You are producing LEADS, not ground truth. Every claim will be independently
verified against the original source before use. Precision about what you are
unsure of is more valuable than fluent completeness.

Wherever you are uncertain, output [UNCERTAIN: <what specifically>] rather than
a confident-sounding guess. Do NOT invent effect sizes, sample sizes, reliability
coefficients, journal names, or identifiers.

The specific failure to avoid: describing a real study's CONTENT correctly while
attributing it to the wrong author, journal, or title. The correct-sounding
content description causes readers to trust the incorrect bibliographic record.

Do NOT strip hedging from what a source actually said.
```

## Block B — Enumerate, do not summarise

```
ENUMERATE the closest existing work. ONE PER LINE. For each:
author | year | venue | full title | what exactly they did |
what they did NOT do that the target question requires.

Do NOT write general statements such as "there is a large literature on X".
Either name the studies, or write exactly `NONE RETRIEVED` and nothing else.
A general claim about a literature is not a finding.

`NOT-COVERED` is a verdict about whether anyone has ANSWERED the question.
It is NOT a statement that you found no relevant literature. EVEN WHEN THE
VERDICT IS NOT-COVERED, you must still enumerate the closest existing work.
```

## Block C — Competing accounts

```
For each alternative account, give:
  - name of the account, and its canonical reference
  - what it explains that the target claim also explains
  - the observable result on which the two accounts DISAGREE

The third bullet is the important one. An alternative account that makes the
same predictions is not a competitor - it is a re-description.

If you find no genuine competing account, write exactly
`NO COMPETING ACCOUNT RETRIEVED` - and then state what you searched for.
```

## Block D — Source standards (graded, not exclusionary)

```
Include peer-reviewed articles, conference papers, and book chapters in ANY
language. Tag every entry:
  [LANG: ...]  [VENUE-TYPE: ...]  [EVIDENCE: empirical|methodological|review|conceptual]

A missing identifier is NOT a reason to exclude a source. Give the fullest
available identifier and mark [NO-DOI: <reason>].

NEVER invent bibliographic fields to satisfy a citation format.
Inventing a journal name, volume, or page range is a fabrication, not a
formatting choice.
```

## Block E — Bilingual search (**adapt the keywords to your field; do not delete this block**)

```
You MUST run BOTH search passes and report what each yielded.
PASS A (English): <keywords>
PASS B (<your language>): <keywords>
<list that language's professional databases>

If a non-English search returns nothing for a sub-question, SAY SO EXPLICITLY
for that sub-question. Do not silently substitute an English-language study.
```

⚠️ **Block E is not diversity for politeness.** Searching in English only silently excludes
an entire language region's literature — **and that exclusion appears in no report** (the "silent filtering" family).

## Block F — Measurement and reliability

```
For every measure you report:
  - state the REPORTED reliability of the individual-level score, with the source
  - if the source does not report it, write [RELIABILITY NOT REPORTED]
  - state sample size, number of trials, number of sessions
  - state whether the score is a difference score, a fitted parameter, or a
    directly-observed quantity

Do NOT estimate, infer, or carry over a value from a different study.
[RELIABILITY NOT REPORTED] is a useful finding; a plausible-looking invented
number is not.
```
