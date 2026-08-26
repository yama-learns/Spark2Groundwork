# corpus_md/ — the plain text extracted from your PDFs

**You do not need to touch this folder.**

The PDFs in `corpus/` are converted to plain text by a script, and the text lands here.
This is what the framework reads when it checks whether a quoted sentence is
really in the source.

To run the conversion (your AI can do this for you):

```
python3 scripts/harness/tool_pdf_to_md.py
```

---

⛔ **Do not edit these files by hand.**
Once edited, they are no longer a faithful copy of the source, and any check
made against them stops meaning anything.

⚠️ Nothing in this folder is touched when you upgrade the framework.

---

(By the way: this note is deliberately a .txt and not a .md.
Every .md file in this folder is treated as text extracted from a PDF,
so a .md that is not an extraction would be reported as an untracked one.)
