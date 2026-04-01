---
name: redline
description: "Compare two .docx files and produce a redline with Word tracked changes. Trigger this skill whenever the user says 'redline' — even just the single word 'redline' with no other context. Also trigger on 'compare documents', 'track changes between files', 'compare two drafts', 'diff these documents', 'blackline', 'compare versions', 'mark up the changes', or 'show me what's different'. The skill reads two .docx files from the workspace redline folder, determines which is original and which is revised, and produces a redline .docx and .pdf in that same folder."
---

# Redline Document Comparison

Compare two .docx files and produce a professional redline with real Word tracked changes (insertions and deletions), saved as both .docx and .pdf.

## Workflow

### Step 1: Identify the Two Documents

The working folder is `claude-workspace/output/redline/` within the user's mounted workspace. Resolve the full path based on the environment — typically this will be at the workspace mount point (e.g., `/sessions/<session>/mnt/claude-workspace/output/redline/`).

List the .docx files in that folder. There should be exactly two (excluding any previous `REDLINE -` output files). If there are zero, tell the user to place two documents in the redline folder and try again. If there is one, ask for the second. If there are more than two (after filtering out previous redline outputs), ask the user to clarify which two to compare.

### Step 2: Determine Original vs. Revised

Use the following heuristics, in priority order, to decide which file is the **original** (base) and which is the **revised** (changed) version:

1. **User says explicitly** — if the user already identified which is original/revised, honor that.
2. **Filename clues** — look for signals in filenames:
   - Words like `original`, `draft`, `v1`, `initial`, `base`, `clean` → likely the original
   - Words like `revised`, `final`, `v2`, `marked`, `redline`, `updated`, `amended`, `executed`, `signed` → likely the revised
   - Version numbers: lower version = original, higher = revised
   - Dates in filenames: earlier date = original
3. **File modification time** — `stat -c %Y <file>` — older file is likely the original

**If you are not confident in the ordering, STOP and ask the user.** Do not guess. Present both filenames and ask which is the starting point (original) and which is the ending point (revised).

If you are confident, tell the user your determination and proceed:
> "I'm treating **[filename A]** as the original and **[filename B]** as the revised version. Let me know if that's backwards."

### Step 3: Unpack Both Documents

Unpack both .docx files (they are ZIP archives) to access their raw XML:

```bash
WORK="$HOME/redline_work"
mkdir -p "$WORK/original_unpacked" "$WORK/revised_unpacked" "$WORK/redline_unpacked"
unzip -o "$ORIGINAL_PATH" -d "$WORK/original_unpacked/" > /dev/null
unzip -o "$REVISED_PATH" -d "$WORK/revised_unpacked/" > /dev/null
cp -r "$WORK/original_unpacked/"* "$WORK/redline_unpacked/"
```

Also extract plain text for reference (if pandoc is available):
```bash
pandoc --track-changes=accept "$ORIGINAL_PATH" -t plain -o "$WORK/original.txt"
pandoc --track-changes=accept "$REVISED_PATH" -t plain -o "$WORK/revised.txt"
```

### Step 4: Build the Redline Document

Run the bundled comparison script. This script produces real Word tracked changes (`<w:ins>` and `<w:del>` elements) so the output opens in Word with a proper revision history.

```bash
python3 <skill-base-dir>/scripts/build_redline.py \
  "$WORK/original_unpacked/word/document.xml" \
  "$WORK/revised_unpacked/word/document.xml" \
  "$WORK/redline_unpacked/word/document.xml"
```

The script will report how many insertions and deletions it found. If it reports zero changes, the documents are likely identical — tell the user and stop.

#### How the comparison works

The script uses a three-phase approach designed to handle real-world legal document edits accurately:

**Phase 1 — Structure-aware paragraph alignment.** Paragraphs are aligned using both their text content and their structural metadata (heading style, numbering level, numbering ID). This prevents the failure where a section heading gets deleted because its body text was merged into a child paragraph. The matcher weighs structural similarity (same heading level, same numbering scheme) alongside text similarity. For example, "7. Transition Services." at Heading1/ilvl=0 will correctly align with the revised "7. Transition Services. We deeply respect..." also at Heading1/ilvl=0, rather than with a former subsection "(a) We deeply respect..." at ilvl=1 that shares more raw text.

**Phase 2 — Character-level diff with run-level formatting preservation.** For each aligned paragraph pair that differs, the script maps character positions back to the original XML runs, then performs a character-level diff using `difflib.SequenceMatcher`. Unchanged text is emitted by copying the original runs exactly — preserving bold, italic, font size, and all other per-run formatting. Only the actual insertion/deletion points get new tracked-change elements. This prevents the common failure where reformatting artifacts appear in paragraphs that only had minor text changes.

**Phase 3 — Full paragraph insertions and deletions.** Paragraphs present only in one version are handled as whole-paragraph tracked changes. Deleted paragraphs get all their text wrapped in `<w:del>` and their paragraph mark tagged with `<w:pPr><w:rPr><w:del>`. Inserted paragraphs work symmetrically with `<w:ins>`.

### Step 5: Pack the Redline .docx

Repack the modified XML back into a .docx (ZIP) file:

```python
import os, zipfile
def pack_docx(source_dir, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)
```

Save this as `$WORK/redline.docx`. This is the **primary deliverable** — it contains real Word tracked changes that render properly in Microsoft Word with accept/reject capability.

### Step 6: Build the Visual Redline for PDF

**IMPORTANT:** Do NOT convert the tracked-change .docx directly to PDF. LibreOffice misrenders Word tracked-change markup around auto-numbered paragraphs, producing artifacts like phantom numbering (e.g., showing `[8.]` in blue where no change exists, or `9.[10.]` where only `9.` should appear).

Instead, create a **visual redline** — a separate .docx where tracked-change XML elements are replaced with equivalent visual formatting:
- Deletions: red text with strikethrough
- Insertions: blue text with double-underline

This produces a PDF that exactly matches how the .docx looks in Word's "Final Showing Markup" view, without any numbering artifacts.

```bash
# Create a copy of the redline unpacked directory for the visual version
mkdir -p "$WORK/visual_unpacked"
cp -r "$WORK/redline_unpacked/"* "$WORK/visual_unpacked/"

# Convert tracked changes to visual formatting
python3 <skill-base-dir>/scripts/visual_redline.py \
  "$WORK/redline_unpacked/word/document.xml" \
  "$WORK/visual_unpacked/word/document.xml"
```

Then pack the visual version into a .docx:

```python
pack_docx("$WORK/visual_unpacked", "$WORK/visual_redline.docx")
```

### Step 7: Convert Visual Redline to PDF

Use the bundled `soffice_wrapper.py` to convert the **visual** redline (NOT the tracked-change version) to PDF:

```bash
python3 <skill-base-dir>/scripts/soffice_wrapper.py \
  --headless --norestore --convert-to pdf \
  --outdir "$OUTDIR" "$WORK/visual_redline.docx"
```

If the docx skill is also installed, its wrapper at `<docx-skill>/scripts/office/soffice.py` works identically.

If LibreOffice is unavailable or the wrapper fails, note this to the user and deliver the .docx only. The .docx is the primary deliverable.

### Step 8: Output File Naming Convention

Save the output files to the same working folder where the input documents live.

The final output files placed in the redline folder MUST follow this naming pattern:

- `REDLINE - [Revised Version File Name].docx`
- `REDLINE - [Revised Version File Name].pdf`

Where `[Revised Version File Name]` is the filename of the revised document (without its `.docx` extension). For example, if the revised file is `Acute Logistics - Letter of Intent (3-27-26).docx`, the outputs should be:
- `REDLINE - Acute Logistics - Letter of Intent (3-27-26).docx`
- `REDLINE - Acute Logistics - Letter of Intent (3-27-26).pdf`

**Important:** The PDF is generated from the visual redline, not from the tracked-change .docx. Rename the visual PDF to match the standard naming convention so the user gets a clean pair of files.

Present both files to the user with computer:// links and note:
- The .docx has real tracked changes (can accept/reject in Word)
- The PDF is a visual representation (red strikethrough = deleted, blue double-underline = inserted)
