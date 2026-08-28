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

## Step 2: install two programs (about 10 minutes)

| What | Why | Where |
|---|---|---|
| **Python 3.9 or later** | Runs the automatic checks | <https://www.python.org/downloads/> ⚠️ **Tick "Add Python to PATH" during install** |
| **Git** | Records what the AI changed, so you can look at it line by line | <https://git-scm.com/downloads> (on Mac, `brew install git` also works) |

### 2.1 Check they installed

Open a terminal (**Windows**: search the Start menu for `cmd`; **Mac**: search for "Terminal"),
type these two lines, pressing Enter after each:

```
git --version
python3 --version
```

**Both should print a version number**, for example `git version 2.45.0`.

⚠️ **On Windows, if `python3` does nothing, type `python` instead.**
⚠️ **On Mac, if `python3` does nothing**, run `xcode-select --install` once first.

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

🔴 **This is the only file you have to write yourself.**
Everything else is looked after by the AI — **you do not need to open those files.**

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

### 4.2 Put your papers in `corpus/`

**Put every PDF you intend to cite into the `corpus/` folder.**
One file per paper; a filename like "FirstAuthor_Year_keyword.pdf" works well.

**Why they have to be there:** the framework checks whether the sentence you quoted is really
in the source. If the source is not in the project, that check cannot run —
⛔ **and "could not check" is not the same as "no problem".**

### 4.3 Build your bibliography

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

### 4.4 Make your first checkpoint

**Windows:** double-click `snapshot.bat`
**Mac:** double-click `snapshot.command`

If you see "checkpoint created", it worked.

⚠️ **If nothing happens the first time on a Mac**, run this once in a terminal:

```
chmod +x *.command
xattr -dr com.apple.quarantine .
```

(The second line is because macOS marks files downloaded from the internet. Once is enough.)

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

### 5.2 Run the self-test first

```
python3 scripts/harness/run_selftest.py
```

**You should see "all self-tests passed".**

⚠️ **If it does not pass, do not start editing the checks.**
A failed self-test means **the checking programs themselves are broken, or something is wrong
with your setup** — ⛔ it does not mean there is something wrong with your documents.
Give the full output to your AI and say clearly: "this is the self-test, not a project check".

### 5.3 Then run the project checks

```
python3 scripts/harness/run_all_sensors.py
```

**On a new project the first run produces a batch of warnings, and that is normal** —
your ledgers are still empty, and the checks are pointing out the unfilled fields.

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

**Open `INITIALIZE_PROMPT.md` and paste the whole thing to your AI, along with your idea.**

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
      │  ① Press "snapshot"        make a checkpoint  │
      │  ② Run run_all_sensors.py  check for red      │
      │  ③ Give the AI its task                       │
      │  ④ The AI finishes and hands over a summary   │
      │  ⑤ Press "review changes"  see what it did    │
      │  ⑥ You decide → update the ledgers            │
      │  ⑦ Press "snapshot" again  = "I have read it" │
      └──────────────────────────────────────────────┘
```

**The three buttons sit at the top level of your project folder**
(`.bat` on Windows, `.command` on Mac):

| Button | When to press it |
|---|---|
| **snapshot** | Before giving out work, and after reviewing it |
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

## Step 9: upgrading when a new version comes out

**Press the "check update" button.** It tells you which version you have and which is the
latest on GitHub.

**To upgrade, three steps:**

1. Download the new ZIP from GitHub and unzip it into an `_upgrade/` folder inside your project
2. Press "check update" again — it lists which parts differ from yours
3. **Replace one part at a time**, for example:
   ```
   python3 scripts/harness/upgrade.py apply governance
   ```

🔴 **It only replaces the things it recognises**: the five folders
`governance`, `policy`, `profiles`, `prompts`, `scripts`,
and the four files `README.md`, `SETUP.md`, `INITIALIZE_PROMPT.md`, `file_index.md`.

⛔ **Everything else is left alone** — including `PROJECT.md`, `ledgers/`, `corpus/`,
`my/`, **and any folder you made yourself** (notes, figures, submitted drafts,
whatever you like).

⚠️ **This is worth stating plainly, because it is often read the other way round:**
**what protects your material is not a list of protected things — it is the list of
replaceable ones.**
🔴 **The tool recognises those nine names and refuses everything else**, so **you never have
to register the folders you create.**

⚠️ **It makes a checkpoint for you before overwriting anything**, so if you had edited a file
inside that part by hand, **"review changes" will get your edits back.**

⛔ **There is no "replace everything at once" option** — that would leave you unable to tell
which part caused a problem.

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
**The three buttons exist so that you do not.**
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
