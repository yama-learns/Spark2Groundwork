# Model Identity Protocol

**Tier: T1 — spec class.**

---

## 1. Why this file exists

**"Which model produced this" is a fact, not an impression.**
Without it, records of model performance degrade into recollection,
and a failure attributed to the wrong model teaches the wrong lesson.

## 2. The rule

**The first act of every working session: write `[Model: <verbatim value>]` in the first output.**

⛔ **Three prohibitions:**

1. Inferring from conversation context, the user's verbal statement, or a value named in a handoff packet
2. Self-diagnosing from your own answering style
3. Guessing when you cannot read it

## 3. Where the authoritative value lives

**This varies by platform. Fill in the row for your platform:**

| Platform | Authoritative source | Nature |
|---|---|---|
| **<<<FILL IN: e.g. an agentic IDE>>>** | **<<<FILL IN: e.g. the `Model:` field of the environment block>>>** | State snapshot / one-off event |
| **<<<FILL IN>>>** | **<<<FILL IN>>>** | |

⚠️ **State snapshots and one-off events fail differently.**
A snapshot attached to every request survives truncation;
a one-off marker is **permanently lost** once a long conversation is truncated.
**A platform of the second kind needs an explicit fallback — see §4.**

## 4. When the field is not where the protocol says it is

⚠️ **Measured case:** in one run the designated block **had no model field**,
but the identifier was written verbatim one line below it.

**Strictly applied, the correct output would be "cannot read" — but that would be a wrong downgrade:
the authoritative information existed, just not where the protocol said.**

**Three-step fallback, in order:**

| Step | Case | Handling |
|---|---|---|
| 1 | The designated location has a value | **Take it verbatim** |
| 2 | It does not, but **the same system message contains a verbatim model identifier** | Take it, **and state explicitly: "authoritative field absent; read verbatim from &lt;actual location&gt;"** |
| 3 | Neither | **Output "cannot read"**. ⛔ Never substitute a platform name |

⛔ **In case 2 that sentence must not be omitted.**
**"I read it" and "I read it from somewhere the protocol does not mention" are different things,
and the reader cannot tell them apart from the output alone.**

## 5. What this protocol does not claim

- ⛔ It **does not verify** that the declared model is the model that actually ran
- ⛔ It **cannot detect** a model that deliberately misreports
- It only makes **"was this read from the authoritative source or inferred"** an answerable question
