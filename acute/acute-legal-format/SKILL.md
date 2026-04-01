---
name: acute-legal-format
description: "Format legal transaction documents for the Acute Logistics acquisition to match the ABP Capital legal agreement template. Use this skill whenever Ryan asks to draft, format, or revise a formal Acute transaction document — Asset Purchase Agreement, Bill of Sale, Assignment and Assumption Agreement, Non-Competition Agreement, Transition Services Agreement, Clawback Note, Escrow Agreement, Employment Agreement, or any other legal agreement for the Acute deal. Also trigger when Ryan says 'format this like the template', 'use the legal format', 'match the template formatting', or references formatting consistency with previously drafted Acute documents. Even if Ryan just says 'draft a [document name] for Acute' without mentioning formatting, use this skill — all formal Acute legal documents should use this formatting unless Ryan explicitly says formatting is not important."
---

# Acute Legal Agreement Formatting

This skill ensures every formal legal document drafted for the Acute Logistics acquisition matches the ABP Capital legal agreement template exactly. The template lives at:

```
mnt/acute/reference/TEMPLATE - Legal Agreement.docx
```

## Why This Matters

Word's .docx format is a ZIP of XML files. If you generate a document with a library like docx-js, it creates its own styles from scratch — and those styles won't match the template. The only reliable way to get pixel-perfect formatting is to **clone the template** (preserving all its styles, numbering definitions, and fonts) and **replace only the body content** with new XML that references the template's existing styles.

Ryan has iterated extensively on this workflow. The formatting rules below are the result of that iteration. Follow them precisely.

---

## Workflow Overview

### Step 1: Unpack the template

```bash
python mnt/.claude/skills/docx/scripts/office/unpack.py \
  "mnt/acute/reference/TEMPLATE - Legal Agreement.docx" \
  <working_dir>/template_unpacked
```

This gives you the template's full XML structure — styles.xml, numbering.xml, document.xml, etc.

### Step 2: Create your working copy

```bash
cp -r <working_dir>/template_unpacked <working_dir>/doc_work
```

You'll be replacing `doc_work/word/document.xml` with your generated content while keeping everything else from the template intact.

### Step 3: Generate document.xml body content

Write a Python script that builds the XML body content using the template's style IDs and numbering references. See the **Style Reference** and **XML Patterns** sections below.

Replace the `<w:body>` content in `doc_work/word/document.xml` with your generated paragraphs, preserving the final `<w:sectPr>` element from the template.

### Step 4: Run the spacing fixer

```bash
python mnt/acute/skills/acute-legal-format/scripts/fix_spacing.py \
  <working_dir>/doc_work \
  <output_path>.docx \
  --template "mnt/acute/reference/TEMPLATE - Legal Agreement.docx"
```

This script inserts the empty spacer paragraphs and line-spacing attributes that match the template's visual rhythm. See `scripts/fix_spacing.py` for details.

### Step 5: Validate

```bash
python mnt/.claude/skills/docx/scripts/office/validate.py <output_path>.docx
```

---

## Style Reference

The template defines a multi-level numbering chain (abstractNum 8, numId 37) with four levels. Every paragraph must use one of the styles below — never invent new styles.

### Document Structure Styles

| Style ID | Purpose | Numbering | Format |
|---|---|---|---|
| `ARTICLE` | Article number line ("ARTICLE 1") | numId 37, ilvl 0 | Centered, bold, Arial 10pt |
| `ARTICLE` (with numId=0) | Article title ("DEFINITIONS") | Numbering suppressed | Centered, bold, Arial 10pt |
| `SECTIONHEADING` | Section heading ("1.01 Defined Terms") | numId 37, ilvl 1 | Left-aligned, underlined, bold, Arial 10pt |
| `SECTIONTEXT` | Body paragraph text | No numbering | Justified, firstLine indent 720 twips, after=240, Arial 10pt |
| `Section101Heading` | Subsection heading (rarely used) | numId 37, ilvl 1 | Similar to SECTIONHEADING |
| `Section101Text` | Subsection body text | No numbering | Similar to SECTIONTEXT |
| `aText` | Lettered list item "(a)" | numId 37, ilvl 2 | Justified, hanging indent, Arial 10pt |
| `iText` | Roman numeral list item "(i)" | numId 37, ilvl 3 | Justified, hanging indent, Arial 10pt |
| `BodyText` | Plain body text (used for spacers) | No numbering | Justified, Arial 10pt |

### Key Numbering Behavior

- **ARTICLE** paragraphs auto-number: "ARTICLE 1", "ARTICLE 2", etc. (decimal format)
- **SECTIONHEADING** paragraphs auto-number within their article: "1.01", "1.02", "2.01", etc. (decimalZero format)
- **aText** paragraphs auto-number: "(a)", "(b)", "(c)", etc. (lowerLetter)
- **iText** paragraphs auto-number: "(i)", "(ii)", "(iii)", etc. (lowerRoman)
- Numbering resets appropriately at each new level

### ARTICLE Pattern (Two Paragraphs)

Each article heading is actually **two** consecutive paragraphs:

1. **Numbered paragraph** — uses `ARTICLE` style with auto-numbering (generates "ARTICLE 1")
2. **Title paragraph** — uses `ARTICLE` style with numbering suppressed (`numId=0`), contains the title text ("DEFINITIONS")

```xml
<!-- Paragraph 1: auto-numbered -->
<w:p>
  <w:pPr><w:pStyle w:val="ARTICLE"/></w:pPr>
</w:p>

<!-- Paragraph 2: title, numbering suppressed -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="ARTICLE"/>
    <w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>
  </w:pPr>
  <w:r><w:t>DEFINITIONS</w:t></w:r>
</w:p>
```

---

## XML Patterns

### Basic paragraph with text

```xml
<w:p>
  <w:pPr><w:pStyle w:val="SECTIONTEXT"/></w:pPr>
  <w:r><w:rPr/><w:t xml:space="preserve">Paragraph text here.</w:t></w:r>
</w:p>
```

### Bold inline text (e.g., defined terms)

```xml
<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Defined Term</w:t></w:r>
```

### Underlined inline text

```xml
<w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>underlined text</w:t></w:r>
```

### Smart quotes and special characters

Use XML character references — never raw smart quotes:
- Left double quote: `&#x201C;`
- Right double quote: `&#x201D;`
- Apostrophe/right single quote: `&#x2019;`
- Em-dash: `&#x2014;`

### Preamble / Lead-in Pattern

Preamble paragraphs that introduce parties or recitals should list items **inline** within a single `SECTIONTEXT` paragraph — never as a lettered `(a)/(b)/(c)` list. Lists create unwanted spacing in lead-in text.

**Correct:**
```xml
<w:p>
  <w:pPr><w:pStyle w:val="SECTIONTEXT"/></w:pPr>
  <w:r><w:rPr/><w:t xml:space="preserve">This AGREEMENT is entered into by and among </w:t></w:r>
  <w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Party One LLC</w:t></w:r>
  <w:r><w:rPr/><w:t xml:space="preserve">, a Delaware LLC (&#x201C;Buyer&#x201D;); </w:t></w:r>
  <w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Party Two Inc.</w:t></w:r>
  <w:r><w:rPr/><w:t xml:space="preserve">, a Tennessee corporation (&#x201C;Seller&#x201D;).</w:t></w:r>
</w:p>
```

**Incorrect:** Using `aText` paragraphs for party listings.

### Signature Block Pattern

Signature blocks use `SECTIONTEXT` style. Use tab characters (`<w:tab/>`) for alignment. Signature lines use underscores.

---

## Spacing Rules (Handled by fix_spacing.py)

The `fix_spacing.py` script handles these automatically — you do NOT need to insert spacer paragraphs manually in your generated XML. Just generate the content paragraphs and let the script handle spacing:

1. **Before each ARTICLE heading** — inserts an empty `BodyText` spacer paragraph
2. **After each ARTICLE title** — inserts an empty `Section101Heading` paragraph (numbering suppressed)
3. **After each SECTIONHEADING** — inserts an empty `Section101Heading` paragraph (numbering suppressed, left indent 720)
4. **On every `aText` and `iText` paragraph** — adds `w:spacing w:after="240" w:line="242" w:lineRule="auto"` to the paragraph properties

These rules reproduce the visual spacing from the template. Without them, sections run together and list items crowd each other.

---

## Exhibits and Schedules Index

Only include an Exhibits and Schedules page if the body of the agreement actually references exhibits or disclosure schedules. If it does, place the index page after the signature block. Format it as a centered bold heading ("EXHIBITS AND SCHEDULES") followed by a list of each referenced exhibit/schedule with its title, using em-dashes (`&#x2014;`) as separators. If the agreement has no exhibits or schedules, omit this page entirely.

---

## File Naming Convention

Ryan's preference: `Acute - [Document Name] - MMDDYYYY [version].docx`

Examples:
- `Acute - Asset Purchase Agreement - 03312026 v3.docx`
- `Acute - Bill of Sale - 04012026.docx`

---

## Common Pitfalls

1. **Don't use docx-js or python-docx to create from scratch** — these libraries generate their own styles that won't match the template. Always clone the template.
2. **Don't use raw smart quotes in XML** — they'll cause encoding issues. Use `&#x201C;` etc.
3. **Don't manually insert spacer paragraphs** — let fix_spacing.py handle all spacing.
4. **Don't use `&amp;#x2014;`** — that's double-escaped. Use `&#x2014;` directly.
5. **Don't forget the ARTICLE two-paragraph pattern** — the numbered paragraph and the title paragraph are separate.
6. **Don't use list formatting in preambles** — parties and recitals go inline in a single SECTIONTEXT paragraph.
7. **Preserve the template's sectPr** — the final `<w:sectPr>` in the body defines page size, margins, headers/footers. Always keep it.
