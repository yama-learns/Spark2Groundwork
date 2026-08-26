# 學術研究神器 · AI 論文發想框架 · Spark2Groundwork

### The Researcher's Power Tool · An AI Framework for Paper Ideation

**把一個發想，變成一份站得住的研究提案。**
**Turn a spark of an idea into a research proposal that holds up.**

[English edition](Spark2Groundwork_en/README.md) ｜ [繁體中文版](Spark2Groundwork_zh/README.md)
｜ [What changed in each release](CHANGELOG.md)

> 這份說明以英文撰寫。**中文使用者請點上面的「繁體中文版」**，那裡有完整的中文說明。

---

## What this is

A set of files you copy into your project folder. They give your AI assistant a way of
working, and they give you a way of checking what it did.

It starts from one assumption: **the AI will be wrong, and it will be wrong in the places
where it sounds most certain.** Every check in here exists because that actually happened
to someone.

| The questions it helps you answer |
|---|
| Which page does this sentence rest on? |
| What would it take to prove this idea wrong? |
| What did the AI just change, and have I looked at it? |

⛔ **It does not promise your research is correct.** It promises something narrower and more
useful: **when something goes wrong, it leaves a trace instead of quietly becoming your
conclusion.**

---

## How it works

<p align="center">
  <img src="Spark2Groundwork_en/docs/fig2_workflow.svg" alt="Workflow: the evidence chain, who watches it, and the loop" width="100%">
</p>

**Four ideas hold the whole thing together.**

**1. Getting from a source to a sentence takes several steps, and they break differently.**
One of those steps — *is this passage actually in the paper?* — can be settled by comparing
text, at no cost. That one is automated, and the rest of the design leans on it.
Two other steps — *does the passage really support the claim?* and *can you generalise from
that study to yours?* — ⛔ **are deliberately left to you.** A check that fires on correct work
teaches you to ignore it, which is worse than having no check at all.

**2. Two records, two different jobs.** One tracks your ideas and what would prove each of
them wrong. The other tracks your sentences and the exact passage each one rests on.

**3. Mistakes come in families.** Writing down one mistake does not help, because the next one
looks different. What you write down is the *pattern* — so you recognise it next time.

**4. You are the one who decides.** This is not caution; it is what happened. Across two
earlier projects, the user caught more genuinely new errors than any other part of the system,
and the most effective thing they did was **bring in information the AI did not have.**

---

## There is no perfect framework — only one that gets better as you use it

🔴 **This is the idea the whole thing is built on.**

**No framework arrives already suited to your topic, your AI and your working habits.**
⛔ **We are not going to pretend otherwise.**

**It is built on a different premise: every hole you fall into becomes a railing for next time.**

| What you do | What the framework grows |
|---|---|
| Catch the AI getting something wrong and say "log that" | One more entry in your project's incident log |
| After a few entries, ask the AI to find the repeating patterns | You see a shape that **will happen again** |
| You decide whether it becomes a rule | One more working rule — **specific to your project** |

⚠️ **The middle step is not optional.** One mistake on its own does not help, because the next
one will not look the same; **what is worth having is the shape that repeats.**

⛔ **The last step is always your decision, never the AI's** — because that rule will bind both
of you afterwards.

**After a while your copy will not look like anyone else's.**
🔴 **That is not drift. That is the point.**

⚠️ **It is also why upgrading is safe, for a reason that is easy to read backwards:**
**the upgrade tool recognises nine names of its own — five framework folders and four
framework files — and ⛔ refuses everything else.**
**Your ledgers, your papers, your incident log, `PROJECT.md`, and any folder you created
yourself are all left alone. You never have to register them anywhere.**

---

## Getting started

**You do not need to know Git, and there is nothing to install for this step.**

1. Click the green **Code** button at the top of this page, then **Download ZIP**.
2. Unzip the file you downloaded.
3. Inside it you will find two folders. **Take the one in your language:**
   - `Spark2Groundwork_en` — English
   - `Spark2Groundwork_zh` — 繁體中文
4. **Copy that folder to wherever you keep your work, and rename it to your project name.**
   For example `bilingual-memory-study`.
5. ⛔ **Delete the rest of the download.** You only need the one folder.
6. Open `SETUP.md` inside your new folder and follow it.

**What you will need later:** Python (free, from [python.org](https://www.python.org/downloads/)),
Git (free, from [git-scm.com](https://git-scm.com/downloads)), and whichever AI you already use.
`SETUP.md` walks you through installing them.

---

## Pointing your AI at the folder

The framework is just files, so **any AI that can read your folder can use it.** Three common
setups, with the steps as of this writing:

### Claude — use Cowork

1. Open the Claude desktop app.
2. In the left panel, find **Projects** and click **+**.
3. Choose **Use an existing folder on your computer**.
4. Pick your project folder, give the project a name, and click **Create**.

Claude can then read and write the files directly, and can run the checks for you.

### Gemini — use Antigravity

1. Open Antigravity.
2. Click **Select Project → New Project**.
3. Use **Add Folder** to add your project folder, then create the project.
4. Chat with the agent in the main panel. **Open IDE** gives you a full editor if you want one.

A project can hold more than one folder, so you can add related material alongside it.

### ChatGPT — use Work mode in the desktop app

1. Open the ChatGPT desktop app and switch to the **Work** tab at the top.
2. Click **Select project** below the input box, then **New project**.
3. In the dialog that opens, type a **project name**.
4. Under **Source folder**, click the box offering to add a folder ChatGPT can read and edit.
   A file picker opens, titled **Select Project Root** — choose your project folder.
5. Click **Create project**.

Work can then read and write files in that folder, and the link stays put between sessions —
⛔ **you do not re-upload anything.**

⚠️ **Local file access depends on your plan and, in an organisation, on your workspace
settings.** If the option to link a folder is not offered, that is why.

⚠️ **Web ChatGPT is a different thing.** There, a project holds uploaded copies rather than a
live folder, with a file limit (5 on Free, 25 on Go/Plus, 40 on the higher plans).
It still works, with more copying and pasting —
**`profiles/PROFILE_chat_only.md` in your folder is written for exactly that case.**

### Already using a coding agent?

**Claude Code and ChatGPT's Codex both work with this framework too**, and they are the most
direct fit — they live in a folder, read files and run commands natively.

⚠️ **We have not tested either of them with this framework, so we are not giving you steps.**
Point them at the folder the way you normally would, and start from `SETUP.md`.

⛔ **One thing to know before you do:** a coding agent will happily edit files and run commands
without pausing. **The protection in this framework comes from the checkpoint habit** — press
snapshot before you hand out work, and again after you have reviewed it.
**Nothing enforces that for you.**

⚠️ **Menus change.** If what you see does not match the steps above, look for the wording that
means the same thing — "add a folder", "link a folder", "project instructions".

---

## What is in the box

<p align="center">
  <img src="Spark2Groundwork_en/docs/fig1_architecture.svg" alt="Architecture: what belongs to the framework and what belongs to you" width="100%">
</p>

```
Spark2Groundwork_en/     the whole framework, in English
Spark2Groundwork_zh/     完整框架，繁體中文
```

**The two are independent and say the same things.** Take one; you do not need both.

Inside either one:

| | |
|---|---|
| `SETUP.md` | The setup guide. Start here |
| `INITIALIZE_PROMPT.md` | The text you paste to your AI the first time |
| `PROJECT.md` | 🔴 **The only file you have to write yourself** |
| `corpus/` | **Your source PDFs go here**, along with your bibliography |
| `corpus_md/` | The plain text pulled out of those PDFs, for checking quotations |
| `ledgers/` | Where your ideas and your quoted evidence are recorded |
| `governance/` | The rules the AI works under |
| `policy/` | Rules for particular topics: sources, handovers, model identity, outside tools |
| `profiles/` | Pick the one that matches how you work |
| `prompts/` | Ready-made instructions you can paste |
| `scripts/harness/` | The automatic checks |
| Three buttons | snapshot / review changes / check update (`.bat` for Windows, `.command` for Mac) |

---

## Versions

Each release is tagged in Git, and **the folder names carry no version number** — if they did,
every path and bookmark would break on each release.

See [CHANGELOG.md](CHANGELOG.md) for what changed, and
[Releases](https://github.com/yama-learns/Spark2Groundwork/releases) for the downloads.

To find out whether you are up to date, press the **check update** button in your project folder.

---

## Where this came from

**Two real research projects, and forty-odd recorded mistakes between them.**
Every check and every rule here carries the case that caused it.

⚠️ Some of the mistake patterns listed in `governance/Incident_Log.md` are marked
`[inherited]`, `[framework's own]` or `[predicted]`. **Those have not happened in your
project.** They are listed so you know what to watch for — ⛔ not so you can assume you are
already safe from them.

---

## Licence

MIT — see [LICENSE](LICENSE). The framework files are covered; **the research you produce with
them is yours.**
