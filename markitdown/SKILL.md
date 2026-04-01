---
name: markitdown
description: >
  Convert files to clean Markdown using Microsoft's markitdown CLI. Use this skill whenever the user says "markitdown", "convert to markdown", "make this markdown", or wants to convert files (docx, pdf, pptx, xlsx, html, etc.) in their output/markdown folder to .md format. Also trigger when the user drops a file into output/markdown and wants it converted, or says anything like "convert what's in the markdown folder". Even a bare "markitdown" with no other context should trigger this skill.
---

# Markitdown — File-to-Markdown Converter

This skill converts files in `claude-workspace/output/markdown/` to `.md` format using the `markitdown` CLI (Microsoft's open-source converter, already installed). It preserves formatting, tables, and structure as faithfully as possible.

## How It Works

The `markitdown` CLI handles: `.docx`, `.pdf`, `.pptx`, `.xlsx`, `.xls`, `.csv`, `.html`, `.htm`, `.txt`, `.rtf`, `.xml`, `.json`, `.jpg`, `.png`, `.wav`, `.mp3`, and more. It outputs clean Markdown with tables, headings, and lists intact.

## Prerequisites

Before converting, make sure the full converter suite is available. Run this once per session if needed:
```bash
pip install "markitdown[all]" --break-system-packages 2>/dev/null
```
This is safe to re-run — it's a no-op if already installed. It adds support for docx, xlsx, pptx, pdf, audio, and other formats beyond the base install.

## Steps

1. **Check the folder exists.** Look for files in the workspace's `output/markdown/` directory. The full path is:
   ```
   /sessions/*/mnt/claude-workspace/output/markdown/
   ```
   If the folder doesn't exist, create it and tell the user to drop files there, then run the command again.

2. **Find files to convert.** List all files in the folder. Identify any file that is NOT a `.md` file. For each non-`.md` file, check whether a corresponding `.md` file already exists (same base name, `.md` extension). Skip files that already have a matching `.md`.

3. **Convert each file.** For every file that needs conversion, run:
   ```bash
   markitdown "<input-file>" -o "<same-folder>/<same-basename>.md"
   ```
   For example, if the file is `report.docx`, the output is `report.md` in the same folder.

4. **Report results.** Tell the user:
   - Which files were converted (and their new `.md` filenames)
   - Which files were skipped (already had a `.md` counterpart)
   - If any conversions failed, show the error

5. **Handle edge cases:**
   - If the folder is empty, say so
   - If all files already have `.md` counterparts, say "Everything is already converted"
   - If a file type isn't supported by markitdown, note which file was skipped and why

## Example

User drops `proposal.docx` and `financials.xlsx` into `output/markdown/`.

After running:
```
output/markdown/
├── proposal.docx
├── proposal.md        ← new
├── financials.xlsx
├── financials.md      ← new
```

## Important Notes

- The original files are never deleted or modified — only new `.md` files are created alongside them.
- Ryan does not code, so don't show raw terminal output unless something goes wrong. Just confirm what was converted.
- If the conversion output looks garbled or empty, mention it so Ryan can decide whether to try a different approach for that file type.
