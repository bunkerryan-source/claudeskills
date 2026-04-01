# Closing Checklist Parsing Logic

## Finding the Checklist File

Scan the input folder for files with names matching any of these patterns (case-insensitive):
- "checklist"
- "closing list"
- "doc list"
- "document list"
- "closing schedule"
- "closing index"

Supported formats: `.docx`, `.xlsx`, `.xls`

If multiple matches are found, prefer the one with "checklist" in the name. If still ambiguous,
ask the user to identify which file is the closing checklist.

If no match is found, ask the user. If the user confirms no checklist exists, process documents
in alphabetical order by filename and skip signatory-per-document cross-referencing.

## Extracting the Project Name

The project name will be clearly labeled at the top of the checklist. Look for it in:

1. **Word document:** The first heading, title line, or bolded text at the top. Common patterns:
   - "Closing Checklist — [Project Name]"
   - "[Project Name] Closing Checklist"
   - "[Project Name]" as a standalone title line
   - A header or first row of a table labeled "Project:" or "Loan:" or "Transaction:"

2. **Excel file:** Check cell A1 or a merged cell at the top. May also appear as a header row
   above the document table.

3. **Filename fallback:** If the project name isn't found in the document content, extract it from
   the checklist filename by removing common suffixes like "closing-checklist," "doc-list," etc.

If the project name can't be determined, ask the user.

## Parsing Word Document Tables

The most common format is a Word table with columns for document name and signatories.

### Strategy

1. Iterate through all tables in the document using `python-docx`.
2. Identify the document list table — it's typically the largest table, or the one with column
   headers matching patterns like "Document," "Doc Name," "Description," "Instrument," etc.
3. Identify columns:
   - **Document name column:** Look for headers containing "document," "description," "instrument,"
     "name," "item," or "title"
   - **Signatory column(s):** Look for headers containing "signatory," "signer," "signature,"
     "execution," "signed by," "parties," or specific party names like "borrower," "lender,"
     "guarantor"
   - **Number/order column:** Look for headers containing "#," "no.," "number," "order," "item"
4. Extract each row as a document entry with:
   - Document name (cleaned of leading numbers, bullets, periods)
   - Signatory name(s) (may be comma-separated, or in separate columns per party)
   - Order (row position in the table, or explicit number if present)

### Signatory Name Extraction from Checklist

Signatory columns may contain:
- Individual names: "John Smith"
- Entity names: "ABC Borrower LLC"
- Role labels: "Borrower," "Lender," "Guarantor" — these are roles, not names. Note them but
  don't use them as signatory names for package filenames. Cross-reference with names found on
  actual signature pages.
- Checkmarks, "X," or "Yes/No" — these indicate who signs but don't give a name. Skip for
  signatory identification.
- Multiple names separated by commas, semicolons, or line breaks within the cell.

### Handling Merged Cells and Multi-Row Entries

Some checklists group related documents under a single heading with merged cells. For example:

| # | Document | Borrower | Lender |
|---|----------|----------|--------|
| 1 | Loan Agreement | X | X |
| 2 | Promissory Note | X | |
|   | *Exhibits* | | |
| 2a | Exhibit A - Compliance Certificate | | |

- Skip rows that appear to be sub-headers or exhibit labels (italicized, indented, or containing
  "exhibit," "schedule," "attachment," "annex" as the primary text)
- Treat these as documents that likely won't have signature pages

## Parsing Excel Files

Use `openpyxl` to read .xlsx files.

### Strategy

1. Load the workbook and check the first sheet. If it doesn't contain a document list, check
   other sheets.
2. Find the header row — look for a row where multiple cells match document-list column patterns
   ("Document," "Signatory," "#," etc.).
3. Extract the project name from cells above the header row (often a merged cell or a title in
   row 1).
4. Parse each data row below the header the same way as Word tables.
5. Stop parsing when you hit an empty row or a row with only formatting (borders, shading) and
   no text content.

### Common Excel Patterns

- Header row is often row 1 or row 2 (row 1 may be the project name)
- Document names may be in column A or B
- Signatory columns may use "X" marks, checkmarks, or full names
- Some checklists use Excel filters — read all rows regardless of filter state
- Watch for hidden rows or columns — include them

## Fuzzy Matching: Checklist Items to Files

Use `thefuzz.fuzz.token_sort_ratio` with a threshold of 70 to match checklist document names to
actual filenames in the folder.

### Pre-processing before matching

1. Strip file extensions from filenames
2. Remove common prefixes: numbers, bullets, dashes (e.g., "01 - ", "1. ", "A. ")
3. Remove common suffixes: "- Draft", "- Final", "- Execution Copy", "(v2)", date stamps
4. Normalize whitespace and case

### Match resolution

- If a checklist item matches multiple files above threshold, take the highest score
- If two checklist items match the same file, flag for user review
- Files that don't match any checklist item: include in the report as "unmatched files"
- Checklist items that don't match any file: include in the report as "unmatched checklist items"

### Common filename patterns in closing folders

- "01 - Loan Agreement.docx"
- "Loan Agreement - FINAL.docx"
- "Loan_Agreement_v3.docx"
- "02_Promissory_Note.docx"
- "Guaranty (Smith).docx"
- "Environmental Indemnity Agreement.pdf"

The matching logic should handle all of these by stripping prefixes, suffixes, and normalizing
separators before comparing to checklist entries.
