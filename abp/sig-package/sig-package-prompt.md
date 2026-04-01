# Build a Cowork Skill: Signature Page Extractor

## What I Want

Build me a Cowork skill called `sig-page-extractor` that extracts signature pages from a folder of .docx and assembles them into bookmarked PDF signature packages.

I'm a lawyer. When I close a real estate loan, I have a folder with 10-40 .docx closing documents plus a closing checklist. I need to pull the signature pages from each doc and create PDF packages for execution. Right now I do this manually — I want to automate it. While the primary initial use is real estate loan closing documents, I need the skill to be flexible enough to apply in other scenarios where I need to extra a signature page package from a set of documents. 

## Trigger

This skill should trigger on: "sig pages," "signature pages," "sig package," "signature package," "extract sig pages," "pull sig pages," "build sig package," "sig page package," or any reference to extracting or assembling signature pages from closing documents. Even a bare "sig pages" with no context should trigger it.

## Input

A folder located at C:\Users\rbunker\claude-workspace\output\sig-package containing:
- Multiple `.docx` closing documents
- A closing checklist (`.docx` or `.xlsx`) that lists the documents in their correct order

## Output

All PDFs saved to the same folder as the source documents:

1. **`ProjectName-Combined-SigPackage.pdf`** — All sig pages from all docs, in closing checklist order, bookmarked by document name. No stamps, headers, or modifications to the pages themselves.

2. **`ProjectName-SignatoryName-SigPackage.pdf`** — One per identified signatory. Contains only that person's sig pages and their associated notary acknowledgment pages, across all docs, in checklist order, bookmarked by doc name. If two signatories share a page (e.g., Borrower and Lender both sign the same page), include the full page in both packages.

3. **`ProjectName-Unsigned-SigPackage.pdf`** — All sig pages where no signatory name could be identified, grouped together. Skip this file if there are no unsigned pages.

Filename format for per-signatory packages: `ProjectName-SignatoryName-SigPackage.pdf`
Project name comes from the closing checklist title, header, or filename.

## Workflow — Five Phases

### Phase 1: Parse the Closing Checklist

- Identify the closing checklist file (look for filenames containing "checklist," "closing list," "doc list," or similar — if ambiguous, ask me).
- Extract the project name and the ordered document list.
- Fuzzy-match each checklist entry to a .docx file in the folder. Use `thefuzz.fuzz.token_sort_ratio` with a threshold of 70.
- Report: matched docs, unmatched checklist items, unmatched files. Ask me to confirm before proceeding.

### Phase 2: Identify Signature Pages

For each .docx, in checklist order, scan for sig pages using layered detection:

**Layer 1 — Keyword Detection.** A page is a candidate if it contains two or more of these markers:

Primary markers (strong signal):
- "IN WITNESS WHEREOF"
- "EXECUTED as of" / "EXECUTED effective"
- "[SEAL]"
- "WITNESS my hand"
- "SIGNED, SEALED"

Signature block markers (moderate signal):
- "By:" followed by a line or underscores
- "Name:" / "Print Name:" followed by a line or underscores
- "Title:" followed by a line or underscores
- Consecutive underscores (5+ in a row), especially multiple instances
- "Authorized Signatory" / "Authorized Representative"

Notary/acknowledgment markers (capture these pages too):
- "STATE OF" followed by "COUNTY OF" within a few lines
- "personally appeared"
- "Notary Public"
- "sworn and subscribed" / "acknowledged before me"
- "My commission expires"
- "ACKNOWLEDGMENT" / "JURAT"

**Layer 2 — Structural Analysis.** For pages with at least one keyword hit, score:
- Page in last 20% of document: +2
- Lower text density than document average: +1
- Multiple "By:" or "Name:" patterns: +1
- Immediately follows another sig page candidate: +1

A page qualifies if:
- 2+ primary markers, OR
- 1 primary marker + 2 structural points, OR
- 3+ signature block markers, OR
- Notary markers present (STATE OF + COUNTY OF, or "Notary Public" + any other notary marker)

**Layer 3 — Visual Verification (Review Mode).** For the first few deals, render each candidate page as an image and show me a summary table (doc name, page #, detected markers, structural score, signatory names) before assembling. I'll tell you when to turn this off and auto-run.

If any document has zero candidates, flag it — could be an exhibit or a detection miss.

### Phase 3: Extract Signatory Names

For each sig page, identify signatories:
- Look for text after "Name:" or "Print Name:" fields (if filled in, not just blanks/underscores)
- Look for proper names below signature lines (underscores) — capitalized words that aren't titles like "Manager"
- Look for entity names in patterns like "[ENTITY NAME], a [state] [entity type]" above "By:" blocks
- For notary pages, match the name in "personally appeared [NAME]" back to a signatory from a preceding sig page in the same document

Normalize names across documents — "John A. Smith," "John Smith," and "JOHN SMITH" should resolve to the same person. Use the most complete version found.

If no name can be identified, tag as "Unsigned."
If multiple signatories on one page, associate the page with all of them.

### Phase 4: Associate Notary Pages

Link notary pages to the signatory they notarize:
1. Name match: Check if the notary page references a signatory name. If yes, associate.
2. Proximity: If no name match, associate with the signatory on the immediately preceding sig page in the same document.
3. If neither works, include in combined package only and flag for me.

### Phase 5: Assemble PDFs

Convert each identified sig page to PDF (extract the page from the .docx into a temp single-page .docx, then convert via LibreOffice). Do not modify page content.

**Combined package:** Merge all sig page PDFs in checklist order. Add PDF bookmarks by document name (with sub-bookmarks if a doc has multiple sig pages, e.g., "Promissory Note — Page 1"). Save as `LoanName-Combined-SigPackage.pdf`.

**Per-signatory packages:** For each signatory, collect their sig pages (including shared pages and their notary pages), merge in checklist order, bookmark by doc name. Save as `LoanName-SignatoryName-SigPackage.pdf`. Sanitize names for filenames.

**Unsigned package:** If any unsigned pages exist, merge in checklist order with bookmarks. Save as `LoanName-Unsigned-SigPackage.pdf`.

### Report Results

Show me:
- Summary table: per document, which sig pages extracted, signatories identified, which package(s) each page lands in
- Files created with locations
- Flags: docs with no sig pages, unmatched checklist items, unassociated notary pages

## Edge Cases

- No closing checklist: Ask me to identify it. If none exists, process in alphabetical order.
- No sig pages in a doc: Flag but continue — probably an exhibit.
- Ambiguous signatory names: Ask me before merging/splitting.
- Short documents (1-5 pages): Lower the position threshold since sig pages won't be in the "last 20%."
- Closing checklist in .xlsx: Use openpyxl, look for first sheet with numbered doc list.
- Some documents have multiple signatories and each signature is required to be notarized. The document may contain signature blocks for each signatory on a single page and then a separate notary page for each signatory (for example, a signature page with 3 signatories followed by three blank notary acknowledgment pages). The output should be one signature page for each signatory plus one notary acknowledgment page. 

## Tech Stack

- `python-docx` for reading .docx
- `pypdf` for PDF merging and bookmarking
- `thefuzz` for fuzzy string matching
- `openpyxl` for .xlsx checklists
- LibreOffice for .docx-to-PDF conversion

## How to Build This

Use the skill-creator skill. Read `/mnt/skills/examples/skill-creator/SKILL.md` first. Build the skill as a proper Cowork skill with:
- `SKILL.md` with YAML frontmatter and full instructions
- `scripts/` directory with the Python processing script(s)
- Pushy trigger description so it fires reliably

I don't write code — I need Claude to handle all the scripting. The SKILL.md should contain enough detail that Claude can execute the full workflow when triggered.

After building, give me a test case to run with a sample set of docs so we can iterate.
