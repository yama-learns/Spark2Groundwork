# Setup guide

**This guide assumes you have no programming background.**
It takes about 40 minutes, and 30 of those are you answering questions about your own research.

> ⚠️ **Please do the steps in order.**
> Everything before step 5 exists so that the checks in step 5 will actually run.

---

## Step 0: check this is the right tool for you

**It suits you if —**

- You have **a research idea that has not taken shape yet** and want to turn it into a proposal
- You will use AI to help, but **you are the one answering for the result**
- You are willing to spend roughly 20% more time in exchange for mistakes leaving a trace

**It does not suit you if —**

- You want output quickly. **This framework will slow you down, and that is deliberate**
- Your work contains no factual claims that need checking
- ⛔ **You want the AI to run ahead on its own while you look only at the final result.**
  The framework assumes the opposite

---

## Step 1: get the framework folder (about 5 minutes)

**You do not need Git for this, and there are no commands to type.**

1. Go to <https://github.com/yama-learns/Spark2Groundwork>
2. Click the green **Code** button → **Download ZIP**
3. Unzip the file you downloaded
4. Inside are two folders. **Take the English one:** `Spark2Groundwork_en`
5. **Copy it to wherever you keep your work, and rename it to your project name** —
   for example `bilingual-memory-study`
6. ⛔ **You can delete the rest of the download.** You only need that one folder

⚠️ **From here on, "your project folder" means the folder you just renamed.**

---

## Step 2: double-click to check your tools

Double-click **check_project.bat (Windows) / check_project.command (Mac)** in the project root. No terminal commands or manual PATH edits are needed.

If Python is missing, the local [startup guide](docs/START_HERE.html) opens. For missing Git or other problems, open the same guide as directed. Complete the official graphical installation and rerun the check. Python 3.9 is the minimum; choose a version currently provided for your system. An install manager without a runtime is not ready.

For a blocked first Mac launch, retain the message and follow the specific-file instructions; do not clear security markers for the entire folder. You can write research notes while tools are unavailable. Results from an AI VM or remote host do not prove your computer passed.

---

## Step 3: point your AI at the folder (about 5 minutes)

**The framework is just files, so any AI that can read your folder can use it.**
Here are three common setups, with the steps as of this writing.

### 3.1 Claude — use Cowork

1. Open the Claude desktop app
2. In the left panel, find **Projects** and click **+**
3. Choose **Use an existing folder on your computer**
4. Pick your project folder, give the project a name, and click **Create**

Claude can then read and write the files directly, and can run the checks for you.

### 3.2 Gemini — use Antigravity

1. Open Antigravity
2. Click **Select Project → New Project**
3. Use **Add Folder** to add your project folder, then create the project
4. Talk to the agent in the main panel. **Open IDE** gives you a full editor if you want one

A project can hold more than one folder, so you can add related material alongside it.

### 3.3 ChatGPT — use Work mode in the desktop app

1. Open the ChatGPT desktop app and switch to the **Work** tab at the top
2. Click **Select project** below the input box, then **New project**
3. In the dialog that opens, type a **project name**
4. Under **Source folder**, click the box offering to add a folder ChatGPT can read and edit.
   A file picker opens, titled **Select Project Root** — choose your project folder
5. Click **Create project**

Work can then read and write files in that folder directly, and the link persists between
sessions — ⛔ **you do not re-upload anything.**

⚠️ **Whether you can link a local folder depends on your plan, and inside an organisation on
your workspace settings.** If the option is not offered, that is usually why.

⚠️ **Web ChatGPT is a different thing.** There, a project holds uploaded copies rather than a
live folder, with a file limit (5 on Free, 25 on Go/Plus, 40 on the higher plans).
It still works, with more copying and pasting —
**`profiles/PROFILE_chat_only.md` in your folder is written for exactly that case.**

### 3.4 Already using a coding agent?

**Claude Code and ChatGPT's Codex work with this framework too**, and they are the most direct
fit — **they live in a folder, and reading files and running commands is native to them.**

⚠️ **We have not tested either of them with this framework, so we are not giving you steps.**
Point them at the folder the way you normally would, and start from this guide.

⛔ **One thing to know first:** a coding agent will happily edit files and run commands without
pausing to ask.
🔴 **The protection in this framework comes from the snapshot habit** — press it before you
hand out work, and again once you have reviewed it.
**⛔ Nothing enforces that for you.**

⚠️ **Menus change.** If what you see does not match the steps above, look for the wording
that means the same thing: "add a folder", "link a folder", "project instructions".

---

## Step 4: fill in and add your material (about 20 minutes, ⛔ **not a step to hand to the AI**)

### 4.1 Fill in `PROJECT.md`

🔴 **This is one of the two project files you fill in yourself.**
The other is `FIRST_IDEA.md` beside it. Every other governance document is looked after by
the AI — **you do not need to open those files.**

⚠️ **The three questions in §1.1 must be answered by you. ⛔ Do not have the AI answer them:**

> **① If this question were answered, which existing claim would no longer stand?**
> (Not "advances understanding" or "fills a gap". **Name a specific casualty.**)
>
> **② Has nobody answered this, or has somebody answered it and I do not know about it?**
> (This is a question of fact you can settle by searching the literature — **not an adjective.**)
>
> **③ Why is it me who should be doing this one?**

**Why the AI must not answer them:**
These three exist to stop **your research agenda quietly being taken over by the AI.**
If you cannot answer the third, what you are working on may be the question the AI finds easy,
rather than the question you wanted to ask.

### 4.2 Fill in `FIRST_IDEA.md`

**Open `FIRST_IDEA.md` at the project root, beside `PROJECT.md`, and replace the placeholder
at the bottom with your complete idea.** Keep the decomposition rules above it; the AI reads
the whole file in the first round.

🔴 **This is a project-owned file.** It deliberately does not live in `prompts/`: that is a
framework folder replaced wholesale on upgrade, while your idea must never be overwritten.

### 4.3 Put your papers in `corpus/`

**Put every PDF you intend to cite into the `corpus/` folder.**
One file per paper; a filename like "FirstAuthor_Year_keyword.pdf" works well.

**Why they have to be there:** the framework checks whether the sentence you quoted is really
in the source. If the source is not in the project, that check cannot run —
⛔ **and "could not check" is not the same as "no problem".**

### 4.4 Build your bibliography

`corpus/` contains a file called **`BIBLIOGRAPHY.docx`**. It is blank right now.

**Do this:**

1. Manage your references in **Zotero** or **EndNote** (both have free versions)
2. Export the whole bibliography in the style you need (APA, Chicago, and so on)
3. **Paste what you exported into `BIBLIOGRAPHY.docx`**
4. Come back and update it whenever you add a reference

🔴 **From then on, every citation in this project follows that file, ⛔ not what the AI says.**

⚠️ **Why this extra step is worth it:**
An AI will get DOIs, page numbers and years wrong, **and a wrong one reads exactly like a
right one.** One measured example: a model produced eight references —
**every one of them a genuine, well-known paper in the field, but at least three had a wrong
identifier.**

> **"Are these good papers?" is a question it can answer. "Is this DOI correct?" is not —**
> **and both answers read with exactly the same confidence.**

⛔ **Do not ask the AI to "fill in the DOIs for you".** It will, and they will look right.
✅ **What you can ask it to do:** compare its own citations against your bibliography and
**list the ones that do not match.**

⚠️ If you later connect your AI directly to Zotero, that is fine —
**but keep this file anyway, as an offline copy to compare against.**

### 4.5 Establish your first human-reviewed baseline

**Read your initial contents first. This confirms human review, not just saving; AI must not press it for you. Use save_progress to save without review.**

**Windows:** double-click `snapshot.bat`
**Mac:** double-click `snapshot.command`

If you see "checkpoint created", it worked.

⚠️ **If nothing happens the first time on a Mac**, open the local guide and retain the actual message:

[Startup help](docs/START_HERE.html)

Do not remove security markers for the whole folder. An unsuccessful launch remains incomplete.

---

## Step 5: pick a profile and run the checks for the first time (about 7 minutes)

### 5.1 Pick a profile

**Open the `profiles/` folder and choose one:**

| Your situation | Choose |
|---|---|
| Just you and one AI | `PROFILE_solo.md` |
| Several AIs with separate jobs (research / governance / audit) | `PROFILE_multi_agent.md` |
| No file access, only a chat window | `PROFILE_chat_only.md` |
| You use outside tools such as Deep Research or n8n | Any of the above, plus `PROFILE_external_tools.md` |

**Each profile tells you which documents to keep, which to delete, and which checks to run.**

⛔ **Do not keep all of them.**
A governance document nobody maintains is worse than not having it —
**it makes you think somebody is watching.**

⚠️ **If you chose the multi-agent profile:** make a folder called `scratch` at the top level
of your project, **as the audit role's sandbox.** ⛔ It does not come with the framework —
**`scratch/` is by definition the place that is not under version control.**

### 5.2 Double-click the project check

Double-click **check_project.bat / check_project.command** again. This checks local tools and calls the existing project sensors. It does not run developer self-tests or create a checkpoint.

### 5.3 Keep the results and follow the next step

Empty fields in a new project may produce warnings. For failures or incomplete checks, keep the full output for your AI; do not edit checks to make warnings disappear. If diagnostic self-tests are needed, a maintainer with local execution access can run them; ordinary users need not paste commands.

### 5.4 What the three results mean

| Code | Meaning | What to do |
|---|---|---|
| **0** | Passed | Carry on |
| **1** | Defect found | **Something is definitely wrong.** Fix it before continuing |
| **2** | **Could not check** | ⛔ **This is not a pass** |

⚠️ **The third one matters most.**
"Could not check" means the program never managed to finish the check.
**Treating it as a pass is exactly the kind of mistake this framework exists to stop.**

---

## Step 6: hand your idea to the AI (about 5 minutes)

**First make sure `FIRST_IDEA.md` is filled in. Then paste all of `INITIALIZE_PROMPT.md` to an
AI that can read this project folder.** It reads `FIRST_IDEA.md` directly; you do not need to
copy the idea into the message again.

That prompt asks the AI to:

1. Read the governance documents first, and **say back which places it is allowed to write to**
2. Break your idea into **numbered conjectures**, each with a note on what would prove it wrong
3. ⛔ **Not start searching the literature yet** — **let you confirm the breakdown first**

⚠️ **Point 3 is deliberate.**
If the breakdown is wrong at the start, every paper found afterwards is only evidence for
the wrong thing.

---

## Step 7: how each round goes from here

```
      ┌──────────────────────────────────────────────┐
      │  ① Press "save progress"   save without review  │
      │  ② Press "check project"   check for red      │
      │  ③ Give the AI its task                       │
      │  ④ The AI finishes and hands over a summary   │
      │  ⑤ Press "review changes"  see what it did    │
      │  ⑥ You decide → update the ledgers            │
      │  ⑦ Press "snapshot" again  = "I have read it" │
      └──────────────────────────────────────────────┘
```

**These buttons sit at the top level of your project folder**
(`.bat` on Windows, `.command` on Mac):

| Button | When to press it |
|---|---|
| **check project** | At startup and before handing out work |
| **snapshot** | Only after actual human review |
| **save progress** | Save without advancing the human baseline |
| **sync rules** | After updating governance, append missing rules and check drift |
| **review changes** | After the AI finishes |
| **check update** | Now and then, to see whether the framework has a new version (step 9) |

⚠️ **Step ⑦ is not a formality.**
It moves a marker called "reviewed" forward, and **the next "what changed" is counted from
there.** If you skip it, you will see the same changes again next time.

---

## Step 8: a few things that will happen, said up front

### 8.1 The checks will produce false alarms

**They will. And the first time one does, you will want to switch it off.**

⛔ **Do not loosen the standard.**
The correct response is to fix the comparison logic and **add a test case saying "this
situation must not raise an alarm".** `my/MY_RULES.md` explains this in full (the framework's rules are copied into its §1).

### 8.2 The AI will be wrong where it is most confident

**Across two earlier projects, forty-odd recorded mistakes — almost all of them in the
passages where the writer sounded most certain.**

→ Which is why `governance/Audit_Protocol.md` asks you to
**spot-check the claims you are most sure about, not the ones you are least sure about.**

### 8.3 You will want to skip the ledger

**Recording a claim with its exact quotation and page takes about five times as long as just
writing the sentence.**

⚠️ **And that is the point:**
filling in the page number forces you to actually turn to that page —
**and when you do, you often find it does not say what you thought it said.**

---

## Step 9: updating, saving and confirming review

Read the [complete instructions](docs/UPDATE.md). Back up outside the project, compare and replace one package at a time; no pasted commands are required. Use sync_rules for missing rules; you still decide existing-text drift.

---

## Appendix: common questions

**Q: Can I use only part of it?**
Yes — that is what `profiles/` is for.
**Keep at least the Claim Ledger and the Git checkpoints**; those two cost the least and
return the most.

**Q: Can the AI update the ledgers itself?**
⛔ **Not recommended.** A ledger records **what you have confirmed**.
If the AI writes straight into it, nobody is confirming anything.
The right pattern is: the AI reports in a "please decide" format → you decide → then it is
written in.

**Q: I do not know how to use Git. Do I have to learn?**
**These buttons exist so that you do not.**
You only need to remember two things: **press one before giving out work, press one after
reviewing it.**

**Q: Is this whole thing too heavy?**
If you use all of it, yes. **That is exactly why `profiles/` exists.**
⚠️ Also worth knowing: **the framework has its own rule guarding against governance documents
multiplying** — it assumes they will grow, ⛔ rather than assuming you will hold back.

**Q: Do my PDFs get uploaded anywhere?**
⛔ **No.** Every file stays on your own computer.
**The only exception is whatever you paste to the AI yourself** — for that, check the data
policy of whichever AI you are using.
