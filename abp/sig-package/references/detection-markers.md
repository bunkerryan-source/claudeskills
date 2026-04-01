# Signature Page Detection Markers & Scoring

## Detection Layers (Priority Order)

### Layer 0 — Custom Footer (Highest Confidence)

The user may add footers to signature pages in the format:
- "Signature"
- "Signature - [Document Name]"
- "Signature Page"
- "Sig Page"
- "Execution Page"

If a page contains any of these footer patterns, it is a signature page. No further scoring needed.
When the footer includes a document name, use it to cross-reference against the checklist.

Check PDF page footers by examining text in the bottom 10% of the page area.

### Layer 1 — Keyword Detection

#### Primary Markers (Strong Signal)

Each hit = 2 points.

- "IN WITNESS WHEREOF"
- "EXECUTED as of" / "EXECUTED effective" / "EXECUTED this"
- "[SEAL]"
- "WITNESS my hand"
- "SIGNED, SEALED" / "SIGNED AND SEALED"
- "WITNESS:" or "WITNESSES:" as a standalone label (not mid-sentence)

#### Signature Block Markers (Moderate Signal)

Each hit = 1 point.

- "By:" followed by a line, underscores, or whitespace (not mid-sentence "by:" in body text —
  look for "By:" at the start of a line or after whitespace, followed by underscores or a blank)
- "Name:" or "Print Name:" followed by a line, underscores, or blank
- "Title:" followed by a line, underscores, or blank (only when near other sig block markers)
- "Its:" followed by a line, underscores, or blank
- Consecutive underscores (5+ underscores in a row), especially 3+ instances on the page
- "Authorized Signatory" / "Authorized Representative" / "Authorized Officer"
- "Signature:" or "Signature" as a field label
- "Date:" as a field label near signature block markers

#### Notary / Acknowledgment Markers

These identify notary pages, which are captured alongside their associated sig pages.

- "STATE OF" followed by "COUNTY OF" within 5 lines = notary page (2 points)
- "personally appeared" (2 points)
- "Notary Public" (1 point)
- "sworn and subscribed" / "acknowledged before me" (1 point each)
- "My commission expires" (1 point)
- "ACKNOWLEDGMENT" / "JURAT" as a heading (1 point)
- "subscribed and sworn" (1 point)
- "before me, the undersigned" (1 point)
- "duly authorized to" (0.5 points — weak signal, only counts with other notary markers)

### Layer 2 — Structural Analysis

For pages with at least 1 keyword point from Layer 1, add structural scoring:

| Condition | Points |
|-----------|--------|
| Page is in the last 20% of the document | +2 |
| Page has lower text density than document average | +1 |
| Multiple "By:" or "Name:" patterns on the page (2+) | +1 |
| Page immediately follows another sig page candidate | +1 |
| Page is in the last 3 pages of the document | +1 |

**Short document adjustment:** For documents with 5 or fewer pages, remove the "last 20%" bonus
and instead give +1 if the page is the last or second-to-last page.

### Qualification Thresholds

A page qualifies as a signature page if ANY of these conditions are met:

1. Layer 0 footer match (automatic qualify)
2. 4+ total points from primary markers (i.e., 2+ primary marker hits)
3. 2+ points from primary markers AND 2+ structural points
4. 3+ points from signature block markers alone
5. Notary page: "STATE OF" + "COUNTY OF" present, OR "Notary Public" + any other notary marker

### Split Signature Block Handling

When a signature block spans two rendered pages (lead-in language like "IN WITNESS WHEREOF" on
page N, actual signature lines on page N+1):

- Capture only page N+1 (the page with "By:" / "Name:" lines)
- Do NOT capture the lead-in page
- The lead-in page may still qualify independently if it has enough markers on its own

To detect a split: if a page scores 2+ on primary markers but has zero signature block markers,
and the next page has signature block markers but no primary markers, they are likely a split block.
Capture only the second page.

## Keyword Matching Notes

- All keyword matching should be case-insensitive
- Strip extra whitespace before matching
- For "By:" detection, require it to be at the start of a line or preceded by whitespace,
  followed by underscores, a blank line, or whitespace (to avoid false positives from body text
  like "signed by the parties")
- Underscores pattern: match `_{5,}` (5 or more consecutive underscores)
- For "Title:" — only count if at least one other signature block marker is present on the same
  page (avoids false positives from document body headings)
