---
name: sig-package
description: >
  Extract signature pages from a folder of closing documents (.docx and .pdf) and assemble them into
  bookmarked PDF signature packages — one combined package, one per signatory, and one for unsigned pages.
  Use this skill whenever the user mentions "sig pages," "signature pages," "sig package," "signature package,"
  "extract sig pages," "pull sig pages," "build sig package," "sig page package," or any reference to extracting
  or assembling signature pages from closing documents or any batch of legal documents. Even a bare "sig pages"
  with no context should trigger this skill. Also trigger when the user asks to "pull sigs," "build execution
  packages," "assemble sig pages," or says anything about creating packages for signing or execution.
---

# Signature Package Extractor

Extract signature pages from a folder of closing documents and assemble them into bookmarked PDF
signature packages for execution.

## When This Skill Runs

The user has a folder of closing documents (typically at `C:\Users\rbunker\claude-workspace\output\sig-package`)
containing .docx and/or .pdf files plus a closing checklist. The skill extracts every signature page,
identifies who signs each one, and produces ready-to-sign PDF packages.

## Important Context

- The user is a lawyer who does not write code. All scripting is handled by this skill.
- Primary use case is CRE loan closings, but the skill must work for corporate docs, M&A docs, and any
  batch of legal documents with signature pages.
- The user may add a footer to signature pages reading "Signature - [Doc Name]" or similar. When present,
  this is the highest-confidence detection signal.
- **Exhibit signature pages should be excluded.** Documents like Loan Agreements often contain exhibits
  with their own signature blocks (compliance certificates, guaranty forms, etc.). These exhibit sig pages
  are not part of the main closing execution package. The skill automatically excludes sig pages that appear
  in exhibit sections. For maximum reliability, the team should add footers to exhibit sig pages reading
  "Signature Page - Exhibit [X]" (e.g., "Signature Page - Exhibit C"). Any page with this footer pattern
  is always excluded from the sig package, regardless of what markers it contains.
- Some documents will arrive as .pdf rather than .docx. Handle both.
- Review mode is ON by default. The user will say "auto-run" or "skip review" when they're ready to
  turn it off.

## Output

All PDFs saved to the same folder as the source documents:

1. **`ProjectName-Combined-SigPackage.pdf`** — All sig pages from all docs, in closing checklist order,
   bookmarked by document name.
2. **`ProjectName-SignatoryName-SigPackage.pdf`** — One per identified signatory (by individual human,
   not by party/role). Contains that person's sig pages and their associated notary acknowledgment pages
   across all docs. If two signatories share a page, include the full page in both packages.
3. **`ProjectName-Unsigned-SigPackage.pdf`** — All sig pages where no signatory name could be identified.
   Skip this file if there are none.

## Workflow — Five Phases

Run `scripts/sig_package.py` to execute the full pipeline. The script handles all five phases.
Before running, install dependencies:

```bash
pip install python-docx pypdf thefuzz openpyxl Pillow --break-system-packages
```

Verify LibreOffice is available:
```bash
which libreoffice || echo "LibreOffice not found — install it"
```

### Phase 1: Parse the Closing Checklist

1. Scan the input folder for the closing checklist. Look for filenames containing "checklist," "closing list,"
   "doc list," or similar. If ambiguous, ask the user.
2. The checklist is typically a **Word document with a table** listing document names and signatories per
   document. It may also be an Excel file.
3. **Project name comes from filenames, not the checklist.** Documents follow the convention
   `[Project Name] - [Document Name].docx`. Extract the common prefix across all files in the folder.
   The checklist content is only used as a fallback if filenames don't share a common prefix.
4. Extract the ordered document list with signatory names per document from the checklist.
4. Fuzzy-match each checklist entry to a file (.docx or .pdf) in the folder using
   `thefuzz.fuzz.token_sort_ratio` with a threshold of 70.
5. **Report to the user and get confirmation before proceeding:**
   - Matched documents (checklist item → file)
   - Unmatched checklist items (no file found)
   - Unmatched files in folder (not on checklist)
   - Project name detected

Read `references/checklist-parsing.md` for detailed parsing logic for Word tables and Excel files.

### Phase 2: Identify Signature Pages

For each document, in checklist order, detect signature pages using a layered approach.
Read `references/detection-markers.md` for the full keyword lists, scoring rules, and threshold logic.

**Detection priority (highest to lowest confidence):**

1. **Layer 0 — Custom Footer.** If a page contains a footer matching "Signature" or "Signature - [text]",
   it is a signature page. This is the highest-confidence signal because the user places these intentionally.

2. **Layer 1 — Keyword Detection.** Scan for primary markers (e.g., "IN WITNESS WHEREOF"), signature block
   markers (e.g., "By:" followed by a line), and notary markers (e.g., "STATE OF" + "COUNTY OF"). A page
   qualifies based on marker combinations — see detection-markers.md for thresholds.

3. **Layer 2 — Structural Analysis.** For pages with at least one keyword hit, score based on position in
   document, text density, multiple signature block patterns, and adjacency to other sig page candidates.

4. **Layer 3 — Review Mode (ON by default).** Render each candidate page as an image and present a summary
   table to the user: document name, page number, detected markers, structural score, signatory names found.
   Wait for user confirmation before assembling. The user will say "auto-run" or "skip review" when they
   no longer need this step.

**When a signature block splits across two pages** (e.g., "IN WITNESS WHEREOF" on one page, signature lines
on the next), capture only the page with the actual signature lines ("By:" / "Name:" lines), not the lead-in page.

**Exhibit exclusion:** The script automatically detects where exhibits begin in a document and excludes
sig pages from exhibit sections. It also uses gap detection — if sig-like pages appear far from the main
signature block cluster (separated by 3+ body text pages), they are excluded as likely exhibit content.
For explicit control, add footers to exhibit sig pages reading "Signature Page - Exhibit [X]".

**Document preparation tip for the team:** To maximize accuracy, add these footers to closing documents:
- Main sig pages: "Signature - [Document Name]" (e.g., "Signature - Loan Agreement")
- Exhibit sig pages: "Signature Page - Exhibit [X]" (e.g., "Signature Page - Exhibit C")
Main sig page footers ensure detection. Exhibit sig page footers ensure exclusion.

If any document has zero candidates, flag it in the report — it's likely an exhibit or a detection miss.

### Phase 3: Extract Signatory Names

For each detected sig page, identify signatories:

- Check for text after "Name:" or "Print Name:" fields (if filled in, not just blanks/underscores)
- Look for proper names below signature lines — capitalized words that aren't titles
- Look for entity names in patterns like "[ENTITY NAME], a [state] [entity type]" above "By:" blocks,
  then extract the individual name from the "By:" line below
- For notary pages, match the name in "personally appeared [NAME]" back to a signatory

**Name normalization:** "John A. Smith," "John Smith," and "JOHN SMITH" should resolve to the same person.
Use the most complete version found across all documents.

**Page detection is primary** for signatory identification. Use the closing checklist's signatory-per-document
data as a cross-reference and backup when page-level detection is ambiguous.

**Pre-filled and blank signature lines:** Some documents will have names already typed into signature blocks;
others will have blanks/underscores. The detection logic must handle both within the same closing.

If no name can be identified on a sig page, tag it as "Unsigned."
If multiple signatories appear on one page, associate the page with all of them.

### Phase 4: Associate Notary Pages

Link notary acknowledgment pages to the signatory they notarize:

1. **Name match:** Check if the notary page references a signatory name ("personally appeared [NAME]").
   If yes, associate with that signatory.
2. **Proximity:** If no name match, associate with the signatory on the immediately preceding sig page
   in the same document.
3. **Fallback:** If neither works, include in the combined package only and flag for the user.

**Shared signature pages with multiple notary acknowledgments:** When a single sig page has multiple
signatories and each has a separate notary page, each per-signatory package gets the shared sig page
plus only their own notary acknowledgment page — not the other signatories' notary pages.

### Phase 5: Assemble PDFs

**For .docx source files:** Convert to PDF via LibreOffice using the bundled `soffice_wrapper.py`,
which handles sandboxed environments where AF_UNIX sockets are blocked. This produces high-fidelity
PDFs that preserve the original Word formatting. Do NOT use pandoc — it completely reflows documents
and destroys formatting.

```bash
python3 scripts/soffice_wrapper.py --headless --norestore --convert-to pdf --outdir /tmp/sig-convert "document.docx"
```

**For .pdf source files:** Extract pages directly using pypdf.

Do not modify page content — no stamps, headers, or watermarks.

**Combined package:** Merge all sig page PDFs in checklist order. Add PDF bookmarks by document name
(with sub-bookmarks if a doc has multiple sig pages, e.g., "Promissory Note — Page 1"). Save as
`ProjectName-Combined-SigPackage.pdf`.

**Per-signatory packages:** For each signatory, collect their sig pages (including shared pages and
their notary pages), merge in checklist order, bookmark by document name. Save as
`ProjectName-SignatoryName-SigPackage.pdf`. Sanitize names for filenames (remove special characters,
replace spaces with hyphens).

**Unsigned package:** If any unsigned pages exist, merge in checklist order with bookmarks. Save as
`ProjectName-Unsigned-SigPackage.pdf`.

### Report Results

Present to the user:

- **Summary table:** Per document — which sig pages extracted, signatories identified, which package(s)
  each page lands in
- **Files created** with locations
- **Flags:** Documents with no sig pages, unmatched checklist items, unassociated notary pages,
  any discrepancies between checklist signatory data and detected signatories

## Edge Cases

- **No closing checklist:** Ask the user to identify it. If none exists, process in alphabetical order
  by filename.
- **No sig pages in a document:** List in the final report but don't pause. Likely an exhibit.
- **Ambiguous signatory names:** Ask the user before merging or splitting.
- **Short documents (1–5 pages):** Lower the position threshold in structural scoring since sig pages
  won't be in the "last 20%."
- **Closing checklist in .xlsx:** Use openpyxl. Look for the first sheet with a document list.
  See `references/checklist-parsing.md`.
- **Multiple signatories per page with separate notary pages:** Each signatory's package gets the shared
  sig page plus only their own notary acknowledgment.
- **Pre-signed documents:** Detect filled-in names in signature blocks, not just blanks/underscores.
- **Mixed .docx and .pdf in the same folder:** Handle both formats transparently.

## Tech Stack

- `python-docx` — reading .docx content for keyword scanning
- `pypdf` — PDF page extraction, merging, and bookmarking
- `thefuzz` — fuzzy string matching for checklist-to-file mapping
- `openpyxl` — parsing .xlsx checklists
- `Pillow` — rendering pages as images for review mode
- LibreOffice — .docx-to-PDF conversion (must be installed on the system)
